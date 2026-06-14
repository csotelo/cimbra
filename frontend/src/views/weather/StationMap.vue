<template>
    <div class="flex flex-col h-full">
        <div class="flex items-start justify-between mb-4 flex-shrink-0">
            <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Mapa de Alertas</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                    Distribución geográfica de estaciones y alertas activas en Perú.
                </p>
            </div>
            <div class="flex items-center gap-3">
                <button @click="refresh" :disabled="loading"
                    class="flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                           text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700
                           disabled:opacity-50 transition-colors">
                    <svg :class="loading ? 'animate-spin' : ''" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                    </svg>
                    Actualizar
                </button>
            </div>
        </div>

        <!-- Leyenda -->
        <div class="flex flex-wrap items-center gap-4 mb-3 flex-shrink-0">
            <div v-for="lvl in levels" :key="lvl.value" class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
                <span class="w-3 h-3 rounded-full inline-block" :style="{ background: lvl.color }"></span>
                <span>{{ lvl.label }}</span>
            </div>
            <div class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
                <span class="w-3 h-3 rounded-full inline-block bg-gray-400"></span>
                <span>Sin alerta activa</span>
            </div>
            <span v-if="lastUpdated" class="ml-auto text-xs text-gray-400">
                Actualizado: {{ lastUpdated }}
            </span>
        </div>

        <!-- Error state -->
        <div v-if="loadError"
             class="mb-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800
                    flex items-center gap-2 text-sm text-red-700 dark:text-red-400">
            <svg class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            Error al cargar datos del mapa. Reintentando automáticamente...
        </div>

        <!-- Mapa -->
        <div class="relative flex-1 rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 shadow-sm"
             style="min-height: 480px;">
            <div ref="mapContainer" class="absolute inset-0"></div>
            <!-- Empty state sobre el mapa -->
            <div v-if="emptyStations && !loading"
                 class="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-gray-900/80 z-10">
                <div class="text-center">
                    <svg class="w-10 h-10 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/>
                    </svg>
                    <p class="text-sm text-gray-500 dark:text-gray-400">Sin estaciones registradas.</p>
                    <p class="text-xs text-gray-400 mt-1">Ejecuta <code class="font-mono bg-gray-100 dark:bg-gray-700 px-1 rounded">seed_stations</code> en Django.</p>
                </div>
            </div>
        </div>

        <!-- Estadísticas por nivel -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 flex-shrink-0">
            <div v-for="lvl in levels" :key="lvl.value"
                 class="rounded-xl p-4 text-white text-center"
                 :style="{ background: lvl.color }">
                <div class="text-2xl font-bold">{{ countByLevel(lvl.value) }}</div>
                <div class="text-xs opacity-90 mt-0.5">{{ lvl.label }}</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { api } from "@/api/index";

const mapContainer = ref(null);
const loading = ref(false);
const loadError = ref(false);
const emptyStations = ref(false);
const lastUpdated = ref(null);

let map = null;
let alertLayer = null;
let stationLayer = null;
let consecutiveErrors = 0;

const levels = [
    { value: 1, label: "Verde — Sin riesgo",   color: "#22c55e" },
    { value: 2, label: "Amarillo — Moderado",  color: "#eab308" },
    { value: 3, label: "Naranja — Peligroso",  color: "#f97316" },
    { value: 4, label: "Rojo — Extremo",       color: "#ef4444" },
];

const alertData = ref([]);

function countByLevel(level) {
    return alertData.value.filter(f => f.properties.alert_level === level).length;
}

function initMap() {
    map = L.map(mapContainer.value, {
        center: [-9.19, -75.0],
        zoom: 5,
        zoomControl: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 18,
    }).addTo(map);

    stationLayer = L.layerGroup().addTo(map);
    alertLayer  = L.layerGroup().addTo(map);
}

function renderStations(geojson) {
    stationLayer.clearLayers();
    for (const feature of geojson.features) {
        const [lng, lat] = feature.geometry.coordinates;
        const { code, name, department, altitude_m } = feature.properties;
        L.circleMarker([lat, lng], {
            radius: 5,
            fillColor: "#94a3b8",
            color: "#64748b",
            weight: 1,
            opacity: 0.8,
            fillOpacity: 0.5,
        })
        .bindPopup(
            `<div class="text-sm">
                <p class="font-semibold">${name}</p>
                <p class="text-gray-500">${department}</p>
                <p class="text-gray-400 text-xs font-mono">${code}${altitude_m ? " · " + altitude_m + " m" : ""}</p>
                <p class="text-gray-400 text-xs mt-1">Sin alerta activa</p>
            </div>`
        )
        .addTo(stationLayer);
    }
}

function renderAlerts(geojson) {
    alertLayer.clearLayers();
    alertData.value = geojson.features;

    // Markers por alerta (encima de las estaciones grises)
    for (const feature of geojson.features) {
        const [lng, lat] = feature.geometry.coordinates;
        const p = feature.properties;
        L.circleMarker([lat, lng], {
            radius: 10,
            fillColor: p.color,
            color: "#fff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.85,
        })
        .bindPopup(
            `<div class="text-sm" style="min-width:160px">
                <p class="font-semibold">${p.station_name}</p>
                <p class="text-gray-500">${p.department}${p.altitude_m ? " · " + p.altitude_m + " m" : ""}</p>
                <div class="mt-2 flex items-center gap-2">
                    <span style="background:${p.color};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600">
                        ${p.level_label}
                    </span>
                    <span style="color:${p.color};font-weight:700">${(p.probability * 100).toFixed(1)}%</span>
                </div>
                <p class="text-gray-400 text-xs mt-1">v${p.model_version}</p>
                <p class="text-gray-400 text-xs">${new Date(p.generated_at).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" })}</p>
            </div>`
        )
        .addTo(alertLayer);
    }
}

async function refresh() {
    loading.value = true;
    try {
        const [stationsRes, alertsRes] = await Promise.all([
            api.get("/api/weather/stations/geojson/"),
            api.get("/api/weather/alerts/geojson/"),
        ]);
        renderStations(stationsRes.data);
        renderAlerts(alertsRes.data);
        emptyStations.value = (stationsRes.data?.features?.length ?? 0) === 0;
        lastUpdated.value = new Date().toLocaleTimeString("es-PE");
        loadError.value = false;
        consecutiveErrors = 0;
    } catch (e) {
        consecutiveErrors++;
        loadError.value = true;
        console.error("Error cargando datos del mapa:", e);
    } finally {
        loading.value = false;
    }
}

let refreshTimeout = null;

function scheduleNext() {
    const base = 5 * 60 * 1000;
    const delay = Math.min(base * Math.pow(2, consecutiveErrors), 20 * 60 * 1000);
    refreshTimeout = setTimeout(async () => {
        await refresh();
        scheduleNext();
    }, delay);
}

onMounted(async () => {
    initMap();
    await refresh();
    scheduleNext();
});

onUnmounted(() => {
    clearTimeout(refreshTimeout);
    if (map) map.remove();
});
</script>
