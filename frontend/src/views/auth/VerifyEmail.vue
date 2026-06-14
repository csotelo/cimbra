<template>
    <div class="min-h-screen flex items-center justify-center bg-gray-100">
        <div class="max-w-md w-full bg-white rounded-lg shadow-md p-8">
            <div v-if="loading" class="text-center">
                <p class="text-gray-600">Verifying your email...</p>
            </div>

            <div v-else-if="success" class="text-center">
                <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                    <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                </div>
                <h2 class="mt-4 text-xl font-bold text-gray-900">Email Verified!</h2>
                <p class="mt-2 text-gray-600">Your email has been verified successfully.</p>
                <router-link
                    to="/login"
                    class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                >
                    Go to Login
                </router-link>
            </div>

            <div v-else class="text-center">
                <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                    <svg class="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </div>
                <h2 class="mt-4 text-xl font-bold text-gray-900">Verification Failed</h2>
                <p class="mt-2 text-gray-600">{{ error || "The verification link is invalid or has expired." }}</p>
                <router-link
                    to="/login"
                    class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                >
                    Go to Login
                </router-link>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { useAuth } from "@/composables/useAuth";

const route = useRoute();
const { verifyEmail, loading, error } = useAuth();

const success = ref(false);

onMounted(async () => {
    const token = route.query.token;
    if (token) {
        const result = await verifyEmail(token);
        success.value = result;
    }
});
</script>
