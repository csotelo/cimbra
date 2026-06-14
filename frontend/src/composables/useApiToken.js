import { ref } from "vue";
import { tenantApi } from "@/api/tenant";

export function useApiToken() {
    const token = ref(null);
    const tokenStatus = ref(null);
    const loading = ref(false);
    const error = ref(null);
    const showToken = ref(false);
    const newlyCreatedToken = ref(null);

    async function fetchTokenStatus(tenantId) {
        loading.value = true;
        error.value = null;
        try {
            const response = await tenantApi.getToken(tenantId);
            tokenStatus.value = response.data;
            return response.data;
        } catch (err) {
            if (err.response?.status === 404) {
                tokenStatus.value = null;
                return null;
            }
            error.value = "Failed to fetch token status";
            return null;
        } finally {
            loading.value = false;
        }
    }

    async function createToken(tenantId, data = {}) {
        loading.value = true;
        error.value = null;
        newlyCreatedToken.value = null;
        try {
            const response = await tenantApi.createToken(tenantId, data);
            tokenStatus.value = response.data;
            newlyCreatedToken.value = response.data.token;
            showToken.value = true;
            return response.data;
        } catch (err) {
            error.value = err.response?.data?.detail || "Failed to create token";
            return null;
        } finally {
            loading.value = false;
        }
    }

    async function revokeToken(tenantId) {
        loading.value = true;
        error.value = null;
        try {
            await tenantApi.revokeToken(tenantId);
            tokenStatus.value = null;
            newlyCreatedToken.value = null;
            showToken.value = false;
            return true;
        } catch (err) {
            error.value = "Failed to revoke token";
            return false;
        } finally {
            loading.value = false;
        }
    }

    function copyToken() {
        if (newlyCreatedToken.value) {
            navigator.clipboard.writeText(newlyCreatedToken.value);
            return true;
        }
        return false;
    }

    function hideToken() {
        showToken.value = false;
    }

    function clearError() {
        error.value = null;
    }

    return {
        token,
        tokenStatus,
        loading,
        error,
        showToken,
        newlyCreatedToken,
        fetchTokenStatus,
        createToken,
        revokeToken,
        copyToken,
        hideToken,
        clearError,
    };
}
