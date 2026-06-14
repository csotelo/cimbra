<template>
    <div class="min-h-screen flex items-center justify-center bg-gray-100">
        <div class="max-w-md w-full bg-white rounded-lg shadow-md p-8">
            <h1 class="text-2xl font-bold text-center mb-6">Reset Password</h1>

            <NotificationBanner v-if="success" type="success" message="Password reset link sent! Check your email." />
            <NotificationBanner v-else-if="error" type="error" :message="error" @close="clearError" />

            <form v-if="!success" @submit.prevent="handleForgotPassword" class="space-y-4">
                <div>
                    <label for="email" class="block text-sm font-medium text-gray-700">
                        Email
                    </label>
                    <input
                        id="email"
                        v-model="form.email"
                        type="email"
                        required
                        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        placeholder="you@example.com"
                    />
                </div>

                <button
                    type="submit"
                    :disabled="loading"
                    class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                    {{ loading ? "Sending..." : "Send Reset Link" }}
                </button>
            </form>

            <div class="mt-6 text-center text-sm">
                <router-link
                    to="/login"
                    class="font-medium text-indigo-600 hover:text-indigo-500"
                >
                    Back to Sign In
                </router-link>
            </div>
        </div>
    </div>
</template>

<script setup>
import { reactive } from "vue";
import { useAuth } from "@/composables/useAuth";
import NotificationBanner from "@/components/NotificationBanner.vue";

const { forgotPassword, loading, error, clearError } = useAuth();

const form = reactive({
    email: "",
});

const success = ref(false);

async function handleForgotPassword() {
    clearError();
    const result = await forgotPassword(form.email);
    if (result) {
        success.value = true;
    }
}
</script>

<script>
import { ref } from "vue";
export default { name: "ForgotPasswordView" };
</script>
