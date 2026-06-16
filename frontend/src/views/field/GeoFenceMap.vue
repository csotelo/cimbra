<template>
    <div class="flex flex-col h-full">
        <div class="flex items-start justify-between mb-4 flex-shrink-0">
            <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Frentes de Trabajo</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                    Dibuja polígonos sobre el mapa para definir los frentes de trabajo de cada proyecto.
                </p>
            </div>
            <div class="flex items-center gap-3">
                <select v-model="selectedProjectId" @change="loadFences"
                    class="text-sm rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white
                           px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    <option value="">— Todos los proyectos —</option>
                    <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
                </select>
            </div>
        </div>

        <div v-if="error" class="mb-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 text-sm text-red-700">
            {{ error }}
        </div>

        <!-- Instrucción dibujo -->
        <div class="mb-3 flex-shrink-0 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800
                    text-sm text-blue-700 dark:text-blue-400">
            Usa el <strong>control de dibujo</strong> en el mapa (icono de polígono) para trazar un frente de trabajo.
            Al terminar, asígnalo a un proyecto y guárdalo.
        </div>

        <!-- Layout principal: mapa + panel -->
        <div class="flex gap-4 flex-1 min-h-0">
            <!-- Mapa -->
            <div class="flex-1 rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 shadow-sm relative"
                style="min-height: 480px;">
                <div ref="mapContainer" class="absolute inset-0"></div>
            </div>

            <!-- Panel de frentes -->
            <div class="w-72 flex-shrink-0 overflow-y-auto">
                <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                    Frentes activos ({{ fences.length }})
                </h3>
                <div v-if="loadingFences" class="text-sm text-gray-500 py-4 text-center">Cargando...</div>
                <div v-else class="space-y-2">
                    <div v-for="fence in fences" :key="fence.id"
                        class="p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
                        <div class="flex items-start justify-between gap-2">
                            <div>
                                <p class="text-sm font-medium text-gray-900 dark:text-white">{{ fence.name }}</p>
                                <p class="text-xs text-gray-500 dark:text-gray-400">{{ fence.project_name }}</p>
                            </div>
                            <button @click="deleteFence(fence)"
                                class="text-xs text-red-500 hover:text-red-700 shrink-0">Eliminar</button>
                        </div>
                    </div>
                    <p v-if="!fences.length" class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                        Sin frentes definidos.
                    </p>
                </div>
            </div>
        </div>

        <!-- Modal guardar frente dibujado -->
        <div v-if="showSaveModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm">
                <div class="p-5 border-b border-gray-200 dark:border-gray-700">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Guardar frente de trabajo</h3>
                </div>
                <div class="p-5 space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre del frente *</label>
                        <input v-model="newFence.name" type="text" required placeholder="ej. Cantera Variante"
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Proyecto *</label>
                        <select v-model="newFence.project" required
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                            <option value="">— Selecciona un proyecto —</option>
                            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
                        </select>
                    </div>
                    <div v-if="saveError" class="p-3 rounded-lg bg-red-50 text-sm text-red-700 border border-red-200">
                        {{ saveError }}
                    </div>
                    <div class="flex justify-end gap-3">
                        <button @click="cancelSave"
                            class="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50">
                            Cancelar
                        </button>
                        <button @click="saveFence" :disabled="saving || !newFence.name || !newFence.project"
                            class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700
                                   rounded-lg disabled:opacity-50 transition-colors">
                            {{ saving ? 'Guardando...' : 'Guardar' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { api } from "@/api/index";
import L from "leaflet";
import "leaflet-draw/dist/leaflet.draw.css";
import "leaflet-draw";

const mapContainer = ref(null);
let map = null;
let drawnItems = null;

const projects = ref([]);
const fences = ref([]);
const selectedProjectId = ref("");
const loadingFences = ref(false);
const error = ref(null);
const showSaveModal = ref(false);
const saving = ref(false);
const saveError = ref(null);
const pendingGeoJSON = ref(null);
const pendingLayer = ref(null);

const newFence = ref({ name: "", project: "" });

const FENCE_COLORS = [
    "#4f46e5", "#059669", "#d97706", "#dc2626", "#7c3aed",
    "#0891b2", "#16a34a", "#ea580c",
];

function fenceColor(idx) {
    return FENCE_COLORS[idx % FENCE_COLORS.length];
}

async function loadProjects() {
    try {
        const res = await api.get("/api/field/projects/?is_active=true");
        projects.value = res.data.results ?? res.data;
    } catch {
        error.value = "Error al cargar proyectos.";
    }
}

async function loadFences() {
    loadingFences.value = true;
    error.value = null;
    try {
        let url = "/api/field/fences/geojson/?is_active=true";
        if (selectedProjectId.value) url += `&project=${selectedProjectId.value}`;
        const res = await api.get(url);
        const geojson = res.data;

        // Fetch list for sidebar
        let listUrl = "/api/field/fences/?is_active=true";
        if (selectedProjectId.value) listUrl += `&project=${selectedProjectId.value}`;
        const listRes = await api.get(listUrl);
        fences.value = listRes.data.results ?? listRes.data;

        // Clear existing fence layers from map
        if (map) {
            map.eachLayer(layer => {
                if (layer._isFence) map.removeLayer(layer);
            });
            // Draw fences from GeoJSON
            if (geojson.features?.length) {
                geojson.features.forEach((feature, idx) => {
                    const layer = L.geoJSON(feature, {
                        style: {
                            color: fenceColor(idx),
                            fillColor: fenceColor(idx),
                            fillOpacity: 0.15,
                            weight: 2,
                        },
                    }).addTo(map);
                    layer._isFence = true;
                    layer.bindTooltip(
                        `<strong>${feature.properties.name}</strong><br>${feature.properties.project_name}`,
                        { permanent: false, direction: "center" }
                    );
                });
            }
        }
    } catch {
        error.value = "Error al cargar frentes.";
    } finally {
        loadingFences.value = false;
    }
}

function initMap() {
    map = L.map(mapContainer.value, { center: [-9.19, -75.01], zoom: 6 });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
        maxZoom: 19,
    }).addTo(map);

    drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
        edit: { featureGroup: drawnItems, remove: false },
        draw: {
            polygon: { shapeOptions: { color: "#4f46e5" } },
            polyline: false,
            rectangle: false,
            circle: false,
            circlemarker: false,
            marker: false,
        },
    });
    map.addControl(drawControl);

    map.on(L.Draw.Event.CREATED, (e) => {
        const layer = e.layer;
        drawnItems.addLayer(layer);
        pendingGeoJSON.value = layer.toGeoJSON().geometry;
        pendingLayer.value = layer;
        newFence.value = { name: "", project: selectedProjectId.value || "" };
        saveError.value = null;
        showSaveModal.value = true;
    });
}

