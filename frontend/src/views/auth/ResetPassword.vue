<template>
    <div class="min-h-screen flex items-center justify-center bg-gray-100">
        <div class="max-w-md w-full bg-white rounded-lg shadow-md p-8">
            <h1 class="text-2xl font-bold text-center mb-6">Set New Password</h1>

            <NotificationBanner v-if="success" type="success" message="Password reset successfully!" />
            <NotificationBanner v-else-if="error" type="error" :message="error" @close="clearError" />

            <form v-if="!success" @submit.prevent="handleResetPassword" class="space-y-4">
                <div>
                    <label for="password" class="block text-sm font-medium text-gray-700">
                        New Password
                    </label>
                    <input
                        id="password"
                        v-model="form.password"
                        type="password"
                        required
                        minlength="8"
                        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                    <p v-if="errors.password" class="mt-1 text-sm text-red-600">{{ errors.password[0] }}</p>
                </div>

                <div>
                    <label for="password_confirm" class="block text-sm font-medium text-gray-700">
                        Confirm Password
                    </label>
                    <input
                        id="password_confirm"
                        v-model="form.password_confirm"
                        type="password"
                        required
                        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                    <p v-if="errors.password_confirm" class="mt-1 text-sm text-red-600">{{ errors.password_confirm[0] }}</p>
                </div>

                <button
                    type="submit"
                    :disabled="loading"
                    class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                    {{ loading ? "Resetting..." : "Reset Password" }}
                </button>
            </form>

            <div v-if="success" class="mt-6 text-center">
                <router-link
                    to="/login"
                    class="font-medium text-indigo-600 hover:text-indigo-500"
                >
                    Go to Sign In
                </router-link>
            </div>
        </div>
    </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuth } from "@/composables/useAuth";
import NotificationBanner from "@/components/NotificationBanner.vue";

const route = useRoute();
const router = useRouter();
const { resetPassword, loading, error, clearError } = useAuth();

const form = reactive({
    password: "",
    password_confirm: "",
});

const errors = reactive({});
const success = ref(false);

function validate() {
    Object.keys(errors).forEach((key) => delete errors[key]);
    let valid = true;

    if (form.password !== form.password_confirm) {
        errors.password_confirm = ["Passwords do not match"];
        valid = false;
    }

    if (form.password.length < 8) {
        errors.password = ["Password must be at least 8 characters"];
        valid = false;
    }

    return valid;
}

async function handleResetPassword() {
    clearError();
    if (!validate()) return;

    const token = route.query.token || route.params.token;
    if (!token) {
        error.value = "Invalid reset link";
        return;
    }

    const result = await resetPassword(token, form.password);
    if (result) {
        success.value = true;
    }
}
</script>
