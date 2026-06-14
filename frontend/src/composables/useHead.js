/**
 * Composable para gestión de <head>: title, meta tags, favicon y CSS var de skin.
 * Se usa en AppLayout (páginas autenticadas) y AuthLayout ya tiene datos mínimos.
 */
import { onUnmounted, watch } from "vue";
import { useRoute } from "vue-router";
import { useConfigStore } from "@/stores/config";

const ROUTE_TITLES = {
    dashboard: "Dashboard",
    "station-map": "Mapa de Alertas",
    "storm-alerts": "Alertas de Tormenta",
    stations: "Estaciones",
    "telegram-subscriptions": "Suscripciones Telegram",
    profile: "Mi Perfil",
    "job-list": "Trabajos",
    watchdog: "Watchdog",
    "tenant-list": "Tenants",
    "tenant-detail": "Detalle Tenant",
    "tenant-settings": "Configuración Tenant",
    "site-settings": "Configuración del Sitio",
    "user-management": "Gestión de Usuarios",
};

function setMeta(nameOrProp, content, attr = "name") {
    if (!content) return;
    let el = document.querySelector(`meta[${attr}="${nameOrProp}"]`);
    if (!el) {
        el = document.createElement("meta");
        el.setAttribute(attr, nameOrProp);
        document.head.appendChild(el);
    }
    el.setAttribute("content", content);
}

function setFavicon(url) {
    if (!url) return;
    let link = document.querySelector("link[rel~='icon']");
    if (!link) {
        link = document.createElement("link");
        link.rel = "icon";
        document.head.appendChild(link);
    }
    link.href = url;
}

export function useHead() {
    const route = useRoute();
    const config = useConfigStore();

    function update() {
        const site = config.siteName || "Ximbra";
        const desc = config.siteDescription || "";
        const routeTitle = ROUTE_TITLES[route.name] || "";
        const pageTitle = routeTitle ? `${routeTitle} — ${site}` : site;

        document.title = pageTitle;

        setMeta("description", desc);
        setMeta("og:title", pageTitle, "property");
        setMeta("og:description", desc, "property");
        if (config.ogImageUrl) setMeta("og:image", config.ogImageUrl, "property");

        setFavicon(config.faviconUrl);

        // Skin: CSS variable para color primario
        if (config.primaryColor) {
            document.documentElement.style.setProperty("--color-primary", config.primaryColor);
        }
    }

    const stopRoute = watch(() => route.name, update);
    const stopConfig = watch(() => config.loaded, update);

    update();

    onUnmounted(() => {
        stopRoute();
        stopConfig();
    });

    return { update };
}
