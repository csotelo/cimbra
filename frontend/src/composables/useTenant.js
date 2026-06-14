import { computed } from "vue";
import { useTenantStore } from "@/stores/tenant";

export function useTenant() {
    const tenantStore = useTenantStore();

    const tenants = computed(() => tenantStore.tenants);
    const tenantCount = computed(() => tenantStore.tenantCount);
    const tenantNext = computed(() => tenantStore.tenantNext);
    const tenantPrevious = computed(() => tenantStore.tenantPrevious);
    const tenant = computed(() => tenantStore.currentTenant);
    const currentTenant = computed(() => tenantStore.currentTenant);
    const members = computed(() => tenantStore.members);
    const loading = computed(() => tenantStore.loading);
    const error = computed(() => tenantStore.error);

    async function fetchTenants(params = {}) {
        return tenantStore.fetchTenants(params);
    }

    async function fetchTenant(id) {
        return tenantStore.fetchTenant(id);
    }

    async function createTenant(data) {
        return tenantStore.createTenant(data);
    }

    async function updateTenant(id, data) {
        return tenantStore.updateTenant(id, data);
    }

    async function deleteTenant(id) {
        return tenantStore.deleteTenant(id);
    }

    async function fetchMembers(tenantId) {
        return tenantStore.fetchMembers(tenantId);
    }

    async function addMember(tenantId, email, role) {
        return tenantStore.addMember(tenantId, email, role);
    }

    async function removeMember(tenantId, userId) {
        return tenantStore.removeMember(tenantId, userId);
    }

    async function changeRole(tenantId, userId, role) {
        return tenantStore.changeRole(tenantId, userId, role);
    }

    function clearError() {
        tenantStore.clearError();
    }

    return {
        tenants,
        tenantCount,
        tenantNext,
        tenantPrevious,
        tenant,
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
}
