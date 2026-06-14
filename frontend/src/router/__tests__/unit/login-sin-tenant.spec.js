/**
 * US14 — Usuario sin tenant puede iniciar sesión en el frontend
 * Unit tests: verifican el comportamiento de checkAuth() ante cache stale.
 *
 * Estado esperado al correr: RED (FAILED)
 * Razón: checkAuth() no tiene fast-path que verifique authStore.user ANTES de
 * consultar router._authCheckPromise. Si el cache está resuelto como false pero
 * el usuario ya está autenticado en el store, el guard redirige incorrectamente
 * al login en lugar de permitir la navegación a la ruta protegida.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("US14 — checkAuth() fast-path con cache stale (unit)", () => {
    beforeEach(() => {
        vi.resetModules();
    });

    it("fast-path no modifica router._authCheckPromise cuando user está seteado", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                user: { id: 1, email: "user@test.com" },
                fetchProfile: vi.fn(),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        const stalePromise = Promise.resolve(false);
        router._authCheckPromise = stalePromise;

        await router.push("/dashboard");
        await router.isReady();

        // FALLA: sin fast-path, checkAuth() usa el cache stale → redirect loop →
        // el guard de /login crea una nueva promesa y reemplaza router._authCheckPromise
        // Con el fix (fast-path): retorna true antes de leer el cache →
        // router._authCheckPromise permanece intacto (stalePromise sin modificar)
        expect(router._authCheckPromise).toBe(stalePromise);
    });

    it("permite navegar a /profile cuando user está seteado aunque el cache diga false", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                user: { id: 1, email: "user@test.com" },
                fetchProfile: vi.fn(),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        router._authCheckPromise = Promise.resolve(false);

        await router.push("/profile");
        await router.isReady();

        // FALLA: mismo problema, aplica a cualquier ruta con requiresAuth
        expect(router.currentRoute.value.name).toBe("profile");
        expect(router.currentRoute.value.path).toBe("/profile");
    });

    it("redirige a /login cuando user es null y fetchProfile falla (caso base correcto)", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                user: null,
                fetchProfile: vi.fn().mockRejectedValue(new Error("401")),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        await router.push("/dashboard");
        await router.isReady();

        // Este comportamiento ya es correcto — sirve como baseline de regresión
        expect(router.currentRoute.value.name).toBe("login");
    });
});
