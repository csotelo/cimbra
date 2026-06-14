/**
 * US12 — Logout completo desde el frontend
 * Integration tests: verifican el comportamiento de navegación tras el logout.
 *
 * Estado esperado al correr: RED (FAILED)
 * Razón: authCheckPromise (variable de módulo en router/index.js) queda cacheado
 * como Promise(true) tras el primer acceso autenticado. Cuando el usuario hace
 * logout (user = null) y el guard vuelve a llamar checkAuth(), recibe el caché
 * en lugar de re-evaluar el estado real — permitiendo acceso a rutas protegidas
 * y redirigiendo fuera de /login hacia /dashboard.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("US12 — redirección post-logout (integration)", () => {
    beforeEach(() => {
        vi.resetModules();
    });

    it("navegar a /dashboard tras logout redirige al login", async () => {
        let userState = { id: 1, email: "user@test.com" };
        const mockFetchProfile = vi.fn().mockImplementation(() => {
            if (userState) return Promise.resolve();
            return Promise.reject(new Error("Unauthorized"));
        });

        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                get user() { return userState; },
                fetchProfile: mockFetchProfile,
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        // Primer acceso autenticado — pobla el caché (authCheckPromise = Promise(true))
        await router.push("/dashboard");
        await router.isReady();
        expect(router.currentRoute.value.name).toBe("dashboard");

        // Simular estado post-logout: user limpiado, caché del router NO reseteado
        userState = null;

        await router.push("/dashboard");
        await router.isReady();

        // FALLA: el guard usa authCheckPromise cacheado como true, permite el acceso
        expect(router.currentRoute.value.name).toBe("login");
        expect(router.currentRoute.value.path).toBe("/login");
    });

    it("navegar a /login tras logout no redirige al dashboard", async () => {
        let userState = { id: 1, email: "user@test.com" };
        const mockFetchProfile = vi.fn().mockImplementation(() => {
            if (userState) return Promise.resolve();
            return Promise.reject(new Error("Unauthorized"));
        });

        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                get user() { return userState; },
                fetchProfile: mockFetchProfile,
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        // Primer acceso autenticado — pobla el caché
        await router.push("/dashboard");
        await router.isReady();

        // Simular logout
        userState = null;

        // Intentar acceder a /login después del logout
        await router.push("/login");
        await router.isReady();

        // FALLA: el guard de meta:guest ve el caché como true y redirige a /dashboard
        expect(router.currentRoute.value.name).toBe("login");
        expect(router.currentRoute.value.path).toBe("/login");
    });

    it("navegar a /profile tras logout con rol owner redirige al login", async () => {
        let userState = { id: 2, email: "owner@test.com", role: "owner" };
        const mockFetchProfile = vi.fn().mockImplementation(() => {
            if (userState) return Promise.resolve();
            return Promise.reject(new Error("Unauthorized"));
        });

        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                get user() { return userState; },
                fetchProfile: mockFetchProfile,
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        await router.push("/profile");
        await router.isReady();
        expect(router.currentRoute.value.name).toBe("profile");

        userState = null;

        await router.push("/profile");
        await router.isReady();

        // FALLA: criterio 3 — el comportamiento debe aplicar a owner
        expect(router.currentRoute.value.name).toBe("login");
        expect(router.currentRoute.value.path).toBe("/login");
    });

    it("navegar a /tenants/:id tras logout con rol admin redirige al login", async () => {
        let userState = { id: 3, email: "admin@test.com", role: "admin" };
        const mockFetchProfile = vi.fn().mockImplementation(() => {
            if (userState) return Promise.resolve();
            return Promise.reject(new Error("Unauthorized"));
        });

        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                get user() { return userState; },
                fetchProfile: mockFetchProfile,
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        await router.push("/tenants/5");
        await router.isReady();
        expect(router.currentRoute.value.name).toBe("tenant-detail");

        userState = null;

        await router.push("/tenants/5");
        await router.isReady();

        // FALLA: criterio 3 — el comportamiento debe aplicar a admin
        expect(router.currentRoute.value.name).toBe("login");
        expect(router.currentRoute.value.path).toBe("/login");
    });

    it("navegar a /tenants/:id/settings tras logout con rol member redirige al login", async () => {
        let userState = { id: 4, email: "member@test.com", role: "member" };
        const mockFetchProfile = vi.fn().mockImplementation(() => {
            if (userState) return Promise.resolve();
            return Promise.reject(new Error("Unauthorized"));
        });

        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                get user() { return userState; },
                fetchProfile: mockFetchProfile,
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        await router.push("/tenants/5/settings");
        await router.isReady();
        expect(router.currentRoute.value.name).toBe("tenant-settings");

        userState = null;

        await router.push("/tenants/5/settings");
        await router.isReady();

        // FALLA: criterio 3 — el comportamiento debe aplicar a member
        expect(router.currentRoute.value.name).toBe("login");
        expect(router.currentRoute.value.path).toBe("/login");
    });
});
