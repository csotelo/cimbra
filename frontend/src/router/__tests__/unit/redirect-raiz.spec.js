/**
 * US11 — Redirección de URL raíz según estado de sesión
 * Unit tests: verifican la configuración de la ruta "/" en el router.
 *
 * Estado esperado al correr: RED (FAILED)
 * Razón: la ruta "/" tiene component: Home.vue, no tiene redirect.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("US11 — configuración de la ruta raíz (unit)", () => {
    beforeEach(() => {
        vi.resetModules();
    });

    it("la ruta '/' define redirect en lugar de component", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                user: null,
                fetchProfile: vi.fn().mockRejectedValue(new Error("401")),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");
        const rootRoute = router.options.routes.find((r) => r.path === "/");

        // FALLA: actualmente "/" tiene component: Home.vue, no redirect
        expect(rootRoute.redirect).toBeDefined();
        expect(rootRoute.component).toBeUndefined();
    });

    it("redirect de '/' retorna { name: 'dashboard' } cuando hay sesión activa", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                user: { email: "user@test.com", id: 1 },
                fetchProfile: vi.fn(),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");
        const rootRoute = router.options.routes.find((r) => r.path === "/");

        // FALLA: redirect no está definido; rootRoute tiene component en su lugar
        expect(typeof rootRoute.redirect).toBe("function");
        const result = await rootRoute.redirect();
        expect(result).toEqual({ name: "dashboard" });
    });

    it("redirect de '/' retorna { name: 'login' } cuando no hay sesión", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                user: null,
                fetchProfile: vi.fn().mockRejectedValue(new Error("Unauthorized")),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");
        const rootRoute = router.options.routes.find((r) => r.path === "/");

        // FALLA: redirect no está definido; rootRoute tiene component en su lugar
        expect(typeof rootRoute.redirect).toBe("function");
        const result = await rootRoute.redirect();
        expect(result).toEqual({ name: "login" });
    });
});
