import api from "./index";

export const tenantApi = {
    list(params = {}) {
        return api.get("/api/tenants/", { params });
    },

    get(id) {
        return api.get(`/api/tenants/${id}/`);
    },

    create(data) {
        return api.post("/api/tenants/", data);
    },

    update(id, data) {
        return api.patch(`/api/tenants/${id}/`, data);
    },

    delete(id) {
        return api.delete(`/api/tenants/${id}/`);
    },

    listMembers(tenantId) {
        return api.get(`/api/tenants/${tenantId}/members/`);
    },

    addMember(tenantId, data) {
        return api.post(`/api/tenants/${tenantId}/members/`, data);
    },

    removeMember(tenantId, userId) {
        return api.delete(`/api/tenants/${tenantId}/members/${userId}/`);
    },

    changeRole(tenantId, userId, role) {
        return api.patch(`/api/tenants/${tenantId}/members/${userId}/role/`, { role });
    },

    getToken(tenantId) {
        return api.get(`/api/tenants/${tenantId}/token/`);
    },

    createToken(tenantId, data = {}) {
        return api.post(`/api/tenants/${tenantId}/token/`, data);
    },

    revokeToken(tenantId) {
        return api.delete(`/api/tenants/${tenantId}/token/`);
    },
};
