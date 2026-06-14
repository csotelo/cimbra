/**
 * US07 — Frontend Vue.js SPA
 * Unit tests: texto en español de la interfaz — CA01, CA02, CA03, CA05
 *
 * Estado esperado al correr: RED (FAILED)
 * Razón: los componentes están en inglés ("Sign In", "Sign Out") pero los
 * criterios de aceptación esperan español ("Iniciar sesión", "Cerrar sesión").
 * El desarrollador debe actualizar el texto de Login.vue y Dashboard.vue.
 *
 * CA01/CA03: Login.vue — botón submit debe decir "Iniciar sesión".
 * CA05:      Dashboard.vue — botón de logout debe decir "Cerrar sesión".
 * CA02:      Dashboard.vue — debe existir un elemento con clase CSS "dashboard"
 *            para que el step "When I wait for '.dashboard'" encuentre el elemento.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { resolve } from "path";

const SRC = resolve(__dirname, "../../../");

describe("US07 — texto en español de la SPA — CA01/CA02/CA03/CA05", () => {
    it("CA01/CA03: Login.vue — el botón de submit dice 'Iniciar sesión'", () => {
        // FALLA: Login.vue actualmente usa "Sign In" en lugar de "Iniciar sesión"
        const source = readFileSync(resolve(SRC, "views/auth/Login.vue"), "utf-8");
        expect(source, "Login.vue debe contener 'Iniciar sesión' en el botón de submit").toContain(
            "Iniciar sesión",
        );
    });

    it("CA01: Login.vue — el estado de loading del botón dice 'Iniciando sesión...'", () => {
        // FALLA: actualmente dice "Signing in..." en lugar de "Iniciando sesión..."
        const source = readFileSync(resolve(SRC, "views/auth/Login.vue"), "utf-8");
        expect(
            source,
            "Login.vue debe mostrar 'Iniciando sesión...' durante el loading",
        ).toContain("Iniciando sesión...");
    });

    it("CA05: Dashboard.vue — el botón de logout dice 'Cerrar sesión'", () => {
        // FALLA: Dashboard.vue actualmente usa "Sign Out" en lugar de "Cerrar sesión"
        const source = readFileSync(resolve(SRC, "views/Dashboard.vue"), "utf-8");
        expect(
            source,
            "Dashboard.vue debe contener 'Cerrar sesión' en el botón de logout",
        ).toContain("Cerrar sesión");
    });

    it("CA02: Dashboard.vue — existe un elemento raíz con clase CSS 'dashboard'", () => {
        // FALLA: el div raíz de Dashboard.vue tiene "min-h-screen bg-gray-100"
        // pero no la clase "dashboard" que necesita el step "When I wait for '.dashboard'"
        const source = readFileSync(resolve(SRC, "views/Dashboard.vue"), "utf-8");
        expect(
            source,
            "Dashboard.vue debe tener un elemento con class='dashboard' (o que la incluya)",
        ).toMatch(/class="[^"]*\bdashboard\b[^"]*"/);
    });
});
