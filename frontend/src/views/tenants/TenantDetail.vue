<template>
    <div>
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ tenant?.name || 'Tenant' }}</h1>
                <div class="flex items-center space-x-4 mt-1 text-sm text-gray-500 dark:text-gray-400">
                    <span>Slug: <code class="font-mono">{{ tenant?.slug }}</code></span>
                    <span>Created: {{ formatDate(tenant?.created_at) }}</span>
                    <span
                        class="px-2 py-0.5 rounded-full text-xs font-medium"
                        :class="tenant?.is_active
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'"
                    >
                        {{ tenant?.is_active ? 'Active' : 'Inactive' }}
                    </span>
                </div>
            </div>
            <router-link
                v-if="canManage"
                :to="`/tenants/${tenantId}/settings`"
                class="px-4 py-2 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
                Settings
            </router-link>
        </div>

        <NotificationBanner v-if="error" type="error" :message="error" @close="error = null" />

        <div v-if="loading" class="text-center py-10">
            <p class="text-gray-500 dark:text-gray-400">Loading...</p>
        </div>

        <template v-else-if="tenant">

            <!-- Members -->
            <div class="bg-white dark:bg-gray-800 shadow rounded-lg mb-6">
                <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                    <div>
                        <h2 class="text-lg font-medium text-gray-900 dark:text-white">Members</h2>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{{ members.length }} member{{ members.length !== 1 ? 's' : '' }}</p>
                    </div>
                    <button
                        v-if="canManage"
                        @click="showAddMember = true"
                        class="px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md"
                    >
                        + Add Member
                    </button>
                </div>

                <!-- Add member form -->
                <div v-if="showAddMember" class="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <form @submit.prevent="handleAddMember" class="flex items-end gap-3">
                        <div class="flex-1">
                            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                            <input
                                v-model="addForm.email"
                                type="email"
                                required
                                placeholder="user@example.com"
                                class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Role</label>
                            <select
                                v-model="addForm.role"
                                class="rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            >
                                <option value="MEMBER">Member</option>
                                <option value="ADMIN">Admin</option>
                            </select>
                        </div>
                        <button
                            type="submit"
                            :disabled="adding"
                            class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md disabled:opacity-50"
                        >
                            {{ adding ? 'Adding...' : 'Add' }}
                        </button>
                        <button
                            type="button"
                            @click="cancelAdd"
                            class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
                        >
                            Cancel
                        </button>
                    </form>
                </div>

                <!-- Members table -->
                <div v-if="membersLoading" class="text-center py-8">
                    <p class="text-sm text-gray-500 dark:text-gray-400">Loading members...</p>
                </div>
                <table v-else class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead class="bg-gray-50 dark:bg-gray-900">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">User</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Role</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Since</th>
                            <th v-if="canManage" class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                        <tr v-if="paginatedMembers.length === 0">
                            <td colspan="4" class="px-6 py-8 text-center text-sm text-gray-500 dark:text-gray-400">No members found.</td>
                        </tr>
                        <tr v-for="m in paginatedMembers" :key="m.id" class="hover:bg-gray-50 dark:hover:bg-gray-700">
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="flex items-center space-x-3">
                                    <div class="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center flex-shrink-0">
                                        <span class="text-xs font-medium text-indigo-700 dark:text-indigo-300">
                                            {{ m.user?.email?.charAt(0).toUpperCase() }}
                                        </span>
                                    </div>
                                    <span class="text-sm text-gray-900 dark:text-white">{{ m.user?.email }}</span>
                                </div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span
                                    class="px-2 py-1 text-xs font-medium rounded-full"
                                    :class="m.role === 'OWNER'
                                        ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300'
                                        : m.role === 'ADMIN'
                                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
                                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'"
                                >
                                    {{ m.role }}
                                </span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                {{ formatDate(m.created_at) }}
                            </td>
                            <td v-if="canManage" class="px-6 py-4 whitespace-nowrap text-right text-sm space-x-3">
                                <template v-if="m.role !== 'OWNER'">
                                    <button
                                        @click="handleRoleChange(m.user.id, m.role === 'ADMIN' ? 'MEMBER' : 'ADMIN')"
                                        class="text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400"
                                    >
                                        → {{ m.role === 'ADMIN' ? 'Member' : 'Admin' }}
                                    </button>
                                    <button
                                        @click="handleRemove(m.user.id)"
                                        class="text-red-500 dark:text-red-400 hover:text-red-700"
                                    >
                                        Remove
                                    </button>
                                </template>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <!-- Paginación members (client-side — bounded by max_users) -->
                <div v-if="memberPages > 1" class="px-6 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        {{ memberPageStart }}–{{ memberPageEnd }} de {{ members.length }}
                    </p>
                    <div class="flex space-x-2">
                        <button
                            @click="memberPage--"
                            :disabled="memberPage === 1"
                            class="px-3 py-1 text-sm rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-40 dark:text-gray-300"
                        >Previous</button>
                        <button
                            @click="memberPage++"
                            :disabled="memberPage === memberPages"
                            class="px-3 py-1 text-sm rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-40 dark:text-gray-300"
                        >Next</button>
                    </div>
                </div>
            </div>

            <!-- API Token -->
            <div class="bg-white dark:bg-gray-800 shadow rounded-lg">
                <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                    <h2 class="text-lg font-medium text-gray-900 dark:text-white">API Token</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Token de acceso para integración con la API de Ximbra</p>
                </div>
                <div class="px-6 py-4">
                    <ApiTokenWidget
                        :tenant-id="tenantId"
                        :can-manage="canManage"
                        @error="error = $event"
                    />
                </div>
            </div>

        </template>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from "vue";
