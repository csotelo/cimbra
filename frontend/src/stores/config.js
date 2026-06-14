import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "@/api/index";

export const useConfigStore = defineStore("config", () => {
    const singleTenantMode = ref(true);
    const mainTenantSlug = ref("ximbra");
    const allowSelfRegistration = ref(true);
    // SEO + skin
    const siteName = ref("Ximbra");
    const siteDescription = ref("");
    const ogImageUrl = ref("");
    const faviconUrl = ref("");
    const allowIndexing = ref(false);
    const primaryColor = ref("#4f46e5");
    const loaded = ref(false);

    // alias para compatibilidad con código anterior
    const appName = siteName;

    async function fetchConfig() {
        if (loaded.value) return;
        try {
            const { data } = await api.get("/api/config/");
            singleTenantMode.value = data.single_tenant_mode ?? true;
            mainTenantSlug.value = data.main_tenant_slug ?? "ximbra";
            allowSelfRegistration.value = data.allow_self_registration ?? true;
            siteName.value = data.site_name || data.app_name || "Ximbra";
            siteDescription.value = data.site_description || "";
            ogImageUrl.value = data.og_image_url || "";
            faviconUrl.value = data.favicon_url || "";
            allowIndexing.value = data.allow_indexing ?? false;
            primaryColor.value = data.primary_color || "#4f46e5";
        } catch {
            // keep defaults
        } finally {
            loaded.value = true;
        }
    }

    function reset() {
        loaded.value = false;
    }

    return {
        singleTenantMode, mainTenantSlug, allowSelfRegistration,
        siteName, appName, siteDescription, ogImageUrl, faviconUrl,
        allowIndexing, primaryColor, loaded,
        fetchConfig, reset,
    };
});
