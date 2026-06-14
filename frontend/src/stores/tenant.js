import { defineStore } from "pinia";
import { ref } from "vue";
import { tenantApi } from "@/api/tenant";

export const useTenantStore = defineStore("tenant", () => {
    const tenants = ref([]);
    const tenantCount = ref(0);
    const tenantNext = ref(null);
    const tenantPrevious = ref(null);
    const currentTenant = ref(null);
    const members = ref([]);
    const loading = ref(false);
    const error = ref(null);

    async function fetchTenants(params = {}) {
        loading.value = true;
        error.value = null;
        try {
            const response = await tenantApi.list(params);
            const data = response.data;
            if (data.results !== undefined) {
                tenants.value = data.results;
                tenantCount.value = data.count;
                tenantNext.value = data.next;
                tenantPrevious.value = data.previous;
            } else {
                tenants.value = data;
                tenantCount.value = data.length;
                tenantNext.value = null;
                tenantPrevious.value = null;
            }
        } catch (err) {
            error.value = "Failed to fetch tenants";
        } finally {
            loading.value = false;
        }
    }

    async function fetchTenant(id) {
        loading.value = true;
        error.value = null;
        try {
            const response = await tenantApi.get(id);
            currentTenant.value = response.data;
            return response.data;
        } catch (err) {
            error.value = "Failed to fetch tenant";
            return null;
        } finally {
            loading.value = false;
        }
    }

    async function createTenant(data) {
        loading.value = true;
        error.value = null;
        try {
            const response = await tenantApi.create(data);
            tenants.value.push(response.data);
            return response.data;
        } catch (err) {
            error.value = err.response?.data || "Failed to create tenant";
            return null;
        } finally {
            loading.value = false;
        }
    }

    async function updateTenant(id, data) {
        loading.value = true;
        error.value = null;
        try {
            const response = await tenantApi.update(id, data);
            const index = tenants.value.findIndex((t) => t.id === id);
            if (index !== -1) {
                tenants.value[index] = response.data;
            }
            if (currentTenant.value?.id === id) {
                currentTenant.value = response.data;
            }
            return response.data;
        } catch (err) {
            error.value = err.response?.data || "Failed to update tenant";
            return null;
        } finally {
            loading.value = false;
        }
    }

    async function deleteTenant(id) {
        loading.value = true;
        error.value = null;
        try {
            await tenantApi.delete(id);
            tenants.value = tenants.value.filter((t) => t.id !== id);
            if (currentTenant.value?.id === id) {
                currentTenant.value = null;
            }
            return true;
        } catch (err) {
            error.value = "Failed to delete tenant";
            return false;
        } finally {
            loading.value = false;
        }
    }

    async function fetchMembers(tenantId) {
        loading.value = true;
        error.value = null;
        try {
            const response = await tenantApi.listMembers(tenantId);
            members.value = response.data.results || response.data;
        } catch (err) {
            error.value = "Failed to fetch members";
        } finally {
            loading.value = false;
        }
    }

    async function addMember(tenantId, email, role) {
        loading.value = true;
        error.value = null;
        try {
            const response = await tenantApi.addMember(tenantId, { email, role });
            members.value.push(response.data);
            return response.data;
        } catch (err) {
            error.value = err.response?.data?.detail || "Failed to add member";
            return null;
        } finally {
            loading.value = false;
        }
    }

    async function removeMember(tenantId, userId) {
        loading.value = true;
        error.value = null;
        try {
            await tenantApi.removeMember(tenantId, userId);
            members.value = members.value.filter(
                (m) => m.user.id !== userId
            );
            return true;
        } catch (err) {
            error.value = "Failed to remove member";
            return false;
        } finally {
            loading.value = false;
        }
    }

    async function changeRole(tenantId, userId, role) {
        loading.value = true;
        error.value = null;
        try {
            const response = await tenantApi.changeRole(tenantId, userId, role);
            const index = members.value.findIndex(
                (m) => m.user.id === userId
            );
            if (index !== -1) {
                members.value[index] = { ...members.value[index], role };
            }
            return response.data;
        } catch (err) {
            error.value = err.response?.data?.detail || "Failed to change role";
            return null;
        } finally {
            loading.value = false;
        }
    }

    function clearError() {
        error.value = null;
    }

    return {
        tenants,
        tenantCount,
        tenantNext,
        tenantPrevious,
        currentTenant,
        members,
        loading,
        error,
        fetchTenants,
        fetchTenant,
        createTenant,
        updateTenant,
        deleteTenant,
        fetchMembers,
        addMember,
        removeMember,
        changeRole,
        clearError,
    };
});
