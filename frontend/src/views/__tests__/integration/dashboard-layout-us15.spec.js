/**
 * US15 — Layout base del dashboard con panel de navegación lateral
 * Integration tests: verifican que el router soporta la navegación lateral
 * y que el layout es accesible con autenticación activa.
 *
 * Estado esperado al correr: RED (FAILED)
 * Razón: el router actual no define rutas de secciones del menú lateral.
 * El developer debe agregar rutas como /dashboard/overview o equivalentes
 * que correspondan a los ítems del sidebar.
 *
 * CA01: /dashboard con sesión activa mantiene la ruta correcta (prerequisito del layout).
 * CA03: el router define al menos una ruta de sección del menú lateral
 *       que permite navegar desde el sidebar sin abandonar el layout del dashboard.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("US15 — navegación del layout del dashboard (integration)", () => {
    beforeEach(() => {
        vi.resetModules();
    });

    it("CA01: /dashboard con sesión activa no redirige y mantiene la ruta", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                get user() { return { id: 1, email: "admin@test.com" }; },
                fetchProfile: vi.fn().mockResolvedValue(undefined),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        await router.push("/dashboard");
        await router.isReady();

        expect(router.currentRoute.value.name).toBe("dashboard");
        expect(router.currentRoute.value.path).toBe("/dashboard");
    });

    it("CA03: el router define rutas navegables desde el sidebar del dashboard", async () => {
        // FALLA: el router actual no define rutas de secciones internas del dashboard
        // El developer debe agregar rutas accesibles desde los ítems del sidebar
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                get user() { return { id: 1, email: "admin@test.com" }; },
                fetchProfile: vi.fn().mockResolvedValue(undefined),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        const routes = router.options.routes;
        const dashboardChildRoutes = routes.filter(
            (r) => r.path.startsWith("/dashboard") && r.path !== "/dashboard",
        );

        // El sidebar debe tener al menos un enlace a una sección del dashboard
        expect(
            dashboardChildRoutes.length,
            "El router debe definir al menos una ruta de sección interna del dashboard (ej: /dashboard/overview)",
        ).toBeGreaterThan(0);
    });

    it("CA03: navegar entre secciones del sidebar mantiene el layout activo", async () => {
        // FALLA: no existen rutas de secciones del sidebar para navegar
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                get user() { return { id: 1, email: "admin@test.com" }; },
                fetchProfile: vi.fn().mockResolvedValue(undefined),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        const routes = router.options.routes;
        const sidebarRoute = routes.find(
            (r) => r.path.startsWith("/dashboard") && r.path !== "/dashboard",
        );

        // FALLA si no existe ninguna ruta de sección del sidebar
        expect(
            sidebarRoute,
            "Debe existir al menos una ruta de sección del dashboard para el sidebar",
        ).toBeDefined();

        await router.push(sidebarRoute.path);
        await router.isReady();

        // Después de navegar a una sección, la ruta activa pertenece al dashboard
        expect(
            router.currentRoute.value.path,
            "La navegación del sidebar debe mantenerse dentro del dominio /dashboard",
        ).toMatch(/^\/dashboard/);
    });
});
