<template>
    <AuthLayout>
        <div>
            <h2 class="text-xl font-semibold mb-1 text-gray-900 dark:text-white">Crear cuenta</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Regístrate para acceder al sistema</p>

            <!-- Registro deshabilitado -->
            <div v-if="!configStore.allowSelfRegistration"
                 class="p-4 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800
                        text-sm text-amber-800 dark:text-amber-400 mb-4">
                <p class="font-medium mb-1">Registro no disponible</p>
                <p class="opacity-80">
                    El registro de nuevos usuarios está deshabilitado. Solicita una invitación al administrador del sistema.
                </p>
            </div>

            <div v-if="success"
                 class="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800
                        flex items-start gap-3 text-sm text-green-700 dark:text-green-400">
                <svg class="w-5 h-5 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
                <div>
                    <p class="font-medium">¡Cuenta creada!</p>
                    <p class="mt-0.5 opacity-80">Revisa tu correo para verificar tu cuenta.</p>
                </div>
            </div>

            <div v-else-if="errorMsg"
                 class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800
                        flex items-start gap-2 text-sm text-red-700 dark:text-red-400">
                <svg class="w-4 h-4 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
                <span>{{ errorMsg }}</span>
                <button @click="clearError" class="ml-auto shrink-0 opacity-60 hover:opacity-100">✕</button>
            </div>

            <form v-if="!success && configStore.allowSelfRegistration" @submit.prevent="handleRegister" class="space-y-4">
                <div>
                    <label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Correo electrónico
                    </label>
                    <input id="email" v-model="form.email" type="email" required autocomplete="email"
                        placeholder="tucorreo@ejemplo.com"
                        class="block w-full rounded-lg border-gray-300 dark:border-gray-600
                               dark:bg-gray-800 dark:text-white dark:placeholder-gray-500
                               shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm transition-colors" />
                    <p v-if="fieldErrors.email" class="mt-1 text-xs text-red-600 dark:text-red-400">{{ fieldErrors.email }}</p>
                </div>

                <div>
                    <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Contraseña <span class="text-gray-400 font-normal">(mínimo 8 caracteres)</span>
                    </label>
                    <div class="relative">
                        <input id="password" v-model="form.password"
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
                    <p v-if="fieldErrors.password" class="mt-1 text-xs text-red-600 dark:text-red-400">{{ fieldErrors.password }}</p>
                </div>

                <div>
                    <label for="password_confirm" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Confirmar contraseña
                    </label>
                    <input id="password_confirm" v-model="form.password_confirm"
                        :type="showPwd ? 'text' : 'password'"
                        required autocomplete="new-password"
                        placeholder="••••••••"
                        class="block w-full rounded-lg border-gray-300 dark:border-gray-600
                               dark:bg-gray-800 dark:text-white dark:placeholder-gray-500
                               shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm transition-colors" />
                    <p v-if="fieldErrors.password_confirm" class="mt-1 text-xs text-red-600 dark:text-red-400">{{ fieldErrors.password_confirm }}</p>
                </div>

                <button type="submit" :disabled="loading"
                    class="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg
                           bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800
                           text-white text-sm font-semibold shadow-sm
                           focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                           dark:focus:ring-offset-gray-900
                           disabled:opacity-60 disabled:cursor-not-allowed transition-colors">
                    <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    {{ loading ? "Creando cuenta..." : "Crear cuenta" }}
                </button>
            </form>

            <p class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
                ¿Ya tienes cuenta?
                <router-link to="/login" class="font-medium text-indigo-600 dark:text-indigo-400 hover:underline">
                    Iniciar sesión
                </router-link>
            </p>
        </div>
    </AuthLayout>
</template>

<script setup>
import { reactive, ref, computed } from "vue";
import { useAuth } from "@/composables/useAuth";
import { useConfigStore } from "@/stores/config";
import AuthLayout from "@/layouts/AuthLayout.vue";

const configStore = useConfigStore();

const { register, loading, error, clearError } = useAuth();

const showPwd = ref(false);
const success = ref(false);
const fieldErrors = reactive({});
const form = reactive({ email: "", password: "", password_confirm: "" });

const errorMsg = computed(() => {
    if (!error.value) return null;
    if (typeof error.value === "string") return error.value;
    const first = Object.values(error.value).flat()[0];
    return first || "Error al crear la cuenta";
});

function validate() {
    Object.keys(fieldErrors).forEach(k => delete fieldErrors[k]);
    if (form.password.length < 8) {
        fieldErrors.password = "Mínimo 8 caracteres";
        return false;
    }
    if (form.password !== form.password_confirm) {
        fieldErrors.password_confirm = "Las contraseñas no coinciden";
        return false;
    }
    return true;
}

async function handleRegister() {
    clearError();
    if (!validate()) return;
    const result = await register(form);
    if (result) success.value = true;
}
</script>
