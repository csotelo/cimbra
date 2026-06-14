/**
 * US14 — Usuario sin tenant puede iniciar sesión en el frontend
 * Unit tests: verifican el comportamiento de useAuthStore.login() sin tenants.
 *
 * Estado esperado al correr: RED (FAILED) para el test de acoplamiento con router.
 * Razón: login() actualmente modifica router._authCheckPromise = null (acoplamiento
 * con internals del router). Tras el fix, este bloque debe eliminarse: el fast-path
 * en checkAuth() hace que el reset sea redundante y el acoplamiento innecesario.
 *
 * Los tests de tenant_list vacío pueden pasar (comportamiento existente) — se
 * incluyen como baseline de regresión, marcados como `unverified` en story.md.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createPinia, setActivePinia } from "pinia";

describe("US14 — useAuthStore.login() con tenant_list vacío (unit)", () => {
    beforeEach(() => {
        vi.resetModules();
        setActivePinia(createPinia());
    });

    it("setea tenants como array vacío cuando tenant_list es []", async () => {
        const mockRouter = {
            push: vi.fn().mockResolvedValue(undefined),
            _authCheckPromise: null,
        };

        vi.doMock("@/router", () => ({ default: mockRouter }));
        vi.doMock("@/api/auth", () => ({
            authApi: {
                login: vi.fn().mockResolvedValue({ data: { tenant_list: [] } }),
                getProfile: vi.fn().mockResolvedValue({ data: { id: 1, email: "user@test.com" } }),
            },
        }));
        vi.doMock("@/api", () => ({ default: {} }));

        const { useAuthStore } = await import("@/stores/auth");
        const store = useAuthStore();

        await store.login("user@test.com", "Secret123!");

        // Comportamiento existente — baseline de regresión (puede pasar)
        expect(store.tenants).toEqual([]);
    });

    it("no llama a selectTenant cuando tenant_list es []", async () => {
        const mockSelectTenant = vi.fn().mockResolvedValue(undefined);
        const mockRouter = {
            push: vi.fn().mockResolvedValue(undefined),
            _authCheckPromise: null,
        };

        vi.doMock("@/router", () => ({ default: mockRouter }));
        vi.doMock("@/api/auth", () => ({
            authApi: {
                login: vi.fn().mockResolvedValue({ data: { tenant_list: [] } }),
                getProfile: vi.fn().mockResolvedValue({ data: { id: 1, email: "user@test.com" } }),
                selectTenant: mockSelectTenant,
            },
        }));
        vi.doMock("@/api", () => ({ default: {} }));

        const { useAuthStore } = await import("@/stores/auth");
        const store = useAuthStore();

        await store.login("user@test.com", "Secret123!");

        // Comportamiento existente — baseline de regresión (puede pasar)
        expect(mockSelectTenant).not.toHaveBeenCalled();
    });

    it("no debe modificar router._authCheckPromise al hacer login", async () => {
        // El fast-path en checkAuth() hace que el reset del cache desde el store
        // sea innecesario. login() no debe acoplarse a internals del router.
        const stalePromise = Promise.resolve(false);
        const mockRouter = {
            push: vi.fn().mockResolvedValue(undefined),
            _authCheckPromise: stalePromise,
        };

        vi.doMock("@/router", () => ({ default: mockRouter }));
        vi.doMock("@/api/auth", () => ({
            authApi: {
                login: vi.fn().mockResolvedValue({ data: { tenant_list: [] } }),
                getProfile: vi.fn().mockResolvedValue({ data: { id: 1, email: "user@test.com" } }),
            },
        }));
        vi.doMock("@/api", () => ({ default: {} }));

        const { useAuthStore } = await import("@/stores/auth");
        const store = useAuthStore();

        await store.login("user@test.com", "Secret123!");

        // FALLA: login() actualmente ejecuta `router._authCheckPromise = null`
        // Con el fix (eliminar el bloque de reset): el valor original se mantiene
        expect(mockRouter._authCheckPromise).toBe(stalePromise);
    });

    it("retorna true tras login exitoso sin tenants", async () => {
        const mockRouter = {
            push: vi.fn().mockResolvedValue(undefined),
            _authCheckPromise: null,
        };

        vi.doMock("@/router", () => ({ default: mockRouter }));
        vi.doMock("@/api/auth", () => ({
            authApi: {
                login: vi.fn().mockResolvedValue({ data: { tenant_list: [] } }),
                getProfile: vi.fn().mockResolvedValue({ data: { id: 1, email: "user@test.com" } }),
            },
        }));
        vi.doMock("@/api", () => ({ default: {} }));

        const { useAuthStore } = await import("@/stores/auth");
        const store = useAuthStore();

        const result = await store.login("user@test.com", "Secret123!");

        // Comportamiento existente — baseline de regresión (puede pasar)
        expect(result).toBe(true);
        expect(store.user).toEqual({ id: 1, email: "user@test.com" });
    });
});
