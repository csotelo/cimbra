<template>
    <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
        <div class="w-full max-w-md">
            <div class="text-center mb-8">
                <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Ximbra</h1>
                <p class="mt-2 text-gray-600 dark:text-gray-400">Sistema de Alertas de Tormentas</p>
            </div>

            <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-8">

                <div v-if="loading" class="text-center py-8">
                    <p class="text-gray-500 dark:text-gray-400">Validando invitación...</p>
                </div>

                <div v-else-if="error" class="text-center py-8">
                    <p class="text-red-600 dark:text-red-400 font-medium">{{ error }}</p>
                    <router-link to="/login" class="mt-4 inline-block text-sm text-indigo-600 dark:text-indigo-400 hover:underline">
                        Ir al inicio de sesión
                    </router-link>
                </div>

                <template v-else>
                    <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">Crear tu cuenta</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
                        Invitado como <strong>{{ invitedEmail }}</strong>
                    </p>

                    <div v-if="successMsg" class="mb-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-md text-sm text-green-700 dark:text-green-400">
                        {{ successMsg }}
                        <router-link to="/login" class="ml-2 font-medium underline">Iniciar sesión</router-link>
                    </div>

                    <form v-else @submit.prevent="handleAccept" class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                            <input
                                :value="invitedEmail"
                                type="email"
                                disabled
                                class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm bg-gray-50 text-gray-500 sm:text-sm"
                            />
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Contraseña</label>
                            <input
                                v-model="password"
                                type="password"
                                required
                                minlength="8"
                                placeholder="Mínimo 8 caracteres"
                                class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            />
                        </div>
                        <div v-if="formError" class="text-sm text-red-600 dark:text-red-400">{{ formError }}</div>
                        <button
                            type="submit"
                            :disabled="submitting"
                            class="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-md disabled:opacity-50"
                        >
                            {{ submitting ? 'Creando cuenta...' : 'Crear cuenta y acceder' }}
                        </button>
                    </form>
                </template>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { api } from "@/api/index";

const route = useRoute();
const token = route.params.token;

const loading = ref(true);
const error = ref(null);
const invitedEmail = ref("");
const password = ref("");
const submitting = ref(false);
const formError = ref(null);
const successMsg = ref(null);

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
        successMsg.value = "Cuenta creada exitosamente.";
    } catch (err) {
        formError.value = err.response?.data?.detail || "Error al crear la cuenta.";
    } finally {
        submitting.value = false;
    }
}
</script>
