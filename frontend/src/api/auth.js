import api from "./index";

export const authApi = {
    login(email, password) {
        return api.post("/api/users/login/", { email, password });
    },

    register(data) {
        return api.post("/api/users/register/", data);
    },

    verifyEmail(token) {
        return api.post("/api/users/verify-email/", { token });
    },

    forgotPassword(email) {
        return api.post("/api/users/forgot-password/", { email });
    },

    resetPassword(token, password) {
        return api.post("/api/users/reset-password/", { token, password });
    },

    changePassword(data) {
        return api.post("/api/users/change-password/", data);
    },

    selectTenant(tenantId) {
        return api.post("/api/users/select-tenant/", { tenant_id: tenantId });
    },

    getProfile() {
        return api.get("/api/users/me/");
    },

    updateProfile(data) {
        return api.patch("/api/users/me/", data);
    },

    logout() {
        return api.post("/api/users/logout/");
    },
};
