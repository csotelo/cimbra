<template>
    <div class="max-w-2xl">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-1">Mi Perfil</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Información de tu cuenta y seguridad.</p>

        <div v-if="toast"
             class="mb-4 p-3 rounded-lg flex items-center gap-2 text-sm"
             :class="toast.type === 'ok'
                ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400'
                : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400'">
            {{ toast.msg }}
        </div>

        <!-- Información de cuenta -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
            <h2 class="text-base font-semibold text-gray-900 dark:text-white border-b border-gray-100 dark:border-gray-700 pb-2 mb-4">
                Información de la cuenta
            </h2>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                        Correo electrónico
                    </label>
                    <p class="text-sm text-gray-900 dark:text-gray-100 font-medium">{{ user?.email }}</p>
                </div>

                <div v-if="user?.first_name || user?.last_name">
                    <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                        Nombre
                    </label>
                    <p class="text-sm text-gray-900 dark:text-gray-100">
                        {{ [user?.first_name, user?.last_name].filter(Boolean).join(' ') }}
                    </p>
                </div>

                <div>
                    <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                        Estado de verificación
                    </label>
                    <span v-if="user?.is_verified"
                          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30
                                 text-green-700 dark:text-green-400 text-xs font-medium">
                        <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                        </svg>
                        Verificado
                    </span>
                    <span v-else
                          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/30
                                 text-amber-700 dark:text-amber-400 text-xs font-medium">
                        <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                        </svg>
                        Sin verificar
                    </span>
                </div>

                <div v-if="user?.is_superuser">
                    <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                        Rol
                    </label>
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/30
                                 text-indigo-700 dark:text-indigo-400 text-xs font-medium">
                        Superadministrador
                    </span>
                </div>
            </div>
        </div>

        <!-- Cambiar contraseña -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 class="text-base font-semibold text-gray-900 dark:text-white border-b border-gray-100 dark:border-gray-700 pb-2 mb-4">
                Cambiar contraseña
            </h2>
            <form @submit.prevent="handleChangePassword" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Contraseña actual
                    </label>
                    <div class="relative">
                        <input v-model="passwordForm.current_password"
                            :type="showCurrent ? 'text' : 'password'"
                            required autocomplete="current-password"
                            placeholder="••••••••"
                            class="block w-full rounded-lg border-gray-300 dark:border-gray-600
                                   dark:bg-gray-900 dark:text-white dark:placeholder-gray-500
                                   shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm pr-10 transition-colors" />
                        <button type="button" @click="showCurrent = !showCurrent" tabindex="-1"
                            class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                            <svg v-if="showCurrent" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 4.411m0 0L21 21"/>
                            </svg>
                            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                            </svg>
                        </button>
                    </div>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Nueva contraseña <span class="text-gray-400 font-normal">(mínimo 8 caracteres)</span>
                    </label>
                    <div class="relative">
                        <input v-model="passwordForm.new_password"
                            :type="showNew ? 'text' : 'password'"
                            required minlength="8" autocomplete="new-password"
                            placeholder="••••••••"
                            class="block w-full rounded-lg border-gray-300 dark:border-gray-600
                                   dark:bg-gray-900 dark:text-white dark:placeholder-gray-500
                                   shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm pr-10 transition-colors" />
                        <button type="button" @click="showNew = !showNew" tabindex="-1"
                            class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                            <svg v-if="showNew" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 4.411m0 0L21 21"/>
                            </svg>
                            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                            </svg>
                        </button>
                    </div>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Confirmar nueva contraseña
                    </label>
                    <input v-model="passwordForm.confirm_password"
                        :type="showNew ? 'text' : 'password'"
                        required autocomplete="new-password"
                        placeholder="••••••••"
                        class="block w-full rounded-lg border-gray-300 dark:border-gray-600
                               dark:bg-gray-900 dark:text-white dark:placeholder-gray-500
                               shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm transition-colors" />
                </div>

                <div class="flex justify-end pt-2">
                    <button type="submit" :disabled="changingPassword"
                        class="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700
                               text-white text-sm font-semibold shadow-sm
                               focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                               dark:focus:ring-offset-gray-900
                               disabled:opacity-60 disabled:cursor-not-allowed transition-colors">
                        <svg v-if="changingPassword" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                        </svg>
                        {{ changingPassword ? "Guardando..." : "Cambiar contraseña" }}
                    </button>
                </div>
            </form>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useAuth } from "@/composables/useAuth";

const { user, changePassword } = useAuth();

const toast = ref(null);
const changingPassword = ref(false);
const showCurrent = ref(false);
const showNew = ref(false);

const passwordForm = reactive({
    current_password: "",
    new_password: "",
    confirm_password: "",
});

function showToast(msg, type = "ok") {
    toast.value = { msg, type };
    setTimeout(() => { toast.value = null; }, 4000);
}

async function handleChangePassword() {
    if (passwordForm.new_password !== passwordForm.confirm_password) {
        showToast("Las contraseñas nuevas no coinciden.", "err");
        return;
    }
    if (passwordForm.new_password.length < 8) {
        showToast("La contraseña debe tener al menos 8 caracteres.", "err");
        return;
    }

    changingPassword.value = true;
    const result = await changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
    });

    if (result) {
        showToast("Contraseña cambiada correctamente.");
        passwordForm.current_password = "";
        passwordForm.new_password = "";
        passwordForm.confirm_password = "";
    } else {
        showToast("Error al cambiar la contraseña. Verifica tu contraseña actual.", "err");
    }
    changingPassword.value = false;
}
</script>
