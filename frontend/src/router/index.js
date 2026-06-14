import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import AppLayout from "@/layouts/AppLayout.vue";

const routes = [
    {
        path: "/",
        name: "home",
        redirect: () => {
            const authStore = useAuthStore();
            return authStore.user ? { name: "dashboard" } : { name: "login" };
        },
    },
    {
        path: "/login",
        name: "login",
        component: () => import("@/views/auth/Login.vue"),
        meta: { guest: true },
    },
    {
        path: "/register",
        name: "register",
        component: () => import("@/views/auth/Register.vue"),
        meta: { guest: true },
    },
    {
        path: "/verify-email",
        name: "verify-email",
        component: () => import("@/views/auth/VerifyEmail.vue"),
    },
    {
        path: "/forgot-password",
        name: "forgot-password",
        component: () => import("@/views/auth/ForgotPassword.vue"),
        meta: { guest: true },
    },
    {
        path: "/reset-password",
        name: "reset-password",
        component: () => import("@/views/auth/ResetPassword.vue"),
        meta: { guest: true },
    },
    {
        path: "/invitations/:token/accept",
        name: "invitation-accept",
        component: () => import("@/views/auth/AcceptInvitation.vue"),
    },
    {
        path: "/",
        component: AppLayout,
        meta: { requiresAuth: true },
        children: [
            {
                path: "dashboard",
                name: "dashboard",
                component: () => import("@/views/Dashboard.vue"),
            },
            {
                path: "profile",
                name: "profile",
                component: () => import("@/views/Profile.vue"),
            },
            {
                path: "tenants",
                name: "tenant-list",
                component: () => import("@/views/tenants/TenantList.vue"),
            },
            {
                path: "jobs",
                name: "job-list",
                component: () => import("@/views/JobList.vue"),
            },
            {
                path: "watchdog",
                name: "watchdog",
                component: () => import("@/views/Watchdog.vue"),
                meta: { requiresAdmin: true },
            },
            {
                path: "tenants/:id",
                name: "tenant-detail",
                component: () => import("@/views/tenants/TenantDetail.vue"),
            },
            {
                path: "tenants/:id/settings",
                name: "tenant-settings",
                component: () => import("@/views/tenants/TenantSettings.vue"),
            },
        ],
    },
];

// Auto-discover Vigilo module routes from src/modules/*/routes.js
const moduleFiles = import.meta.glob('../modules/*/routes.js', { eager: true })
const moduleRoutes = Object.values(moduleFiles).flatMap(m => m.default || [])
const appRoute = routes.find(r => r.children)
if (appRoute) appRoute.children.push(...moduleRoutes)

const router = createRouter({
    history: createWebHistory(),
    routes,
});

router._authCheckPromise = null;

async function checkAuth() {
    const authStore = useAuthStore();
    if (authStore.user) return true;
    if (router._authCheckPromise) return router._authCheckPromise;
    router._authCheckPromise = (async () => {
        if (authStore.user) return true;
        try {
            await authStore.fetchProfile();
            return !!authStore.user;
        } catch {
            return false;
        }
    })();
    return router._authCheckPromise;
}

router.beforeEach(async (to, from, next) => {
    const requiresAuth = to.matched.some(r => r.meta.requiresAuth)
    const requiresAdmin = to.matched.some(r => r.meta.requiresAdmin)
    const isGuest = to.matched.some(r => r.meta.guest)

    if (requiresAuth || requiresAdmin) {
        const authenticated = await checkAuth();
        if (!authenticated) {
            router._authCheckPromise = null;
            return next({ name: "login" });
        }
        if (requiresAdmin) {
            const authStore = useAuthStore();
            if (!authStore.user?.is_superuser) {
                return next({ name: "dashboard" });
            }
        }
    } else if (isGuest) {
        const authStore = useAuthStore();
        if (authStore.user) {
            return next({ name: "dashboard" });
        }
    }
    next();
});

export default router;
