<template>
    <AuthLayout>
        <div>
            <!-- Loading -->
            <div v-if="loading" class="flex flex-col items-center gap-3 py-4">
                <svg class="animate-spin w-8 h-8 text-indigo-500" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                <p class="text-sm text-gray-500 dark:text-gray-400">Validando invitación...</p>
            </div>

            <!-- Invalid token -->
            <div v-else-if="error" class="text-center py-2">
                <div class="flex items-center justify-center w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 mx-auto mb-3">
                    <svg class="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </div>
                <h2 class="text-base font-semibold text-gray-900 dark:text-white mb-1">Invitación inválida</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">{{ error }}</p>
                <router-link to="/login" class="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:underline">
                    Ir al inicio de sesión
                </router-link>
            </div>

            <!-- Form -->
            <template v-else>
                <h2 class="text-xl font-semibold mb-1 text-gray-900 dark:text-white">Crear tu cuenta</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
                    Invitado como <span class="font-medium text-indigo-600 dark:text-indigo-400">{{ invitedEmail }}</span>
                </p>

                <div v-if="successMsg"
                     class="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800
                            flex items-start gap-3 text-sm text-green-700 dark:text-green-400 mb-4">
                    <svg class="w-5 h-5 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                    </svg>
                    <div>
                        <p class="font-medium">¡Cuenta creada!</p>
                        <p class="mt-0.5">
                            {{ successMsg }}
                            <router-link to="/login" class="font-semibold underline ml-1">Iniciar sesión</router-link>
                        </p>
                    </div>
                </div>

                <form v-else @submit.prevent="handleAccept" class="space-y-4">
                    <div v-if="formError"
                         class="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800
                                text-sm text-red-700 dark:text-red-400">
                        {{ formError }}
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Correo electrónico
                        </label>
                        <input :value="invitedEmail" type="email" disabled
                            class="block w-full rounded-lg border-gray-200 dark:border-gray-700
                                   bg-gray-50 dark:bg-gray-800/50 text-gray-500 dark:text-gray-400
                                   shadow-sm sm:text-sm cursor-not-allowed" />
                    </div>

                    <div>
                        <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Contraseña <span class="text-gray-400 font-normal">(mínimo 8 caracteres)</span>
                        </label>
                        <div class="relative">
                            <input id="password" v-model="password"
                                :type="showPwd ? 'text' : 'password'"
                                required minlength="8" autocomplete="new-password"
                                placeholder="••••••••"
                                class="block w-full rounded-lg border-gray-300 dark:border-gray-600
                                       dark:bg-gray-800 dark:text-white dark:placeholder-gray-500
                                       shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm pr-10 transition-colors" />
                            <button type="button" @click="showPwd = !showPwd" tabindex="-1"
                                class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                                <svg v-if="showPwd" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 4.411m0 0L21 21"/>
                                </svg>
                                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                                </svg>
                            </button>
                        </div>
                    </div>

                    <button type="submit" :disabled="submitting"
                        class="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg
                               bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800
                               text-white text-sm font-semibold shadow-sm
                               focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                               dark:focus:ring-offset-gray-900
                               disabled:opacity-60 disabled:cursor-not-allowed transition-colors">
                        <svg v-if="submitting" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                        </svg>
                        {{ submitting ? "Creando cuenta..." : "Crear cuenta y acceder" }}
                    </button>
                </form>
            </template>
        </div>
    </AuthLayout>
</template>

<script setup>
import { ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "@/api/index";
import AuthLayout from "@/layouts/AuthLayout.vue";

const route = useRoute();
const token = route.params.token;

const loading = ref(true);
const error = ref(null);
const invitedEmail = ref("");
const password = ref("");
const showPwd = ref(false);
const submitting = ref(false);
const formError = ref(null);
const successMsg = ref(null);

import { onMounted } from "vue";
onMounted(async () => {
    try {
        const res = await api.get(`/api/users/invitations/${token}/`);
        invitedEmail.value = res.data.email;
    } catch (err) {
        error.value = err.response?.data?.detail || "Invitación inválida o expirada.";
    } finally {
        loading.value = false;
    }
});

async function handleAccept() {
    submitting.value = true;
    formError.value = null;
    try {
        await api.post(`/api/users/invitations/${token}/`, { password: password.value });
        successMsg.value = "Tu cuenta ha sido creada exitosamente.";
    } catch (err) {
        formError.value = err.response?.data?.detail || "Error al crear la cuenta.";
    } finally {
        submitting.value = false;
    }
}
</script>
