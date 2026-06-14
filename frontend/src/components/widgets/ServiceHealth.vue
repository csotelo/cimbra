<template>
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Estado de Servicios</h3>
            <span class="text-xs px-2 py-0.5 rounded-full font-medium"
                :class="overall === 'ok'
                    ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                    : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'">
                {{ overall === 'ok' ? 'Todos OK' : 'Degradado' }}
            </span>
        </div>

        <div v-if="loading" class="text-center py-4 text-sm text-gray-400">Cargando...</div>

        <div v-else class="space-y-3">
            <div v-for="(info, name) in services" :key="name"
                class="flex items-center justify-between py-1">
                <div class="flex items-center space-x-2.5">
                    <div class="relative flex h-2.5 w-2.5">
                        <span v-if="info.status === 'ok'"
                            class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2.5 w-2.5"
                            :class="info.status === 'ok' ? 'bg-green-500' : 'bg-red-500'"></span>
                    </div>
                    <span class="text-sm text-gray-700 dark:text-gray-300 font-medium">{{ name }}</span>
                </div>
                <div class="text-right">
                    <span class="text-xs font-medium"
                        :class="info.status === 'ok' ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'">
                        {{ info.status === 'ok' ? 'OK' : 'DOWN' }}
                    </span>
                    <span v-if="info.latency_ms != null" class="text-xs text-gray-400 ml-1.5">
                        {{ info.latency_ms }}ms
                    </span>
                </div>
            </div>
        </div>

        <p class="text-xs text-gray-400 dark:text-gray-500 mt-4 text-right">
            Actualizado hace {{ secondsAgo }}s
        </p>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import api from "@/api/index.js";

const services = ref({});
const overall = ref("ok");
const loading = ref(true);
const secondsAgo = ref(0);

let pollInterval = null;
let tickInterval = null;

async function fetchHealth() {
    try {
        const res = await api.get("/api/watchdog/health/");
        services.value = res.data.services;
        overall.value = res.data.overall;
        secondsAgo.value = 0;
    } catch { /* network error */ }
    loading.value = false;
}

onMounted(() => {
    fetchHealth();
    pollInterval = setInterval(fetchHealth, 30_000);
    tickInterval = setInterval(() => secondsAgo.value++, 1_000);
});
onUnmounted(() => {
    clearInterval(pollInterval);
    clearInterval(tickInterval);
});
</script>
