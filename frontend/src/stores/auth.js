import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { authApi } from "@/api/auth";
import router from "@/router";

export const useAuthStore = defineStore("auth", () => {
    const user = ref(null);
    const tenants = ref([]);
    const currentTenant = ref(null);
    const loading = ref(false);
    const error = ref(null);

    const isAuthenticated = computed(() => !!user.value);

    async function login(email, password) {
        loading.value = true;
        error.value = null;
        try {
            const response = await authApi.login(email, password);
            const { tenant_list } = response.data;

            tenants.value = tenant_list || [];

            if (tenants.value.length > 0) {
                currentTenant.value = tenants.value[0];
                await selectTenant(currentTenant.value.id);
            }

            await fetchProfile();

            return true;
        } catch (err) {
            error.value = err.response?.data?.detail || "Login failed";
            return false;
        } finally {
            loading.value = false;
        }
    }

    async function register(data) {
        loading.value = true;
        error.value = null;
        try {
            await authApi.register(data);
            return true;
        } catch (err) {
            error.value = err.response?.data || "Registration failed";
            return false;
        } finally {
            loading.value = false;
        }
    }

    async function verifyEmail(token) {
        loading.value = true;
        error.value = null;
        try {
            await authApi.verifyEmail(token);
            return true;
        } catch (err) {
            error.value = err.response?.data?.detail || "Verification failed";
            return false;
        } finally {
            loading.value = false;
        }
    }

    async function forgotPassword(email) {
        loading.value = true;
        error.value = null;
        try {
            await authApi.forgotPassword(email);
            return true;
        } catch (err) {
            error.value = err.response?.data?.detail || "Request failed";
            return false;
        } finally {
            loading.value = false;
        }
    }

    async function resetPassword(token, password) {
        loading.value = true;
        error.value = null;
        try {
            await authApi.resetPassword(token, password);
            return true;
        } catch (err) {
            error.value = err.response?.data?.detail || "Reset failed";
            return false;
        } finally {
            loading.value = false;
        }
    }

    async function changePassword(data) {
        loading.value = true;
        error.value = null;
        try {
            await authApi.changePassword(data);
            return true;
        } catch (err) {
            error.value = err.response?.data?.detail || "Change password failed";
            return false;
        } finally {
            loading.value = false;
        }
    }

    async function selectTenant(tenantId) {
        try {
            await authApi.selectTenant(tenantId);
            currentTenant.value = tenants.value.find((t) => t.id === tenantId);
            return true;
        } catch (err) {
            error.value = "Failed to select tenant";
            return false;
        }
    }

    async function fetchProfile() {
        try {
            const response = await authApi.getProfile();
            user.value = response.data;
        } catch (err) {
            console.error("Failed to fetch profile:", err);
            user.value = null;
            throw err;
        }
    }

    async function logout() {
        user.value = null;
        tenants.value = [];
        currentTenant.value = null;
        router._authCheckPromise = null;
        try {
            await authApi.logout();
        } catch (err) {
            console.error("Logout error:", err);
        }
        router.push("/login");
    }

    return {
        user,
        tenants,
        currentTenant,
        loading,
        error,
        isAuthenticated,
        login,
        register,
        verifyEmail,
        forgotPassword,
        resetPassword,
        changePassword,
        selectTenant,
        fetchProfile,
        logout,
    };
});
