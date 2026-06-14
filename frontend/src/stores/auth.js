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
            error.value = err.response?.data?.detail || "Correo o contraseña incorrectos.";
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
            error.value = err.response?.data || "Error al crear la cuenta.";
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
            error.value = err.response?.data?.detail || "El enlace de verificación no es válido o ha expirado.";
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
            error.value = err.response?.data?.detail || "Error al enviar el correo de recuperación.";
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
            error.value = err.response?.data?.detail || "El enlace de recuperación no es válido o ha expirado.";
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
            error.value = err.response?.data?.detail || "Error al cambiar la contraseña.";
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
            error.value = "Error al seleccionar la organización.";
            return false;
        }
    }

    async function fetchProfile() {
        try {
            const response = await authApi.getProfile();
            user.value = response.data;
        } catch (err) {
            console.error("Error al cargar el perfil:", err);
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
            console.error("Error al cerrar sesión:", err);
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
