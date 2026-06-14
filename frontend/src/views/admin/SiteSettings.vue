<template>
    <div class="max-w-2xl">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-1">Configuración del Sitio</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">SEO, apariencia e indexación por buscadores.</p>

        <div v-if="saved"
             class="mb-4 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800
                    flex items-center gap-2 text-sm text-green-700 dark:text-green-400">
            <svg class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            Configuración guardada correctamente.
        </div>

        <div v-if="errorMsg"
             class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800
                    text-sm text-red-700 dark:text-red-400">
            {{ errorMsg }}
        </div>

        <form @submit.prevent="save" class="space-y-6">
            <!-- Identidad -->
            <section class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-4">
                <h2 class="text-base font-semibold text-gray-900 dark:text-white border-b border-gray-100 dark:border-gray-700 pb-2">
                    Identidad y SEO
                </h2>

                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre del sitio</label>
                    <input v-model="form.site_name" type="text" maxlength="100" required
                        class="block w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-900 dark:text-white
                               shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm transition-colors" />
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descripción</label>
                    <textarea v-model="form.site_description" rows="3" maxlength="500"
                        placeholder="Descripción breve del sitio (aparece en buscadores y redes sociales)"
                        class="block w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-900 dark:text-white
                               shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm resize-none transition-colors" />
                    <p class="mt-1 text-xs text-gray-400">{{ form.site_description.length }}/500</p>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">OG Image URL</label>
                    <input v-model="form.og_image_url" type="url"
                        placeholder="https://tusitio.com/og-image.png"
                        class="block w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-900 dark:text-white
                               shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm transition-colors" />
                    <p class="mt-1 text-xs text-gray-400">Imagen que aparece al compartir en redes (recomendado 1200×630px).</p>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Favicon URL</label>
                    <input v-model="form.favicon_url" type="url"
                        placeholder="https://tusitio.com/favicon.ico"
                        class="block w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-900 dark:text-white
                               shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm transition-colors" />
                </div>
            </section>

            <!-- Apariencia (skin) -->
            <section class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-4">
                <h2 class="text-base font-semibold text-gray-900 dark:text-white border-b border-gray-100 dark:border-gray-700 pb-2">
                    Apariencia (Skin)
                </h2>

                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Color primario</label>
                    <div class="flex items-center gap-3">
                        <input v-model="form.primary_color" type="color"
                            class="h-9 w-16 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer p-0.5 bg-white dark:bg-gray-900" />
                        <input v-model="form.primary_color" type="text" maxlength="7"
                            pattern="^#[0-9a-fA-F]{6}$"
                            placeholder="#4f46e5"
                            class="w-32 rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-900 dark:text-white
                                   shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono transition-colors" />
                        <div class="w-8 h-8 rounded-full border border-gray-200 dark:border-gray-700 shadow-sm"
                             :style="{ backgroundColor: form.primary_color }"></div>
                    </div>
                    <p class="mt-1 text-xs text-gray-400">Color principal del sistema (botones, enlaces activos, badges).</p>
                </div>
            </section>

            <!-- Buscadores -->
            <section class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 class="text-base font-semibold text-gray-900 dark:text-white border-b border-gray-100 dark:border-gray-700 pb-3 mb-4">
                    Indexación por buscadores
                </h2>

                <label class="flex items-start gap-4 cursor-pointer group">
                    <div class="relative mt-0.5">
                        <input type="checkbox" v-model="form.allow_indexing" class="sr-only peer" />
                        <div class="w-10 h-5 bg-gray-200 dark:bg-gray-700 rounded-full
                                    peer-checked:bg-indigo-600 transition-colors"></div>
                        <div class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow
                                    transition-transform peer-checked:translate-x-5"></div>
                    </div>
                    <div>
                        <span class="text-sm font-medium text-gray-900 dark:text-white">
                            Permitir indexación por buscadores
                        </span>
                        <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            Cuando está desactivado, <code class="font-mono bg-gray-100 dark:bg-gray-700 px-1 rounded">robots.txt</code>
                            bloquea todos los bots (<code class="font-mono bg-gray-100 dark:bg-gray-700 px-1 rounded">Disallow: /</code>).
                            Activa solo cuando el sitio esté listo para producción pública.
                        </p>
                    </div>
                </label>

                <div class="mt-4 p-3 rounded-lg bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700">
                    <p class="text-xs font-mono text-gray-500 dark:text-gray-400">
                        robots.txt actual:<br/>
                        <span class="text-gray-800 dark:text-gray-200">User-agent: *<br/>
                        {{ form.allow_indexing ? 'Allow: /' : 'Disallow: /' }}</span>
                    </p>
                </div>
            </section>

            <div class="flex justify-end">
                <button type="submit" :disabled="saving"
                    class="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700
                           text-white text-sm font-semibold shadow-sm focus:outline-none focus:ring-2
                           focus:ring-offset-2 focus:ring-indigo-500 dark:focus:ring-offset-gray-900
                           disabled:opacity-60 disabled:cursor-not-allowed transition-colors">
                    <svg v-if="saving" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    {{ saving ? "Guardando..." : "Guardar cambios" }}
                </button>
            </div>
        </form>
    </div>
</template>

<script setup>
import { reactive, ref, onMounted } from "vue";
import { api } from "@/api/index";
import { useConfigStore } from "@/stores/config";

const config = useConfigStore();
const saving = ref(false);
const saved = ref(false);
const errorMsg = ref("");

const form = reactive({
    site_name: "",
    site_description: "",
    og_image_url: "",
    favicon_url: "",
    allow_indexing: false,
    primary_color: "#4f46e5",
});

onMounted(async () => {
    try {
        const { data } = await api.get("/api/config/site/");
        Object.assign(form, {
            site_name: data.site_name || "Ximbra",
            site_description: data.site_description || "",
            og_image_url: data.og_image_url || "",
            favicon_url: data.favicon_url || "",
            allow_indexing: data.allow_indexing ?? false,
            primary_color: data.primary_color || "#4f46e5",
        });
    } catch {
        // keep defaults
    }
});

async function save() {
    saving.value = true;
    errorMsg.value = "";
    saved.value = false;
    try {
        await api.patch("/api/config/site/", form);
        saved.value = true;
        // Refresh config store so useHead picks up changes immediately
        config.reset();
        await config.fetchConfig();
        setTimeout(() => { saved.value = false; }, 3000);
    } catch (err) {
        const data = err.response?.data;
        if (data && typeof data === "object") {
            errorMsg.value = Object.values(data).flat().join(" ");
        } else {
            errorMsg.value = "Error al guardar la configuración.";
        }
    } finally {
        saving.value = false;
    }
}
</script>
