/**
 * US11 — Redirección de URL raíz según estado de sesión
 * Integration tests: verifican el comportamiento de navegación real al acceder a "/".
 *
 * Estado esperado al correr: RED (FAILED)
 * Razón: navegar a "/" renderiza Home.vue en lugar de redirigir.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("US11 — navegación a '/' (integration)", () => {
    beforeEach(() => {
        vi.resetModules();
    });

    it("navegar a '/' con sesión activa redirige a /dashboard", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                user: { email: "user@test.com", id: 1 },
                fetchProfile: vi.fn(),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        await router.push("/");
        await router.isReady();

        // FALLA: actualmente "/" renderiza Home.vue sin redirigir
        expect(router.currentRoute.value.name).toBe("dashboard");
        expect(router.currentRoute.value.path).toBe("/dashboard");
    });

    it("navegar a '/' sin sesión redirige a /login", async () => {
        vi.doMock("@/stores/auth", () => ({
            useAuthStore: vi.fn(() => ({
                user: null,
                fetchProfile: vi.fn().mockRejectedValue(new Error("Unauthorized")),
            })),
        }));
        vi.doMock("@/api", () => ({ default: {} }));
        vi.doMock("@/api/auth", () => ({ authApi: {} }));

        const { default: router } = await import("@/router/index.js");

        await router.push("/");
        await router.isReady();

        // FALLA: actualmente "/" renderiza Home.vue sin redirigir
        expect(router.currentRoute.value.name).toBe("login");
        expect(router.currentRoute.value.path).toBe("/login");
    });
});
