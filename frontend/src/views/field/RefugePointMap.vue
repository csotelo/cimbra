<template>
    <div class="flex flex-col h-full">
        <div class="flex items-start justify-between mb-4 flex-shrink-0">
            <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Puntos de Refugio Fijo</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                    Haz clic en el mapa para agregar un nuevo punto de refugio fijo.
                </p>
            </div>
            <div>
                <select v-model="selectedProjectId" @change="loadPoints"
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

        <div class="mb-3 flex-shrink-0 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800
                    text-sm text-green-700 dark:text-green-400">
            Haz <strong>clic en el mapa</strong> para posicionar un nuevo punto de refugio. Luego completa el formulario y guárdalo.
        </div>

        <div class="flex gap-4 flex-1 min-h-0">
            <!-- Mapa -->
            <div class="flex-1 rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 shadow-sm relative"
                style="min-height: 480px;">
                <div ref="mapContainer" class="absolute inset-0"></div>
            </div>

            <!-- Panel -->
            <div class="w-72 flex-shrink-0 overflow-y-auto">
                <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                    Puntos activos ({{ points.length }})
                </h3>
                <div v-if="loadingPoints" class="text-sm text-gray-500 py-4 text-center">Cargando...</div>
                <div v-else class="space-y-2">
                    <div v-for="pt in points" :key="pt.id"
                        class="p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
                        <div class="flex items-start justify-between gap-2">
                            <div>
                                <p class="text-sm font-medium text-gray-900 dark:text-white">{{ pt.name }}</p>
                                <p class="text-xs text-gray-500 dark:text-gray-400">Cap. {{ pt.capacity }} pers.</p>
                                <p v-if="pt.project_name" class="text-xs text-gray-400">{{ pt.project_name }}</p>
                            </div>
                            <button @click="deletePoint(pt)"
                                class="text-xs text-red-500 hover:text-red-700 shrink-0">Eliminar</button>
                        </div>
                    </div>
                    <p v-if="!points.length" class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                        Sin puntos de refugio definidos.
                    </p>
                </div>
            </div>
        </div>

        <!-- Modal nuevo punto -->
        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm">
                <div class="p-5 border-b border-gray-200 dark:border-gray-700">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Nuevo punto de refugio</h3>
                    <p class="text-xs text-gray-500 mt-1">
                        {{ pendingLatLng ? `${pendingLatLng.lat.toFixed(5)}, ${pendingLatLng.lng.toFixed(5)}` : '' }}
                    </p>
                </div>
                <div class="p-5 space-y-3">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre *</label>
                        <input v-model="form.name" type="text" placeholder="ej. Almacén Norte"
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descripción</label>
                        <textarea v-model="form.description" rows="2" placeholder="Condiciones, acceso, etc."
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"></textarea>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Capacidad</label>
                            <input v-model.number="form.capacity" type="number" min="1"
                                class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                       dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Proyecto</label>
                            <select v-model="form.project"
                                class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                       dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                                <option :value="null">— Ninguno —</option>
                                <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
                            </select>
                        </div>
                    </div>
                    <div v-if="saveError" class="p-3 rounded-lg bg-red-50 text-sm text-red-700 border border-red-200">
                        {{ saveError }}
                    </div>
                    <div class="flex justify-end gap-3 pt-1">
                        <button @click="cancelModal"
                            class="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50">
                            Cancelar
                        </button>
                        <button @click="savePoint" :disabled="saving || !form.name"
                            class="px-4 py-2 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700
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

const mapContainer = ref(null);
let map = null;

const projects = ref([]);
const points = ref([]);
const selectedProjectId = ref("");
const loadingPoints = ref(false);
const error = ref(null);
const showModal = ref(false);
const saving = ref(false);
const saveError = ref(null);
const pendingLatLng = ref(null);
let pendingMarker = null;

const form = ref({ name: "", description: "", capacity: 50, project: null });

