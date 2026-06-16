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
                    class="p-3 rounded-lg bg-white dark:bg-gray-800 border shadow-sm
                           cursor-pointer transition-colors hover:border-indigo-400"
                    :class="alertBorderClass(pos)"
                    @click="centerOn(pos)">
                    <div class="flex items-start gap-2">
                        <span class="mt-0.5 w-2.5 h-2.5 rounded-full flex-shrink-0"
                            :class="pos.mobile_refuge ? 'bg-orange-500' : 'bg-indigo-500'"></span>
                        <div class="min-w-0">
                            <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ pos.label }}</p>
                            <p v-if="pos.mobile_refuge" class="text-xs text-orange-600 dark:text-orange-400">
                                Refugio: {{ pos.mobile_refuge.code }} · {{ pos.mobile_refuge.plate }}
                            </p>
                            <!-- Alert badge -->
                            <div v-if="pos.field_alert && pos.field_alert.level > 1"
                                class="mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                                :class="alertBadgeClass(pos.field_alert.level)">
                                ⚡ {{ alertLabel(pos.field_alert.level) }}
                                <span v-if="pos.field_alert.distance_km">
                                    · {{ pos.field_alert.distance_km }} km
                                </span>
                            </div>
                            <p class="text-xs text-gray-500 dark:text-gray-400 font-mono mt-0.5">
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
const markers = {};

const positions = ref([]);
const polling = ref(true);
const error = ref(null);
let pollTimer = null;

const ALERT_COLORS = { 4: "#ef4444", 3: "#f97316", 2: "#eab308", 1: null };
const ALERT_LABELS = { 4: "Alerta Roja", 3: "Alerta Naranja", 2: "Alerta Amarilla", 1: "Sin riesgo" };

function alertLabel(level) { return ALERT_LABELS[level] || "—"; }

function alertBorderClass(pos) {
    const level = pos.field_alert?.level;
    if (level >= 4) return "border-red-400 dark:border-red-600";
    if (level >= 3) return "border-orange-400 dark:border-orange-600";
    if (level >= 2) return "border-yellow-400 dark:border-yellow-600";
    return "border-gray-200 dark:border-gray-700";
}

function alertBadgeClass(level) {
    if (level >= 4) return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
    if (level >= 3) return "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400";
    return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400";
}

function makeIcon(isRefuge, alertLevel) {
    const baseColor = isRefuge ? "#f97316" : "#4f46e5";
    const size = isRefuge ? 18 : 14;
    const ring = ALERT_COLORS[alertLevel];
    const ringHtml = ring
        ? `<div style="position:absolute;top:-5px;left:-5px;width:${size + 10}px;height:${size + 10}px;
                       border-radius:50%;border:2.5px solid ${ring};
                       animation:pulse 1.2s ease-in-out infinite;"></div>`
        : "";
    return L.divIcon({
        className: "",
        html: `<style>@keyframes pulse{0%,100%{opacity:.5;transform:scale(1)}50%{opacity:1;transform:scale(1.15)}}</style>
               <div style="position:relative;width:${size}px;height:${size}px;">
                   ${ringHtml}
                   <div style="width:${size}px;height:${size}px;border-radius:50%;background:${baseColor};
                                border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.4)"></div>
               </div>`,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
    });
}

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
        const alertLevel = pos.field_alert?.level || 1;
        const icon = makeIcon(!!pos.mobile_refuge, alertLevel);
        const popup = buildPopup(pos);

        if (markers[pos.entity_id]) {
            markers[pos.entity_id].setLatLng(latlng);
            markers[pos.entity_id].setIcon(icon);
            markers[pos.entity_id].setPopupContent(popup);
        } else {
            markers[pos.entity_id] = L.marker(latlng, { icon })
                .addTo(map)
                .bindPopup(popup);
        }
    }
    for (const eid of Object.keys(markers)) {
        if (!seen.has(eid)) { map.removeLayer(markers[eid]); delete markers[eid]; }
    }
}

function buildPopup(pos) {
    let html = `<strong>${pos.label}</strong>`;
    if (pos.mobile_refuge) {
        html += `<br>Refugio: ${pos.mobile_refuge.code}`;
        if (pos.mobile_refuge.plate) html += ` · ${pos.mobile_refuge.plate}`;
    }
    if (pos.field_alert && pos.field_alert.level > 1) {
        const color = ALERT_COLORS[pos.field_alert.level] || "#888";
        html += `<br><span style="color:${color};font-weight:bold">⚡ ${alertLabel(pos.field_alert.level)}</span>`;
        if (pos.field_alert.distance_km) html += ` (${pos.field_alert.distance_km} km)`;
        if (pos.field_alert.station) html += `<br>${pos.field_alert.station}`;
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
    } catch { return ts; }
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

onMounted(() => { initMap(); startPolling(); });
onUnmounted(() => { stopPolling(); if (map) { map.remove(); map = null; } });
</script>
