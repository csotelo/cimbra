import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "@/api/index";

export const useConfigStore = defineStore("config", () => {
    const singleTenantMode = ref(true);
    const mainTenantSlug = ref("ximbra");
    const allowSelfRegistration = ref(true);
    const appName = ref("Ximbra");
    const loaded = ref(false);

    async function fetchConfig() {
        if (loaded.value) return;
        try {
            const response = await api.get("/api/config/");
            singleTenantMode.value = response.data.single_tenant_mode;
            mainTenantSlug.value = response.data.main_tenant_slug;
            allowSelfRegistration.value = response.data.allow_self_registration;
            appName.value = response.data.app_name;
        } catch {
            // keep defaults
        } finally {
            loaded.value = true;
        }
    }

    return { singleTenantMode, mainTenantSlug, allowSelfRegistration, appName, loaded, fetchConfig };
});