const REFUGE_ICON = L.divIcon({
    className: "",
    html: `<div style="width:22px;height:22px;border-radius:50%;background:#16a34a;border:2.5px solid white;
                       box-shadow:0 2px 6px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;">
               <svg width="12" height="12" viewBox="0 0 24 24" fill="white">
                   <path d="M12 2L2 7v15h20V7L12 2zm0 2.24L20 8.5V20H4V8.5L12 4.24zM12 10a3 3 0 100 6 3 3 0 000-6z"/>
               </svg>
           </div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -12],
});

async function loadProjects() {
    try {
        const res = await api.get("/api/field/projects/?is_active=true");
        projects.value = res.data.results ?? res.data;
    } catch {
        error.value = "Error al cargar proyectos.";
    }
}

async function loadPoints() {
    loadingPoints.value = true;
    error.value = null;
    try {
        let url = "/api/field/points/?is_active=true";
        if (selectedProjectId.value) url += `&project=${selectedProjectId.value}`;
        const listRes = await api.get(url);
        points.value = listRes.data.results ?? listRes.data;

        let geoUrl = "/api/field/points/geojson/?is_active=true";
        if (selectedProjectId.value) geoUrl += `&project=${selectedProjectId.value}`;
        const geoRes = await api.get(geoUrl);

        // Remove existing refuge markers
        if (map) {
            map.eachLayer(layer => {
                if (layer._isRefuge) map.removeLayer(layer);
            });
            if (geoRes.data.features?.length) {
                geoRes.data.features.forEach(feature => {
                    const [lng, lat] = feature.geometry.coordinates;
                    const marker = L.marker([lat, lng], { icon: REFUGE_ICON }).addTo(map);
                    marker._isRefuge = true;
                    marker.bindPopup(
                        `<strong>${feature.properties.name}</strong><br>Cap. ${feature.properties.capacity} pers.`
                        + (feature.properties.project_name ? `<br>${feature.properties.project_name}` : "")
                    );
                });
            }
        }
    } catch {
        error.value = "Error al cargar los puntos de refugio.";
    } finally {
        loadingPoints.value = false;
    }
}

function initMap() {
    map = L.map(mapContainer.value, { center: [-9.19, -75.01], zoom: 6 });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
        maxZoom: 19,
    }).addTo(map);

    map.on("click", (e) => {
        if (pendingMarker) map.removeLayer(pendingMarker);
        pendingLatLng.value = e.latlng;
        pendingMarker = L.marker(e.latlng, { icon: REFUGE_ICON }).addTo(map);
        form.value = { name: "", description: "", capacity: 50, project: selectedProjectId.value || null };
        saveError.value = null;
        showModal.value = true;
    });
}

async function savePoint() {
    if (!form.value.name || !pendingLatLng.value) return;
    saving.value = true;
    saveError.value = null;
    try {
        await api.post("/api/field/points/", {
            name: form.value.name,
            description: form.value.description,
            capacity: form.value.capacity,
            project: form.value.project || null,
            location: {
                type: "Point",
                coordinates: [pendingLatLng.value.lng, pendingLatLng.value.lat],
            },
        });
        showModal.value = false;
        pendingLatLng.value = null;
        pendingMarker = null;
        await loadPoints();
    } catch (err) {
        saveError.value = err.response?.data?.detail || err.response?.data?.name?.[0] || "Error al guardar.";
    } finally {
        saving.value = false;
    }
}

function cancelModal() {
    if (pendingMarker) { map.removeLayer(pendingMarker); pendingMarker = null; }
    pendingLatLng.value = null;
    showModal.value = false;
}

async function deletePoint(pt) {
    if (!confirm(`¿Eliminar "${pt.name}"?`)) return;
    try {
        await api.delete(`/api/field/points/${pt.id}/`);
        await loadPoints();
    } catch {
        error.value = "Error al eliminar el punto.";
    }
}

onMounted(async () => {
    await loadProjects();
    initMap();
    await loadPoints();
});

onUnmounted(() => {
    if (map) { map.remove(); map = null; }
});
</script>
