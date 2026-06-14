/**
 * US07 — Frontend Vue.js SPA
 * Integration tests: guards del router — CA03 y CA04
 *
 * Estado esperado al correr: PASS (guards ya implementados).
 * Si pasan → criterios CA03/CA04 marcados como 'unverified' en story.md.
 *
 * CA03: Ruta protegida sin sesión redirige a /login.
 * CA04: JWT auto-refresh — /login con sesión redirige a /dashboard (meta: guest).
 *       /profile con sesión activa es accesible (no redirige).
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("US07 — guards del router — CA03/CA04", () => {
    beforeEach(() => {
        vi.resetModules();
    });

    it("CA03: /dashboard sin sesión redirige a /login", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                get user() { return null; },
                fetchProfile: vi.fn().mockRejectedValue(new Error("Unauthorized")),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        await router.push("/dashboard");
        await router.isReady();

        expect(router.currentRoute.value.name).toBe("login");
        expect(router.currentRoute.value.path).toBe("/login");
    });

    it("CA03: /profile sin sesión redirige a /login", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                get user() { return null; },
                fetchProfile: vi.fn().mockRejectedValue(new Error("Unauthorized")),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        await router.push("/profile");
        await router.isReady();

        expect(router.currentRoute.value.name).toBe("login");
        expect(router.currentRoute.value.path).toBe("/login");
    });

    it("CA04: /login con sesión activa redirige a /dashboard (meta: guest)", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                get user() { return { id: 1, email: "admin@example.com" }; },
                fetchProfile: vi.fn().mockResolvedValue(undefined),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        await router.push("/login");
        await router.isReady();

        expect(router.currentRoute.value.name).toBe("dashboard");
    });

    it("CA04: /profile con sesión activa es accesible y no redirige a /login", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                get user() { return { id: 1, email: "admin@example.com" }; },
                fetchProfile: vi.fn().mockResolvedValue(undefined),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        await router.push("/profile");
        await router.isReady();

        expect(router.currentRoute.value.name).toBe("profile");
        expect(router.currentRoute.value.path).toBe("/profile");
    });
});
