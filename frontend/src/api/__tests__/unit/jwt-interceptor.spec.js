/**
 * US07 — Frontend Vue.js SPA
 * Unit tests: interceptor JWT de Axios — CA04
 *
 * Estado esperado al correr: RED (FAILED)
 * Razón: las aserciones sobre el comportamiento del interceptor fallan porque
 * axios-mock-adapter no está instalado y el api.interceptors.response.handlers
 * es null en Axios ≥ 1.x (los handlers se almacenan distinto al acceso directo).
 *
 * Para hacer GREEN:
 *   1. npm install -D axios-mock-adapter
 *   2. Refactorizar los tests usando MockAdapter en lugar de acceso directo
 *      a interceptors.response.handlers.
 *
 * CA04: JWT auto-refresh — el interceptor en src/api/index.js debe:
 *   - Llamar POST /api/users/refresh/ cuando cualquier endpoint retorna 401.
 *   - Reintentar el request original después de un refresh exitoso.
 *   - Redirigir a /login cuando el refresh también falla.
 *   - Encolar requests concurrentes (solo 1 refresh aunque haya N peticiones).
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("US07 — CA04: interceptor JWT auto-refresh (api/index.js)", () => {
    beforeEach(() => {
        vi.resetModules();
    });

    it("api tiene al menos un interceptor de respuesta registrado", async () => {
        vi.doMock("@/router", () => ({ default: { push: vi.fn() } }));

        const { default: api } = await import("@/api");

        // Verifica que se registró al menos un response interceptor.
        // En Axios ≥ 1.x, handlers puede ser null para slots libres;
        // filter(Boolean) elimina los slots vacíos.
        const activeHandlers = api.interceptors.response.handlers?.filter(Boolean) ?? [];

        // RED: si axios-mock-adapter no está instalado, la integración completa
        // (401 → refresh → retry) no puede ser testada. Este test sólo verifica
        // que el interceptor existe; las aserciones de comportamiento están abajo.
        expect(
            activeHandlers.length,
            "src/api/index.js debe registrar al menos 1 response interceptor",
        ).toBeGreaterThan(0);
    });

    it("interceptor llama POST /api/users/refresh/ cuando un endpoint retorna 401", async () => {
        vi.doMock("@/router", () => ({ default: { push: vi.fn() } }));

        const { default: api } = await import("@/api");

        const postSpy = vi.spyOn(api, "post").mockResolvedValue({ data: {} });
        const requestSpy = vi.spyOn(api, "request").mockResolvedValue({ data: { retried: true } });

        const errorHandler = api.interceptors.response.handlers?.filter(Boolean)?.[0]?.rejected;

        expect(errorHandler, "Debe existir un rejected handler en el interceptor").toBeDefined();

        const fakeError = {
            response: { status: 401 },
            config: { _retry: false, method: "get", url: "/api/users/me/" },
        };

        await errorHandler(fakeError);

        // RED: la llamada a refresh debe haberse realizado
        expect(postSpy).toHaveBeenCalledWith("/api/users/refresh/");
    });

    it("interceptor retoca el request original después de un refresh exitoso", async () => {
        vi.doMock("@/router", () => ({ default: { push: vi.fn() } }));

        const { default: api } = await import("@/api");

        vi.spyOn(api, "post").mockResolvedValue({ data: {} });
        const requestSpy = vi.spyOn(api, "request").mockResolvedValue({ data: { retried: true } });

        const errorHandler = api.interceptors.response.handlers?.filter(Boolean)?.[0]?.rejected;

        expect(errorHandler, "Debe existir un rejected handler en el interceptor").toBeDefined();

        const fakeError = {
            response: { status: 401 },
            config: { _retry: false, method: "get", url: "/api/users/me/" },
        };

        const result = await errorHandler(fakeError);

        // RED: el interceptor debe reintentar y devolver la respuesta del retry
        expect(result).toEqual({ data: { retried: true } });
        expect(requestSpy).toHaveBeenCalled();
    });

    it("interceptor redirige a /login cuando el refresh también falla", async () => {
        const pushSpy = vi.fn();
        vi.doMock("@/router", () => ({ default: { push: pushSpy } }));

        const { default: api } = await import("@/api");

        vi.spyOn(api, "post").mockRejectedValue({ response: { status: 401 } });

        const errorHandler = api.interceptors.response.handlers?.filter(Boolean)?.[0]?.rejected;

        expect(errorHandler, "Debe existir un rejected handler en el interceptor").toBeDefined();

        const fakeError = {
            response: { status: 401 },
            config: { _retry: false, method: "get", url: "/api/users/me/" },
        };

        await errorHandler(fakeError).catch(() => {});

        // RED: tras un refresh fallido, debe redirigir al login
        expect(pushSpy).toHaveBeenCalledWith("/login");
    });
});
