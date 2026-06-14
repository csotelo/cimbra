import { computed } from "vue";
import { useAuthStore } from "@/stores/auth";

export function useAuth() {
    const authStore = useAuthStore();

    const user = computed(() => authStore.user);
    const isAuthenticated = computed(() => authStore.isAuthenticated);
    const loading = computed(() => authStore.loading);
    const error = computed(() => authStore.error);
    const currentTenant = computed(() => authStore.currentTenant);

    async function login(email, password) {
        return authStore.login(email, password);
    }

    async function register(data) {
        return authStore.register(data);
    }

    async function verifyEmail(token) {
        return authStore.verifyEmail(token);
    }

    async function forgotPassword(email) {
        return authStore.forgotPassword(email);
    }

    async function resetPassword(token, password) {
        return authStore.resetPassword(token, password);
    }

    async function changePassword(data) {
        return authStore.changePassword(data);
    }

    function logout() {
        authStore.logout();
    }

    function clearError() {
        authStore.error = null;
    }

    return {
        user,
        isAuthenticated,
        loading,
        error,
        currentTenant,
        login,
        register,
        verifyEmail,
        forgotPassword,
        resetPassword,
        changePassword,
        logout,
        clearError,
    };
}