import { useRoute } from "vue-router";
import { useAuth } from "@/composables/useAuth";
import { useTenant } from "@/composables/useTenant";
import { tenantApi } from "@/api/tenant";
import NotificationBanner from "@/components/NotificationBanner.vue";
import ApiTokenWidget from "@/components/tenants/ApiTokenWidget.vue";

const route = useRoute();
const tenantId = computed(() => route.params.id);

const { user } = useAuth();
const { fetchTenant, tenant, loading } = useTenant();

const members = ref([]);
const membersLoading = ref(false);
const error = ref(null);
const memberPage = ref(1);
const memberPageSize = 10;

const canManage = computed(() => tenant.value?.is_owner === true || user.value?.is_superuser === true);

// Paginación client-side para members (bounded por max_users del tenant)
const memberPages = computed(() => Math.ceil(members.value.length / memberPageSize));
const memberPageStart = computed(() => (memberPage.value - 1) * memberPageSize + 1);
const memberPageEnd = computed(() => Math.min(memberPage.value * memberPageSize, members.value.length));
const paginatedMembers = computed(() => {
    const start = (memberPage.value - 1) * memberPageSize;
    return members.value.slice(start, start + memberPageSize);
});

// Add member
const showAddMember = ref(false);
const adding = ref(false);
const addForm = reactive({ email: "", role: "MEMBER" });

function cancelAdd() {
    showAddMember.value = false;
    addForm.email = "";
    addForm.role = "MEMBER";
}

async function handleAddMember() {
    adding.value = true;
    try {
        await tenantApi.addMember(tenantId.value, { email: addForm.email, role: addForm.role });
        cancelAdd();
        await loadMembers();
    } catch (e) {
        error.value = e.response?.data?.detail || e.response?.data?.email?.[0] || "Failed to add member";
    } finally {
        adding.value = false;
    }
}

async function handleRemove(userId) {
    if (!confirm("Remove this member?")) return;
    try {
        await tenantApi.removeMember(tenantId.value, userId);
        await loadMembers();
    } catch (e) {
        error.value = e.response?.data?.detail || "Failed to remove member";
    }
}

async function handleRoleChange(userId, newRole) {
    try {
        await tenantApi.changeRole(tenantId.value, userId, newRole);
        await loadMembers();
    } catch (e) {
        error.value = e.response?.data?.detail || "Failed to change role";
    }
}

async function loadMembers() {
    membersLoading.value = true;
    try {
        const response = await tenantApi.listMembers(tenantId.value);
        members.value = response.data.results ?? response.data;
    } catch (e) {
        error.value = e.response?.data?.detail || "Failed to load members";
    } finally {
        membersLoading.value = false;
    }
}

function formatDate(dateStr) {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString();
}

onMounted(async () => {
    await fetchTenant(tenantId.value);
    await loadMembers();
});
</script>
