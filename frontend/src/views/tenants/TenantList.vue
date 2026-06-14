<template>
    <div>
        <div class="flex items-center justify-between mb-6">
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Tenants</h1>
            <button
                v-if="!singleTenantMode"
                @click="showCreateModal = true"
                class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md"
            >
                + New Tenant
            </button>
        </div>

        <NotificationBanner v-if="error" type="error" :message="typeof error === 'string' ? error : 'Error'" @close="clearError" />

        <!-- Filtros -->
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-4 mb-4 flex flex-wrap gap-4">
            <input
                v-model="search"
                type="text"
                placeholder="Filter by name..."
                class="rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
            <select
                v-model="statusFilter"
                class="rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            >
                <option value="">All statuses</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
            </select>
            <button
                @click="resetFilters"
                class="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            >
                Clear
            </button>
        </div>

        <!-- Tabla -->
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
            <div v-if="loading" class="text-center py-12">
                <p class="text-gray-500 dark:text-gray-400">Loading tenants...</p>
            </div>

            <template v-else>
                <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead class="bg-gray-50 dark:bg-gray-900">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Slug</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Members</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Created</th>
                            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                        <tr v-if="tenants.length === 0">
                            <td colspan="6" class="px-6 py-10 text-center text-sm text-gray-500 dark:text-gray-400">
                                No tenants found.
                            </td>
                        </tr>
                        <tr
                            v-for="t in tenants"
                            :key="t.id"
                            class="hover:bg-gray-50 dark:hover:bg-gray-700"
                        >
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ t.name }}</span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="text-sm font-mono text-gray-500 dark:text-gray-400">{{ t.slug }}</span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                {{ t.member_count }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span
                                    class="px-2 py-1 text-xs font-medium rounded-full"
                                    :class="t.is_active
                                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'"
                                >
                                    {{ t.is_active ? 'Active' : 'Inactive' }}
                                </span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                {{ formatDate(t.created_at) }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-right text-sm space-x-3">
                                <router-link
                                    :to="`/tenants/${t.id}`"
                                    class="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-200"
                                >
                                    View
                                </router-link>
                                <router-link
                                    v-if="t.is_owner || isSuperuser"
                                    :to="`/tenants/${t.id}/settings`"
                                    class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
                                >
                                    Edit
                                </router-link>
                                <button
                                    v-if="(t.is_owner || isSuperuser) && t.is_active"
                                    @click="confirmDeactivate(t)"
                                    class="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-200"
                                >
                                    Deactivate
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <!-- Paginación server-side -->
                <div class="px-6 py-4 flex items-center justify-between border-t border-gray-200 dark:border-gray-700">
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        <span v-if="tenantCount > 0">
                            {{ pageStart }}–{{ pageEnd }} de {{ tenantCount }} tenants
                        </span>
                    </p>
                    <div class="flex space-x-2">
                        <button
                            @click="goToPrevious"
                            :disabled="!tenantPrevious"
                            class="px-3 py-1 text-sm rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-gray-300 disabled:cursor-not-allowed"
                        >
                            Previous
                        </button>
                        <span class="px-3 py-1 text-sm text-gray-600 dark:text-gray-400">
                            Página {{ currentPage }}
                        </span>
                        <button
                            @click="goToNext"
                            :disabled="!tenantNext"
                            class="px-3 py-1 text-sm rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-gray-300 disabled:cursor-not-allowed"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </template>
        </div>

        <!-- Modal crear tenant -->
        <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
                <h2 class="text-lg font-medium text-gray-900 dark:text-white mb-4">New Tenant</h2>
                <NotificationBanner v-if="createError" type="error" :message="createError" @close="createError = null" />
                <form @submit.prevent="handleCreate">
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                        <input
                            v-model="createForm.name"
                            type="text"
                            required
                            minlength="2"
                            autofocus
                            class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                    </div>
                    <div class="flex justify-end space-x-3">
                        <button
                            type="button"
                            @click="showCreateModal = false"
                            class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            :disabled="creating"
                            class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md disabled:opacity-50"
                        >
                            {{ creating ? 'Creating...' : 'Create' }}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import { useTenant } from "@/composables/useTenant";
import { useAuth } from "@/composables/useAuth";
import { useConfigStore } from "@/stores/config";
import NotificationBanner from "@/components/NotificationBanner.vue";

const { tenants, tenantCount, tenantNext, tenantPrevious, loading, error, fetchTenants, createTenant, deleteTenant, clearError } = useTenant();
const { user } = useAuth();
const configStore = useConfigStore();
const singleTenantMode = computed(() => configStore.singleTenantMode);

const isSuperuser = computed(() => user.value?.is_superuser === true);

// Estado de paginación y filtros
const currentPage = ref(1);
const pageSize = 20;
const search = ref("");
const statusFilter = ref("");

let searchTimeout = null;

const pageStart = computed(() => (currentPage.value - 1) * pageSize + 1);
const pageEnd = computed(() => Math.min(currentPage.value * pageSize, tenantCount.value));

// Modal crear
const showCreateModal = ref(false);
const creating = ref(false);
const createError = ref(null);
const createForm = reactive({ name: "" });

function buildParams() {
    const params = { page: currentPage.value };
    if (search.value) params.search = search.value;
    if (statusFilter.value !== "") params.is_active = statusFilter.value;
    return params;
}

async function load() {
    await fetchTenants(buildParams());
}

// Búsqueda con debounce — espera 400ms antes de hacer el request
watch(search, () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage.value = 1;
        load();
    }, 400);
});

// Filtro de estado — request inmediato
watch(statusFilter, () => {
    currentPage.value = 1;
    load();
});

function goToNext() {
    if (!tenantNext.value) return;
    currentPage.value++;
    load();
}

function goToPrevious() {
    if (!tenantPrevious.value) return;
    currentPage.value--;
    load();
}

function resetFilters() {
    search.value = "";
    statusFilter.value = "";
    currentPage.value = 1;
    load();
}

function formatDate(dateStr) {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString();
}

async function handleCreate() {
    creating.value = true;
    createError.value = null;
    const result = await createTenant({ name: createForm.name });
    if (result) {
        showCreateModal.value = false;
        createForm.name = "";
        currentPage.value = 1;
        load();
    } else {
        createError.value = typeof error.value === "string" ? error.value : "Failed to create tenant";
    }
    creating.value = false;
}

async function confirmDeactivate(t) {
    if (window.confirm(`Deactivate "${t.name}"? This cannot be undone.`)) {
        await deleteTenant(t.id);
        load();
    }
}

onMounted(load);
</script>
