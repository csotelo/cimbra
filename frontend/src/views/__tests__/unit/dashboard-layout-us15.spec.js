/**
 * US15 — Layout base del dashboard con panel de navegación lateral
 * Unit tests: análisis estático de la estructura del componente Dashboard.vue.
 *
 * Estado esperado al correr: RED (FAILED)
 * Razón: Dashboard.vue actual tiene un <nav> horizontal y un <main> sin las clases
 * "sidebar" ni "main-content". La estructura de layout lateral no existe aún.
 *
 * CA01: el panel izquierdo tiene la clase CSS "sidebar".
 * CA02: el área de contenido tiene la clase CSS "main-content"
 *       y no existe ningún elemento con clase "tenant-access-button".
 * CA03: sidebar y main-content son hermanos directos en un contenedor flex,
 *       garantizando que el layout persiste en cualquier contexto de navegación.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { resolve } from "path";

const SRC = resolve(__dirname, "../../../");

describe("US15 — layout base del dashboard (unit)", () => {
    it("CA01: Dashboard.vue — existe un panel izquierdo con clase CSS 'sidebar'", () => {
        // FALLA: Dashboard.vue no tiene ningún elemento con clase "sidebar"
        const source = readFileSync(resolve(SRC, "views/Dashboard.vue"), "utf-8");
        expect(
            source,
            "Dashboard.vue debe contener un elemento con class='sidebar' (o que la incluya)",
        ).toMatch(/class="[^"]*\bsidebar\b[^"]*"/);
    });

    it("CA01: Dashboard.vue — el sidebar es un elemento lateral, no un <nav> horizontal", () => {
        // FALLA: el nav actual es horizontal (top bar), no un panel lateral
        const source = readFileSync(resolve(SRC, "views/Dashboard.vue"), "utf-8");
        expect(
            source,
            "Dashboard.vue debe tener un elemento aside o div con clase 'sidebar'",
        ).toMatch(/<(aside|div)[^>]*class="[^"]*\bsidebar\b[^"]*"/);
    });

    it("CA02: Dashboard.vue — existe un área de contenido con clase CSS 'main-content'", () => {
        // FALLA: el <main> actual no tiene la clase "main-content"
        const source = readFileSync(resolve(SRC, "views/Dashboard.vue"), "utf-8");
        expect(
            source,
            "Dashboard.vue debe tener un elemento con class='main-content' (o que la incluya)",
        ).toMatch(/class="[^"]*\bmain-content\b[^"]*"/);
    });

    it("CA02: Dashboard.vue — no existe ningún elemento con clase 'tenant-access-button'", () => {
        // FALLA si el botón de acceso al tenant sigue siendo el elemento principal
        const source = readFileSync(resolve(SRC, "views/Dashboard.vue"), "utf-8");
        expect(
            source,
            "Dashboard.vue no debe contener la clase 'tenant-access-button'",
        ).not.toContain("tenant-access-button");
    });

    it("CA03: Dashboard.vue — existe un contenedor raíz con layout flex que aloja sidebar y main-content", () => {
        // FALLA: la estructura actual tiene flex en elementos internos pero no un contenedor
        // de layout principal que use flex para alinear sidebar + main-content como hermanos.
        // El developer debe crear un div con clase que combine "flex" y contenga ambos paneles.
        const source = readFileSync(resolve(SRC, "views/Dashboard.vue"), "utf-8");
        expect(
            source,
            "Dashboard.vue debe tener un contenedor de layout con 'flex' que contenga sidebar y main-content como hermanos directos",
        ).toMatch(/class="[^"]*\bflex\b[^"]*"[\s\S]*sidebar[\s\S]*main-content/);
    });
});
