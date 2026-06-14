<template>
    <AuthLayout>
        <div class="text-center">
            <!-- Loading -->
            <div v-if="loading" class="flex flex-col items-center gap-3">
                <svg class="animate-spin w-10 h-10 text-indigo-500" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                <p class="text-sm text-gray-500 dark:text-gray-400">Verificando tu correo electrónico...</p>
            </div>

            <!-- Success -->
            <div v-else-if="success" class="flex flex-col items-center gap-4">
                <div class="flex items-center justify-center w-14 h-14 rounded-full bg-green-100 dark:bg-green-900/30">
                    <svg class="w-7 h-7 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                    </svg>
                </div>
                <div>
                    <h2 class="text-lg font-semibold text-gray-900 dark:text-white">¡Correo verificado!</h2>
                    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Tu cuenta ha sido activada correctamente.</p>
                </div>
                <router-link to="/login"
                    class="mt-2 inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700
                           text-white text-sm font-semibold shadow-sm transition-colors">
                    Ir al inicio de sesión →
                </router-link>
            </div>

            <!-- Error / no token -->
            <div v-else class="flex flex-col items-center gap-4">
                <div class="flex items-center justify-center w-14 h-14 rounded-full bg-red-100 dark:bg-red-900/30">
                    <svg class="w-7 h-7 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </div>
                <div>
                    <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Verificación fallida</h2>
                    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        {{ errorMsg }}
                    </p>
                </div>
                <router-link to="/login"
                    class="mt-2 inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600
                           text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                    ← Volver al inicio de sesión
                </router-link>
            </div>
        </div>
    </AuthLayout>
</template>

<script setup>
import { onMounted, ref, computed } from "vue";
import { useRoute } from "vue-router";
import { useAuth } from "@/composables/useAuth";
import AuthLayout from "@/layouts/AuthLayout.vue";

const route = useRoute();
const { verifyEmail, loading, error } = useAuth();

const success = ref(false);

const errorMsg = computed(() => {
    if (error.value) {
        if (typeof error.value === "string") return error.value;
        return Object.values(error.value).flat()[0] || "El enlace de verificación es inválido o ha expirado.";
    }
    return "El enlace de verificación es inválido o ha expirado.";
});

onMounted(async () => {
    const token = route.query.token;
    if (token) {
        const result = await verifyEmail(token);
        success.value = !!result;
    }
});
</script>
