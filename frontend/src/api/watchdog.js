import api from "./index";

export const watchdogApi = {
    getHealth() {
        return api.get("/api/watchdog/health/");
    },
    dispatchInternalTask() {
        return api.post("/api/watchdog/internal/dispatch/");
    },
    sendCommand(action, payload = {}) {
        return api.post("/api/watchdog/command/", { action, payload });
    },
    getCommandResult(commandId) {
        return api.get(`/api/watchdog/command/${commandId}/`);
    },
    getSchedulableTasks() {
        return api.get("/api/watchdog/schedules/tasks/");
    },
    getSchedules() {
        return api.get("/api/watchdog/schedules/");
    },
    createSchedule(data) {
        return api.post("/api/watchdog/schedules/", data);
    },
    updateSchedule(id, data) {
        return api.patch(`/api/watchdog/schedules/${id}/`, data);
    },
    deleteSchedule(id) {
        return api.delete(`/api/watchdog/schedules/${id}/`);
    },
};
