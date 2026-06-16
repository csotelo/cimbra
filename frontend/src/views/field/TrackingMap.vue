<template>
    <div class="flex flex-col h-full">
        <div class="flex items-start justify-between mb-4 flex-shrink-0">
            <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Rastreo en Tiempo Real</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                    Posición en vivo de empleados y unidades móviles. Actualización automática cada 5 s.
                </p>
            </div>
            <div class="flex items-center gap-3">
                <span :class="polling ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                       : 'bg-gray-100 text-gray-500'"
                    class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium">
                    <span class="w-2 h-2 rounded-full" :class="polling ? 'bg-green-500 animate-pulse' : 'bg-gray-400'"></span>
                    {{ polling ? 'En vivo' : 'Pausado' }}
                </span>
                <button @click="togglePolling"
                    class="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                           hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300">
                    {{ polling ? 'Pausar' : 'Reanudar' }}
                </button>
            </div>
        </div>

        <div v-if="error" class="mb-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 text-sm text-red-700">
            {{ error }}
        </div>

        <div class="flex gap-4 flex-1 min-h-0">
            <!-- Mapa -->
            <div class="flex-1 rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 shadow-sm relative"
                style="min-height: 480px;">
                <div ref="mapContainer" class="absolute inset-0"></div>
            </div>

            <!-- Panel unidades -->
            <div class="w-72 flex-shrink-0 overflow-y-auto space-y-2">
                <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                    Unidades activas ({{ positions.length }})
                </h3>
                <div v-for="pos in positions" :key="pos.entity_id"
                    class="p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm
                           cursor-pointer hover:border-indigo-400 transition-colors"
                    @click="centerOn(pos)">
                    <div class="flex items-start gap-2">
                        <span class="mt-0.5 w-2.5 h-2.5 rounded-full flex-shrink-0"
                            :class="pos.mobile_refuge ? 'bg-orange-500' : 'bg-indigo-500'"></span>
                        <div class="min-w-0">
                            <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ pos.label }}</p>
                            <p v-if="pos.mobile_refuge" class="text-xs text-orange-600 dark:text-orange-400">
                                Refugio: {{ pos.mobile_refuge.code }} · {{ pos.mobile_refuge.plate }}
                            </p>
                            <p class="text-xs text-gray-500 dark:text-gray-400 font-mono">
                                {{ pos.lat.toFixed(5) }}, {{ pos.lon.toFixed(5) }}
                            </p>
                            <p class="text-xs text-gray-400 dark:text-gray-500">{{ formatTs(pos.ts) }}</p>
                        </div>
                    </div>
                </div>
                <p v-if="!positions.length" class="text-sm text-gray-500 dark:text-gray-400 text-center py-6">
                    Sin posiciones recibidas. Los dispositivos de campo deben estar enviando GPS por MQTT.
                </p>
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
const markers = {};  // entity_id → L.Marker

const positions = ref([]);
const polling = ref(true);
const error = ref(null);
let pollTimer = null;

const EMPLOYEE_ICON = L.divIcon({
    className: "",
    html: `<div style="width:14px;height:14px;border-radius:50%;background:#4f46e5;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.4)"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
});

const REFUGE_ICON = L.divIcon({
    className: "",
    html: `<div style="width:18px;height:18px;border-radius:50%;background:#f97316;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.4)"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
});

function initMap() {
    map = L.map(mapContainer.value, { center: [-9.19, -75.01], zoom: 6 });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
        maxZoom: 19,
    }).addTo(map);
}

async function fetchPositions() {
    try {
        const res = await api.get("/api/field/tracking/live/");
        const data = res.data.positions || [];
        positions.value = data;
        updateMarkers(data);
        error.value = null;
    } catch {
        error.value = "Error al obtener posiciones en vivo.";
    }
}

function updateMarkers(data) {
    const seen = new Set();
    for (const pos of data) {
        seen.add(pos.entity_id);
        const latlng = [pos.lat, pos.lon];
        const icon = pos.mobile_refuge ? REFUGE_ICON : EMPLOYEE_ICON;
        const popupHtml = buildPopup(pos);

        if (markers[pos.entity_id]) {
            markers[pos.entity_id].setLatLng(latlng);
            markers[pos.entity_id].setPopupContent(popupHtml);
        } else {
            markers[pos.entity_id] = L.marker(latlng, { icon })
                .addTo(map)
                .bindPopup(popupHtml);
        }
    }
    // Remove stale markers
    for (const eid of Object.keys(markers)) {
        if (!seen.has(eid)) {
            map.removeLayer(markers[eid]);
            delete markers[eid];
        }
    }
}

function buildPopup(pos) {
    let html = `<strong>${pos.label}</strong>`;
    if (pos.mobile_refuge) {
        html += `<br>Refugio: ${pos.mobile_refuge.code}`;
        if (pos.mobile_refuge.plate) html += ` · ${pos.mobile_refuge.plate}`;
        html += `<br>Capacidad: ${pos.mobile_refuge.capacity} pers.`;
    }
    html += `<br><span style="font-size:11px;color:#888">${formatTs(pos.ts)}</span>`;
    return html;
}

function centerOn(pos) {
    if (map) {
        map.setView([pos.lat, pos.lon], 14);
        const m = markers[pos.entity_id];
        if (m) m.openPopup();
    }
}

function formatTs(ts) {
    if (!ts) return "—";
    try {
        return new Date(ts).toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
        return ts;
    }
}

function startPolling() {
    polling.value = true;
    fetchPositions();
    pollTimer = setInterval(fetchPositions, 5000);
}

function stopPolling() {
    polling.value = false;
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

function togglePolling() {
    polling.value ? stopPolling() : startPolling();
}

onMounted(() => {
    initMap();
    startPolling();
});

onUnmounted(() => {
    stopPolling();
    if (map) { map.remove(); map = null; }
});
</script>
