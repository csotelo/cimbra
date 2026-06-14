<template>
    <div class="max-w-2xl">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Profile</h1>

        <NotificationBanner v-if="error" type="error" :message="error" @close="error = null" />
        <NotificationBanner v-if="success" type="success" :message="success" @close="success = null" />

        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
            <h2 class="text-lg font-medium text-gray-900 dark:text-white mb-4">Account Information</h2>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Email</label>
                    <p class="mt-1 text-sm text-gray-900 dark:text-gray-100">{{ user?.email }}</p>
                </div>
                <div v-if="user?.first_name || user?.last_name">
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Name</label>
                    <p class="mt-1 text-sm text-gray-900 dark:text-gray-100">
                        {{ [user?.first_name, user?.last_name].filter(Boolean).join(' ') }}
                    </p>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Verified</label>
                    <p class="mt-1 text-sm">
                        <span v-if="user?.is_verified" class="text-green-600">Verified</span>
                        <span v-else class="text-yellow-600">Not Verified</span>
                    </p>
                </div>
            </div>
        </div>

        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 class="text-lg font-medium text-gray-900 dark:text-white mb-4">Change Password</h2>
            <form @submit.prevent="handleChangePassword">
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Current Password</label>
                    <input
                        v-model="passwordForm.current_password"
                        type="password"
                        required
                        class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">New Password</label>
                    <input
                        v-model="passwordForm.new_password"
                        type="password"
                        required
                        minlength="8"
                        class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Confirm New Password</label>
                    <input
                        v-model="passwordForm.confirm_password"
                        type="password"
                        required
                        class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                </div>
                <div class="flex justify-end">
                    <button
                        type="submit"
                        :disabled="changingPassword"
                        class="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                    >
                        {{ changingPassword ? "Changing..." : "Change Password" }}
                    </button>
                </div>
            </form>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useAuth } from "@/composables/useAuth";
import NotificationBanner from "@/components/NotificationBanner.vue";

const { user, changePassword } = useAuth();

const error = ref(null);
const success = ref(null);
const changingPassword = ref(false);

const passwordForm = reactive({
    current_password: "",
    new_password: "",
    confirm_password: "",
});

async function handleChangePassword() {
    error.value = null;
    success.value = null;

    if (passwordForm.new_password !== passwordForm.confirm_password) {
        error.value = "New passwords do not match";
        return;
    }

    if (passwordForm.new_password.length < 8) {
        error.value = "Password must be at least 8 characters";
        return;
    }

    changingPassword.value = true;
    const result = await changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
    });

    if (result) {
        success.value = "Password changed successfully";
        passwordForm.current_password = "";
        passwordForm.new_password = "";
        passwordForm.confirm_password = "";
    } else {
        error.value = "Failed to change password. Check your current password.";
    }
    changingPassword.value = false;
}
</script>
