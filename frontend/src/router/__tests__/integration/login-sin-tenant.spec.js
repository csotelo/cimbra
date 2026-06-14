/**
 * US14 — Usuario sin tenant puede iniciar sesión en el frontend
 * Integration tests: verifican la secuencia completa de login sin tenants.
 *
 * Estado esperado al correr: RED (FAILED)
 * Razón: la secuencia exacta del bug — visitar /login crea un cache
 * router._authCheckPromise = Promise<false>; tras el login exitoso el user
 * queda seteado pero el guard sigue usando el cache stale al navegar a /dashboard,
 * lo que produce un redirect loop. El fix requiere el fast-path en checkAuth().
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("US14 — login sin tenants no produce redirect loop (integration)", () => {
    beforeEach(() => {
        vi.resetModules();
    });

    it("login sin tenants navega a /dashboard sin redirect loop", async () => {
        // Simula estado dinámico: empieza sin sesión, luego el login la establece
        let userState = null;
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

        // Paso 1: usuario visita /login (no autenticado)
        // El guard crea router._authCheckPromise = Promise<false> como cache stale
        await router.push("/login");
        await router.isReady();
        expect(router.currentRoute.value.name).toBe("login");

        // Paso 2: login exitoso — user queda seteado, NO se resetea el cache manualmente
        // (así se prueba que el fix no depende del reset del store)
        userState = { id: 1, email: "user@test.com" };

        // Paso 3: navegación al dashboard tras login
        await router.push("/dashboard");
        await router.isReady();

        // FALLA: el guard lee el cache stale Promise<false> → redirige a /login
        // Con el fix (fast-path): user está seteado → retorna true → llega a /dashboard
        expect(router.currentRoute.value.name).toBe("dashboard");
        expect(router.currentRoute.value.path).toBe("/dashboard");
    });

    it("login sin tenants permite acceder a /profile sin bloqueo", async () => {
        let userState = null;
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

        // Crear cache stale visitando /login primero
        await router.push("/login");
        await router.isReady();

        // Simular login exitoso
        userState = { id: 1, email: "user@test.com" };

        // Navegar a /profile — criterio 3: no debe bloquear acceso por ausencia de tenants
        await router.push("/profile");
        await router.isReady();

        // FALLA: mismo bug del cache stale aplica a todas las rutas requiresAuth
        expect(router.currentRoute.value.name).toBe("profile");
        expect(router.currentRoute.value.path).toBe("/profile");
    });

    it("login con tenants sigue navegando a /dashboard sin regresión", async () => {
        let userState = null;
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

        await router.push("/login");
        await router.isReady();

        // Usuario CON tenants — el bug también afecta este caso
        userState = { id: 2, email: "owner@test.com", tenants: [{ id: 10, name: "Acme" }] };

        await router.push("/dashboard");
        await router.isReady();

        // FALLA: el cache stale también afecta usuarios con tenants (el fix debe mantener regresión)
        expect(router.currentRoute.value.name).toBe("dashboard");
        expect(router.currentRoute.value.path).toBe("/dashboard");
    });

    it("guard de ruta guest /login no redirige al dashboard durante el login", async () => {
        // Durante el proceso de login, el usuario está en /login (guest route).
        // El guard guest llama checkAuth() — si user está seteado, redirige a /dashboard.
        // Este test verifica que el guard guest funciona correctamente con el fast-path.
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                user: null,
                fetchProfile: vi.fn().mockRejectedValue(new Error("Unauthorized")),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        // Usuario no autenticado visita /login — debe quedarse en /login
        await router.push("/login");
        await router.isReady();

        // Baseline correcto — no debe fallar con el fix
        expect(router.currentRoute.value.name).toBe("login");
        expect(router.currentRoute.value.path).toBe("/login");
    });
});
