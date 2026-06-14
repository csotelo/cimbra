<template>
    <div>
        <div class="flex items-center justify-between mb-6">
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Alertas de Tormenta</h1>
            <button @click="load" :disabled="loading"
                class="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-700 text-white rounded-md disabled:opacity-50">
                {{ loading ? 'Actualizando...' : 'Actualizar' }}
            </button>
        </div>

        <!-- Resumen por nivel -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <div v-for="lvl in levels" :key="lvl.value"
                class="rounded-lg p-4 text-white"
                :style="{ background: lvl.color }">
                <div class="text-2xl font-bold">{{ countByLevel(lvl.value) }}</div>
                <div class="text-sm opacity-90">Nivel {{ lvl.value }} — {{ lvl.label }}</div>
            </div>
        </div>

        <!-- Tabla de alertas activas -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <div v-if="loading" class="p-8 text-center text-gray-500">Cargando alertas...</div>
            <div v-else-if="!alerts.length" class="p-8 text-center text-gray-500">
                Sin alertas activas. El predictor generará alertas en el próximo ciclo.
            </div>
            <table v-else class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-700">
                    <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Estación</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Departamento</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Nivel</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Probabilidad</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Generado</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Modelo</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                    <tr v-for="alert in alerts" :key="alert.id"
                        class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                        <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                            {{ alert.station_name }}
                        </td>
                        <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{{ alert.department }}</td>
                        <td class="px-4 py-3">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold text-white"
                                :style="{ background: levelColor(alert.alert_level) }">
                                {{ alert.level_label }}
                            </span>
                        </td>
                        <td class="px-4 py-3 text-sm font-mono font-bold"
                            :style="{ color: levelColor(alert.alert_level) }">
                            {{ (alert.probability * 100).toFixed(1) }}%
                        </td>
                        <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                            {{ formatDate(alert.generated_at) }}
                        </td>
                        <td class="px-4 py-3 text-xs text-gray-400 font-mono">{{ alert.model_version }}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <p v-if="lastUpdated" class="mt-3 text-xs text-gray-400 text-right">
            Última actualización: {{ formatDate(lastUpdated) }}
        </p>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { api } from "@/api/index";

const alerts = ref([]);
const loading = ref(false);
const lastUpdated = ref(null);
let interval = null;

const levels = [
    { value: 1, label: "Verde", color: "#22c55e" },
    { value: 2, label: "Amarillo", color: "#eab308" },
    { value: 3, label: "Naranja", color: "#f97316" },
    { value: 4, label: "Rojo", color: "#ef4444" },
];

const COLORS = { 1: "#22c55e", 2: "#eab308", 3: "#f97316", 4: "#ef4444" };

function levelColor(level) {
    return COLORS[level] || "#6b7280";
}

function countByLevel(level) {
    return alerts.value.filter(a => a.alert_level === level).length;
}

function formatDate(dt) {
    if (!dt) return "—";
    return new Date(dt).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" });
}

async function load() {
    loading.value = true;
    try {
        const res = await api.get("/api/weather/alerts/");
        alerts.value = res.data.results ?? res.data;
        lastUpdated.value = new Date().toISOString();
    } catch (e) {
        console.error("Error cargando alertas:", e);
    } finally {
        loading.value = false;
    }
}

onMounted(() => {
    load();
    interval = setInterval(load, 5 * 60 * 1000); // refresca cada 5 min
});

onUnmounted(() => clearInterval(interval));
</script>
