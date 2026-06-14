/**
 * US12 — Logout completo desde el frontend
 * Unit tests: verifican que useAuthStore.logout() resetea el caché de autenticación.
 *
 * Estado esperado al correr: RED (FAILED)
 * Razón: logout() no asigna router._authCheckPromise = null, por lo que el guard
 * del router sigue usando el caché previo (Promise resuelto como true) y redirige
 * al usuario a /dashboard en lugar de dejarlo llegar a /login.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createPinia, setActivePinia } from "pinia";

describe("US12 — useAuthStore.logout() resetea el caché del router (unit)", () => {
    beforeEach(() => {
        vi.resetModules();
        setActivePinia(createPinia());
    });

    it("logout() asigna null a router._authCheckPromise para invalidar el caché", async () => {
        const cachedPromise = Promise.resolve(true);
        const mockRouter = {
            push: vi.fn().mockResolvedValue(undefined),
            _authCheckPromise: cachedPromise,
        };

        vi.doMock("@/router", () => ({ default: mockRouter }));
        vi.doMock("@/api/auth", () => ({
            authApi: { logout: vi.fn().mockResolvedValue({}) },
        }));
        vi.doMock("@/api", () => ({ default: {} }));

        const { useAuthStore } = await import("@/stores/auth");
        const store = useAuthStore();
        store.user = { id: 1, email: "user@test.com" };
        store.tenants = [{ id: 10, name: "Acme" }];
        store.currentTenant = { id: 10, name: "Acme" };

        await store.logout();

        // FALLA: logout() no resetea router._authCheckPromise.
        // El caché sigue apuntando a la promesa anterior (authenticated = true),
        // lo que hace que el beforeEach guard redirija al dashboard.
        expect(mockRouter._authCheckPromise).toBeNull();
    });
});