async function saveFence() {
    if (!newFence.value.name || !newFence.value.project) return;
    saving.value = true;
    saveError.value = null;
    try {
        const res = await api.post("/api/field/fences/", {
            name: newFence.value.name,
            project: newFence.value.project,
            perimeter: pendingGeoJSON.value,
        });
        fences.value.unshift(res.data);
        showSaveModal.value = false;
        pendingGeoJSON.value = null;
        pendingLayer.value = null;
        await loadFences();
    } catch (err) {
        saveError.value = err.response?.data?.detail || err.response?.data?.perimeter?.[0] || "Error al guardar el frente.";
    } finally {
        saving.value = false;
    }
}

function cancelSave() {
    if (pendingLayer.value) drawnItems.removeLayer(pendingLayer.value);
    pendingLayer.value = null;
    pendingGeoJSON.value = null;
    showSaveModal.value = false;
}

async function deleteFence(fence) {
    if (!confirm(`¿Eliminar el frente "${fence.name}"?`)) return;
    try {
        await api.delete(`/api/field/fences/${fence.id}/`);
        fences.value = fences.value.filter(f => f.id !== fence.id);
        await loadFences();
    } catch {
        error.value = "Error al eliminar el frente.";
    }
}

onMounted(async () => {
    await loadProjects();
    initMap();
    await loadFences();
});

onUnmounted(() => {
    if (map) { map.remove(); map = null; }
});
</script>
