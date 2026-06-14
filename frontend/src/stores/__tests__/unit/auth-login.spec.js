/**
 * US07 — Frontend Vue.js SPA
 * Unit tests: authStore.login() — CA01 y CA02
 *
 * Estado esperado al correr: PASS (comportamiento ya existe).
 * Si pasan → criterios CA01/CA02 marcados como 'unverified' en story.md.
 *
 * CA01: login() retorna true y setea user con credenciales válidas.
 * CA01: login() retorna false y setea error con credenciales inválidas.
 * CA02: login() popula tenants y currentTenant desde la respuesta de la API.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createPinia, setActivePinia } from "pinia";

describe("US07 — authStore.login() — CA01/CA02", () => {
    beforeEach(() => {
        vi.resetModules();
        setActivePinia(createPinia());
    });

    it("CA01: login() retorna true y setea user con credenciales válidas", async () => {
        vi.doMock("@/api/auth", () => ({
            authApi: {
                login: vi.fn().mockResolvedValue({
                    data: { tenant_list: [{ id: 1, name: "Acme", slug: "acme" }] },
                }),
                selectTenant: vi.fn().mockResolvedValue({}),
                getProfile: vi.fn().mockResolvedValue({
                    data: { id: 1, email: "admin@example.com" },
                }),
            },
        }));
        vi.doMock("@/router", () => ({
            default: { push: vi.fn(), _authCheckPromise: null },
        }));
        vi.doMock("@/api", () => ({ default: {} }));

        const { useAuthStore } = await import("@/stores/auth");
        const store = useAuthStore();

        const result = await store.login("admin@example.com", "admin123");

        expect(result).toBe(true);
        expect(store.user).toEqual({ id: 1, email: "admin@example.com" });
        expect(store.loading).toBe(false);
        expect(store.error).toBeNull();
    });

    it("CA01: login() retorna false y setea error con credenciales inválidas", async () => {
        vi.doMock("@/api/auth", () => ({
            authApi: {
                login: vi.fn().mockRejectedValue({
                    response: { data: { detail: "Credenciales inválidas." } },
                }),
            },
        }));
        vi.doMock("@/router", () => ({
            default: { push: vi.fn(), _authCheckPromise: null },
        }));
        vi.doMock("@/api", () => ({ default: {} }));

        const { useAuthStore } = await import("@/stores/auth");
        const store = useAuthStore();

        const result = await store.login("admin@example.com", "wrong_password");

        expect(result).toBe(false);
        expect(store.error).toBe("Credenciales inválidas.");
        expect(store.user).toBeNull();
    });

    it("CA02: login() popula tenants desde tenant_list del response", async () => {
        vi.doMock("@/api/auth", () => ({
            authApi: {
                login: vi.fn().mockResolvedValue({
                    data: {
                        tenant_list: [
                            { id: 1, name: "Acme Corp", slug: "acme" },
                            { id: 2, name: "Beta Inc", slug: "beta" },
                        ],
                    },
                }),
                selectTenant: vi.fn().mockResolvedValue({}),
                getProfile: vi.fn().mockResolvedValue({
                    data: { id: 1, email: "admin@example.com" },
                }),
            },
        }));
        vi.doMock("@/router", () => ({
            default: { push: vi.fn(), _authCheckPromise: null },
        }));
        vi.doMock("@/api", () => ({ default: {} }));

        const { useAuthStore } = await import("@/stores/auth");
        const store = useAuthStore();

        await store.login("admin@example.com", "admin123");

        expect(store.tenants).toHaveLength(2);
        expect(store.tenants[0].name).toBe("Acme Corp");
        expect(store.tenants[1].slug).toBe("beta");
    });

    it("CA02: login() setea currentTenant al primer tenant del response", async () => {
        vi.doMock("@/api/auth", () => ({
            authApi: {
                login: vi.fn().mockResolvedValue({
                    data: {
                        tenant_list: [{ id: 5, name: "Principal", slug: "principal" }],
                    },
                }),
                selectTenant: vi.fn().mockResolvedValue({}),
                getProfile: vi.fn().mockResolvedValue({
                    data: { id: 1, email: "admin@example.com" },
                }),
            },
        }));
        vi.doMock("@/router", () => ({
            default: { push: vi.fn(), _authCheckPromise: null },
        }));
        vi.doMock("@/api", () => ({ default: {} }));

        const { useAuthStore } = await import("@/stores/auth");
        const store = useAuthStore();

        await store.login("admin@example.com", "admin123");

        expect(store.currentTenant).toEqual({ id: 5, name: "Principal", slug: "principal" });
    });
});
