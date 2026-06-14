<template>
    <div class="min-h-screen flex items-center justify-center bg-gray-100">
        <div class="max-w-md w-full bg-white rounded-lg shadow-md p-8">
            <h1 class="text-2xl font-bold text-center mb-6">Create Account</h1>

            <NotificationBanner v-if="error" type="error" :message="errorMessage" @close="clearError" />
            <NotificationBanner v-if="success" type="success" message="Registration successful! Please check your email to verify your account." />

            <form v-if="!success" @submit.prevent="handleRegister" class="space-y-4">
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
                    <p v-if="errors.email" class="mt-1 text-sm text-red-600">{{ errors.email[0] }}</p>
                </div>

                <div>
                    <label for="password" class="block text-sm font-medium text-gray-700">
                        Password
                    </label>
                    <div class="relative mt-1">
                        <input
                            id="password"
                            v-model="form.password"
                            :type="showPassword ? 'text' : 'password'"
                            required
                            minlength="8"
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm pr-10"
                        />
                        <button
                            type="button"
                            @click="showPassword = !showPassword"
                            class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
                            tabindex="-1"
                        >
                            <svg v-if="showPassword" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 4.411m0 0L21 21"/>
                            </svg>
                            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                            </svg>
                        </button>
                    </div>
                    <p v-if="errors.password" class="mt-1 text-sm text-red-600">{{ errors.password[0] }}</p>
                </div>

                <div>
                    <label for="password_confirm" class="block text-sm font-medium text-gray-700">
                        Confirm Password
                    </label>
                    <div class="relative mt-1">
                        <input
                            id="password_confirm"
                            v-model="form.password_confirm"
                            :type="showPassword ? 'text' : 'password'"
                            required
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm pr-10"
                        />
                    </div>
                </div>

                <button
                    type="submit"
                    :disabled="loading"
                    class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                    {{ loading ? "Creating account..." : "Create Account" }}
                </button>
            </form>

            <div class="mt-6 text-center text-sm">
                <router-link
                    to="/login"
                    class="font-medium text-indigo-600 hover:text-indigo-500"
                >
                    Already have an account? Sign in
                </router-link>
            </div>
        </div>
    </div>
</template>

<script setup>
import { reactive, computed, ref } from "vue";
import { useAuth } from "@/composables/useAuth";
import NotificationBanner from "@/components/NotificationBanner.vue";

const { register, loading, error, clearError } = useAuth();

const form = reactive({
    email: "",
    password: "",
    password_confirm: "",
});

const errors = reactive({});
const success = ref(false);
const showPassword = ref(false);

const errorMessage = computed(() => {
    if (typeof error.value === "object") {
        return JSON.stringify(error.value);
    }
    return error.value;
});

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

async function handleRegister() {
    clearError();
    if (!validate()) return;

    const result = await register(form);
    if (result) {
        success.value = true;
    }
}
</script>

<script>
export default { name: "RegisterView" };
</script>
