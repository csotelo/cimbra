<template>
    <div class="flex flex-col h-full">
        <div class="flex items-start justify-between mb-4 flex-shrink-0">
            <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Mapa de Seguridad</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                    Vista integrada: frentes de trabajo, refugios, unidades en campo y alertas de tormenta.
                </p>
            </div>
            <div class="flex items-center gap-2">
                <span :class="tracking ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'"
                    class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium">
                    <span class="w-2 h-2 rounded-full" :class="tracking ? 'bg-green-500 animate-pulse' : 'bg-gray-400'"></span>
                    {{ tracking ? 'GPS en vivo' : 'Pausado' }}
                </span>
                <button @click="toggleTracking"
                    class="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                           hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300">
                    {{ tracking ? 'Pausar' : 'Reanudar' }}
                </button>
            </div>
        </div>

        <!-- Leyenda capas -->
        <div class="mb-3 flex-shrink-0 flex flex-wrap gap-3 text-xs">
            <span v-for="layer in legendItems" :key="layer.label"
                class="flex items-center gap-1.5 px-2.5 py-1 rounded-full border"
                :style="`background:${layer.bg};border-color:${layer.border};color:${layer.color}`">
                <span class="w-3 h-3 rounded-sm inline-block" :style="`background:${layer.dot}`"></span>
                {{ layer.label }}
            </span>
        </div>

        <div v-if="error" class="mb-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 text-sm text-red-700">
            {{ error }}
        </div>

        <div class="flex gap-4 flex-1 min-h-0">
            <div class="flex-1 rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 shadow-sm relative"
                style="min-height: 520px;">
                <div ref="mapContainer" class="absolute inset-0"></div>
            </div>

            <!-- Panel derecho -->
            <div class="w-64 flex-shrink-0 overflow-y-auto space-y-4">
                <!-- Alertas activas -->
                <div>
                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Alertas activas ({{ alerts.length }})
                    </h3>
                    <div class="space-y-1">
                        <div v-for="alert in alerts.slice(0, 5)" :key="alert.id"
                            class="p-2 rounded-lg border text-xs"
                            :style="`background:${levelBg(alert.alert_level)};border-color:${levelColor(alert.alert_level)}40`">
                            <p class="font-semibold" :style="`color:${levelColor(alert.alert_level)}`">
                                {{ alert.level_label }}
                            </p>
                            <p class="text-gray-700 dark:text-gray-300">{{ alert.station_name }}</p>
                            <p class="text-gray-500">{{ (alert.probability * 100).toFixed(0) }}% prob.</p>
                        </div>
                        <p v-if="!alerts.length" class="text-xs text-gray-400 text-center py-2">Sin alertas activas.</p>
                    </div>
                </div>

                <!-- Unidades en campo -->
                <div>
                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Unidades en campo ({{ livePositions.length }})
                    </h3>
                    <div class="space-y-1">
                        <div v-for="pos in livePositions" :key="pos.entity_id"
                            class="p-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700
                                   text-xs cursor-pointer hover:border-indigo-400"
                            @click="centerOn(pos.lat, pos.lon, 14)">
                            <div class="flex items-center gap-1.5">
                                <span class="w-2 h-2 rounded-full" :class="pos.mobile_refuge ? 'bg-orange-500' : 'bg-indigo-500'"></span>
                                <span class="font-medium text-gray-900 dark:text-white truncate">{{ pos.label }}</span>
                            </div>
                            <p v-if="pos.mobile_refuge" class="text-orange-600 dark:text-orange-400 ml-3.5">
                                {{ pos.mobile_refuge.code }}
                            </p>
                        </div>
                        <p v-if="!livePositions.length" class="text-xs text-gray-400 text-center py-2">Sin GPS recibido.</p>
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
const liveMarkers = {};

const alerts = ref([]);
const livePositions = ref([]);
const error = ref(null);
const tracking = ref(true);
let trackTimer = null;

const legendItems = [
    { label: "Frentes de trabajo", dot: "#4f46e5", bg: "#eef2ff", border: "#a5b4fc", color: "#3730a3" },
    { label: "Refugios fijos", dot: "#16a34a", bg: "#f0fdf4", border: "#86efac", color: "#15803d" },
    { label: "Empleados GPS", dot: "#4f46e5", bg: "#eef2ff", border: "#a5b4fc", color: "#3730a3" },
    { label: "Refugio móvil", dot: "#f97316", bg: "#fff7ed", border: "#fdba74", color: "#c2410c" },
    { label: "Estaciones", dot: "#0891b2", bg: "#ecfeff", border: "#67e8f9", color: "#0e7490" },
];

const LEVEL_COLORS = { 1: "#22c55e", 2: "#eab308", 3: "#f97316", 4: "#ef4444" };

function levelColor(level) { return LEVEL_COLORS[level] || "#6b7280"; }
function levelBg(level) {
    const map = { 1: "#f0fdf4", 2: "#fefce8", 3: "#fff7ed", 4: "#fef2f2" };
    return map[level] || "#f9fafb";
}

