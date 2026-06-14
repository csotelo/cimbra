import api from "./index.js";

export const dashboardApi = {
    getWidgets: () => api.get("/api/dashboard/"),
    updateWidget: (widgetId, data) => api.post("/api/dashboard/", { widget_id: widgetId, ...data }),
};
