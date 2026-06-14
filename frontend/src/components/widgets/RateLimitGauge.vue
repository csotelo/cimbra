<template>
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
        <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Consumo Rate Limit</h3>
            <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="planBadgeClass">
                {{ data?.plan ?? '—' }}
            </span>
        </div>

        <div v-if="loading" class="text-center py-4 text-sm text-gray-400">Cargando...</div>

        <template v-else-if="data">
            <!-- Minuto -->
            <div class="mb-4">
                <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                    <span>Este minuto</span>
                    <span>{{ data.usage.minute }} / {{ data.limits.rate_limit_per_minute }}</span>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                    <div class="h-2.5 rounded-full transition-all duration-500"
                        :class="barClass(minutePct)"
                        :style="{ width: minutePct + '%' }"></div>
                </div>
            </div>

            <!-- Hora + Día -->
            <div class="grid grid-cols-2 gap-3">
                <div>
                    <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                        <span>Esta hora</span>
                        <span>{{ data.usage.hour }} / {{ data.limits.requests_per_hour }}</span>
                    </div>
                    <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div class="h-1.5 rounded-full transition-all duration-500"
                            :class="barClass(hourPct)"
                            :style="{ width: hourPct + '%' }"></div>
                    </div>
                </div>
                <div>
                    <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                        <span>Hoy</span>
                        <span>{{ data.usage.day }} / {{ data.limits.requests_per_day }}</span>
                    </div>
                    <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div class="h-1.5 rounded-full transition-all duration-500"
                            :class="barClass(dayPct)"
                            :style="{ width: dayPct + '%' }"></div>
                    </div>
                </div>
            </div>

            <p class="text-xs text-gray-400 dark:text-gray-500 mt-3 text-right">
                Actualizado hace {{ secondsAgo }}s
            </p>
        </template>

        <p v-else class="text-sm text-gray-400 py-4 text-center">Sin plan activo.</p>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import api from "@/api/index.js";

const data = ref(null);
const loading = ref(true);
const secondsAgo = ref(0);

let pollInterval = null;
let tickInterval = null;

async function fetchUsage() {
    try {
        const res = await api.get("/api/plans/usage/");
        data.value = res.data;
        secondsAgo.value = 0;
    } catch { /* sin plan o error */ }
    loading.value = false;
}

const minutePct = computed(() => data.value
    ? Math.min(100, Math.round(data.value.usage.minute / data.value.limits.rate_limit_per_minute * 100))
    : 0);
const hourPct = computed(() => data.value
    ? Math.min(100, Math.round(data.value.usage.hour / data.value.limits.requests_per_hour * 100))
    : 0);
const dayPct = computed(() => data.value
    ? Math.min(100, Math.round(data.value.usage.day / data.value.limits.requests_per_day * 100))
    : 0);

function barClass(pct) {
    if (pct >= 90) return "bg-red-500";
    if (pct >= 70) return "bg-yellow-500";
    return "bg-green-500";
}

const planBadgeClass = computed(() => {
    const p = data.value?.plan;
    if (p === "Basic") return "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300";
    if (p === "Pro") return "bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300";
    if (p === "Enterprise") return "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300";
    return "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300";
});

onMounted(() => {
    fetchUsage();
    pollInterval = setInterval(fetchUsage, 30_000);
    tickInterval = setInterval(() => secondsAgo.value++, 1_000);
});
onUnmounted(() => {
    clearInterval(pollInterval);
    clearInterval(tickInterval);
});
</script>
