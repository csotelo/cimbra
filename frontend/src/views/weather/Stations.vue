<template>
    <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Estaciones Meteorológicas</h1>

        <div v-if="loading" class="text-center py-12 text-gray-500">Cargando estaciones...</div>

        <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-700">
                    <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Código</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Nombre</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Departamento</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Latitud</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Longitud</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Altitud</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Estado</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                    <tr v-for="st in stations" :key="st.id" class="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td class="px-4 py-3 text-sm font-mono text-gray-700 dark:text-gray-300">{{ st.code }}</td>
                        <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ st.name }}</td>
                        <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{{ st.department }}</td>
                        <td class="px-4 py-3 text-sm font-mono text-gray-500">{{ st.latitude }}</td>
                        <td class="px-4 py-3 text-sm font-mono text-gray-500">{{ st.longitude }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ st.altitude_m ? st.altitude_m + ' m' : '—' }}</td>
                        <td class="px-4 py-3">
                            <span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium"
                                :class="st.is_active
                                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                    : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'">
                                {{ st.is_active ? 'Activa' : 'Inactiva' }}
                            </span>
                        </td>
                    </tr>
                </tbody>
            </table>
            <div v-if="!stations.length" class="p-8 text-center text-gray-500">
                Sin estaciones registradas. Ejecuta <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">seed_stations</code> en Django.
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { api } from "@/api/index";

const stations = ref([]);
const loading = ref(true);

onMounted(async () => {
    try {
        const res = await api.get("/api/weather/stations/");
        stations.value = res.data.results ?? res.data;
    } finally {
        loading.value = false;
    }
});
</script>
