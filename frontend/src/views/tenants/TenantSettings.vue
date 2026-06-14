<template>
    <div class="max-w-3xl">
        <div class="flex items-center space-x-3 mb-6">
            <router-link
                :to="`/tenants/${tenantId}`"
                class="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            >
                ← {{ tenant?.name || 'Tenant' }}
            </router-link>
            <span class="text-gray-300 dark:text-gray-600">/</span>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        </div>

        <NotificationBanner v-if="error" type="error" :message="error" @close="error = null" />
        <NotificationBanner v-if="success" type="success" :message="success" @close="success = null" />

        <div v-if="loading" class="text-center py-10">
            <p class="text-gray-500 dark:text-gray-400">Loading...</p>
        </div>

        <template v-else-if="tenant">
            <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
                <h2 class="text-lg font-medium text-gray-900 dark:text-white mb-4">General Settings</h2>
                <form @submit.prevent="handleUpdate">
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                        <input
                            v-model="form.name"
                            type="text"
                            required
                            class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                    </div>
                    <div class="flex justify-end">
                        <button
                            type="submit"
                            :disabled="saving"
                            class="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                        >
                            {{ saving ? "Saving..." : "Save Changes" }}
                        </button>
                    </div>
                </form>
            </div>

            <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-red-200 dark:border-red-900">
                <h2 class="text-lg font-medium text-red-600 dark:text-red-400 mb-2">Danger Zone</h2>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    Deactivates this tenant and all associated data. This action cannot be undone.
                </p>
                <button
                    @click="confirmDelete"
                    class="px-4 py-2 border border-red-300 dark:border-red-700 text-sm font-medium rounded-md text-red-600 dark:text-red-400 bg-white dark:bg-gray-800 hover:bg-red-50 dark:hover:bg-red-900"
                >
                    Delete Tenant
                </button>
            </div>
        </template>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useTenant } from "@/composables/useTenant";
import NotificationBanner from "@/components/NotificationBanner.vue";

const route = useRoute();
const router = useRouter();
const tenantId = route.params.id;

const { fetchTenant, tenant, updateTenant, deleteTenant, loading } = useTenant();

const form = reactive({ name: "" });
const saving = ref(false);
const error = ref(null);
const success = ref(null);

async function handleUpdate() {
    saving.value = true;
    error.value = null;
    success.value = null;
    const result = await updateTenant(tenantId, form);
    if (result) {
        success.value = "Tenant updated successfully";
        form.name = result.name;
    } else {
        error.value = "Failed to update tenant";
    }
    saving.value = false;
}

function confirmDelete() {
    if (window.confirm("Are you sure you want to delete this tenant? This action cannot be undone.")) {
        handleDelete();
    }
}

async function handleDelete() {
    const result = await deleteTenant(tenantId);
    if (result) {
        router.push("/dashboard");
    } else {
        error.value = "Failed to delete tenant";
    }
}

onMounted(async () => {
    await fetchTenant(tenantId);
    if (tenant.value) {
        form.name = tenant.value.name;
    }
});
</script>
