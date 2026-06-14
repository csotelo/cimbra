import api from "./index";

export const jobsApi = {
    list(params = {}) {
        return api.get("/api/jobs/", { params });
    },
    get(taskId) {
        return api.get(`/api/jobs/${taskId}/`);
    },
    delete(taskId) {
        return api.delete(`/api/jobs/${taskId}/`);
    },
};
