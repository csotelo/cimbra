<template>
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Historial de Consumo</h3>

        <div v-if="loading" class="text-center py-4 text-sm text-gray-400">Cargando...</div>

        <template v-else-if="plan">
            <div class="grid grid-cols-3 gap-3">
                <div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ plan.rate_limit_per_minute }}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">req / min</p>
                </div>
                <div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ formatNum(plan.requests_per_hour) }}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">req / hora</p>
                </div>
                <div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ formatNum(plan.requests_per_day) }}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">req / día</p>
                </div>
            </div>

            <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-xs text-gray-500 dark:text-gray-400">Plan activo</p>
                        <p class="text-sm font-medium text-gray-900 dark:text-white">{{ plan.plan_name }}</p>
                    </div>
                    <div class="text-right">
                        <p class="text-xs text-gray-500 dark:text-gray-400">Tenants usados</p>
                        <p class="text-sm font-medium text-gray-900 dark:text-white">
                            {{ plan.tenants_used }} / {{ plan.max_tenants }}
                        </p>
                    </div>
                </div>
            </div>
        </template>

        <p v-else class="text-sm text-gray-400 py-4 text-center">Sin plan activo.</p>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "@/api/index.js";

const plan = ref(null);
const loading = ref(true);

async function fetchPlan() {
    try {
        const res = await api.get("/api/plans/me/");
        plan.value = res.data;
    } catch { /* sin plan */ }
    loading.value = false;
}

function formatNum(n) {
    return n >= 1000 ? (n / 1000).toFixed(0) + "k" : n;
}

onMounted(fetchPlan);
</script>
