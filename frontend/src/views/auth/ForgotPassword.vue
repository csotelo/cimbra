<template>
    <AuthLayout>
        <div>
            <h2 class="text-xl font-semibold mb-1 text-gray-900 dark:text-white">Recuperar contraseña</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
                Ingresa tu correo y te enviaremos un enlace para restablecer tu contraseña.
            </p>

            <div v-if="success"
                 class="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800
                        flex items-start gap-3 text-sm text-green-700 dark:text-green-400 mb-4">
                <svg class="w-5 h-5 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
                <div>
                    <p class="font-medium">¡Correo enviado!</p>
                    <p class="mt-0.5 opacity-80">Revisa tu bandeja de entrada y sigue las instrucciones.</p>
                </div>
            </div>

            <div v-else-if="error"
                 class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800
                        flex items-start gap-2 text-sm text-red-700 dark:text-red-400">
                <svg class="w-4 h-4 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
                <span>{{ error }}</span>
                <button @click="clearError" class="ml-auto shrink-0 opacity-60 hover:opacity-100">✕</button>
            </div>

            <form v-if="!success" @submit.prevent="handleSubmit" class="space-y-4">
                <div>
                    <label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Correo electrónico
                    </label>
                    <input id="email" v-model="email" type="email" required autocomplete="email"
                        placeholder="tucorreo@ejemplo.com"
                        class="block w-full rounded-lg border-gray-300 dark:border-gray-600
                               dark:bg-gray-800 dark:text-white dark:placeholder-gray-500
                               shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm transition-colors" />
                </div>

                <button type="submit" :disabled="loading"
                    class="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg
                           bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-sm
                           focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                           dark:focus:ring-offset-gray-900
                           disabled:opacity-60 disabled:cursor-not-allowed transition-colors">
                    <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    {{ loading ? "Enviando..." : "Enviar enlace de recuperación" }}
                </button>
            </form>

            <p class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
                <router-link to="/login" class="font-medium text-indigo-600 dark:text-indigo-400 hover:underline">
                    ← Volver al inicio de sesión
                </router-link>
            </p>
        </div>
    </AuthLayout>
</template>

<script setup>
import { ref } from "vue";
import { useAuth } from "@/composables/useAuth";
import AuthLayout from "@/layouts/AuthLayout.vue";

const { forgotPassword, loading, error, clearError } = useAuth();
const email = ref("");
const success = ref(false);

async function handleSubmit() {
    clearError();
    const result = await forgotPassword(email.value);
    if (result) success.value = true;
}
</script>