const EMPLOYEE_ICON = L.divIcon({
    className: "",
    html: `<div style="width:14px;height:14px;border-radius:50%;background:#4f46e5;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.4)"></div>`,
    iconSize: [14, 14], iconAnchor: [7, 7],
});
const REFUGE_MOBILE_ICON = L.divIcon({
    className: "",
    html: `<div style="width:18px;height:18px;border-radius:50%;background:#f97316;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.4)"></div>`,
    iconSize: [18, 18], iconAnchor: [9, 9],
});
const STATION_ICON = (color) => L.divIcon({
    className: "",
    html: `<div style="width:16px;height:16px;border-radius:3px;background:${color};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.4)"></div>`,
    iconSize: [16, 16], iconAnchor: [8, 8],
});

function buildRefugeIcon() {
    return L.divIcon({
        className: "",
        html: `<div style="width:22px;height:22px;border-radius:50%;background:#16a34a;border:2.5px solid white;
                           box-shadow:0 2px 6px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center;">
                   <svg width="11" height="11" viewBox="0 0 24 24" fill="white"><path d="M12 2L2 7v15h20V7L12 2zm0 2.24L20 8.5V20H4V8.5L12 4.24zM12 10a3 3 0 100 6 3 3 0 000-6z"/></svg>
               </div>`,
        iconSize: [22, 22], iconAnchor: [11, 11],
    });
}

function initMap() {
    map = L.map(mapContainer.value, { center: [-9.19, -75.01], zoom: 6 });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
        maxZoom: 19,
    }).addTo(map);
}

async function loadStaticLayers() {
    const [fencesRes, refugesRes, stationsRes] = await Promise.allSettled([
        api.get("/api/field/fences/geojson/?is_active=true"),
        api.get("/api/field/points/geojson/?is_active=true"),
        api.get("/api/weather/stations/geojson/"),
    ]);

    if (fencesRes.status === "fulfilled") {
        const geojson = fencesRes.value.data;
        if (geojson.features?.length) {
            L.geoJSON(geojson, {
                style: { color: "#4f46e5", fillColor: "#4f46e5", fillOpacity: 0.1, weight: 2 },
                onEachFeature: (feat, layer) => layer.bindTooltip(`<strong>${feat.properties.name}</strong>`, { direction: "center" }),
            }).addTo(map);
        }
    }

    if (refugesRes.status === "fulfilled") {
        const geojson = refugesRes.value.data;
        if (geojson.features?.length) {
            geojson.features.forEach(feat => {
                const [lng, lat] = feat.geometry.coordinates;
                L.marker([lat, lng], { icon: buildRefugeIcon() })
                    .bindPopup(`<strong>${feat.properties.name}</strong><br>Cap. ${feat.properties.capacity} pers.`)
                    .addTo(map);
            });
        }
    }

    if (stationsRes.status === "fulfilled") {
        const geojson = stationsRes.value.data;
        if (geojson.features?.length) {
            geojson.features.forEach(feat => {
                const [lng, lat] = feat.geometry.coordinates;
                L.marker([lat, lng], { icon: STATION_ICON("#0891b2") })
                    .bindPopup(`<strong>${feat.properties.name}</strong><br>${feat.properties.code || ""}`)
                    .addTo(map);
            });
        }
    }
}

async function loadAlerts() {
    try {
        const res = await api.get("/api/weather/alerts/?is_active=true&limit=20");
        alerts.value = res.data.results ?? res.data;
    } catch { /* alerts non-critical */ }
}

async function fetchLive() {
    try {
        const res = await api.get("/api/field/tracking/live/");
        const data = res.data.positions || [];
        livePositions.value = data;
        updateLiveMarkers(data);
        error.value = null;
    } catch {
        error.value = "Error al obtener posiciones GPS.";
    }
}

function updateLiveMarkers(data) {
    const seen = new Set();
    for (const pos of data) {
        seen.add(pos.entity_id);
        const latlng = [pos.lat, pos.lon];
        const icon = pos.mobile_refuge ? REFUGE_MOBILE_ICON : EMPLOYEE_ICON;
        const popup = `<strong>${pos.label}</strong>${pos.mobile_refuge ? `<br>${pos.mobile_refuge.code}` : ""}`;

        if (liveMarkers[pos.entity_id]) {
            liveMarkers[pos.entity_id].setLatLng(latlng);
            liveMarkers[pos.entity_id].setPopupContent(popup);
        } else {
            liveMarkers[pos.entity_id] = L.marker(latlng, { icon }).addTo(map).bindPopup(popup);
        }
    }
    for (const eid of Object.keys(liveMarkers)) {
        if (!seen.has(eid)) { map.removeLayer(liveMarkers[eid]); delete liveMarkers[eid]; }
    }
}

function centerOn(lat, lon, zoom = 14) {
    if (map) map.setView([lat, lon], zoom);
}

function startTracking() {
    tracking.value = true;
    fetchLive();
    trackTimer = setInterval(fetchLive, 5000);
}

function stopTracking() {
    tracking.value = false;
    if (trackTimer) { clearInterval(trackTimer); trackTimer = null; }
}

function toggleTracking() {
    tracking.value ? stopTracking() : startTracking();
}

onMounted(async () => {
    initMap();
    await Promise.all([loadStaticLayers(), loadAlerts()]);
    startTracking();
});

onUnmounted(() => {
    stopTracking();
    if (map) { map.remove(); map = null; }
});
</script>
