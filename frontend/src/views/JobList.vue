<template>
    <div>
        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Jobs</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Procesos ejecutados en tu cuenta</p>
            </div>
            <button
                @click="load"
                class="px-3 py-1.5 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
                Actualizar
            </button>
        </div>

        <NotificationBanner v-if="error" type="error" :message="error" @close="error = null" />

        <!-- Filtros -->
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-4 mb-4 flex flex-wrap gap-4">
            <input
                v-model="search"
                type="text"
                placeholder="Buscar por nombre..."
                class="rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
            <select
                v-model="statusFilter"
                class="rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            >
                <option value="">Todos los estados</option>
                <option value="SUCCESS">Success</option>
                <option value="FAILURE">Failure</option>
                <option value="STARTED">Started</option>
                <option value="PENDING">Pending</option>
                <option value="REVOKED">Revoked</option>
            </select>
            <button @click="resetFilters" class="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200">
                Limpiar
            </button>
        </div>

        <!-- Tabla -->
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
            <div v-if="loading" class="text-center py-12">
                <p class="text-gray-500 dark:text-gray-400">Cargando jobs...</p>
            </div>

            <template v-else>
                <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead class="bg-gray-50 dark:bg-gray-900">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tarea</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Estado</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Duración</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Fecha</th>
                            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Acciones</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                        <tr v-if="jobs.length === 0">
                            <td colspan="5" class="px-6 py-10 text-center text-sm text-gray-500 dark:text-gray-400">
                                Sin jobs registrados.
                            </td>
                        </tr>
                        <tr
                            v-for="job in jobs"
                            :key="job.task_id"
                            class="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                            @click="openDetail(job)"
                        >
                            <td class="px-6 py-4">
                                <p class="text-sm font-medium text-gray-900 dark:text-white">{{ shortName(job.task_name) }}</p>
                                <p class="text-xs text-gray-400 font-mono">{{ job.task_id.slice(0, 16) }}…</p>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-2 py-1 text-xs font-medium rounded-full" :class="statusClass(job.status)">
                                    {{ job.status }}
                                </span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                {{ job.duration_seconds != null ? `${job.duration_seconds}s` : '—' }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                {{ formatDate(job.date_created) }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-right text-sm" @click.stop>
                                <button
                                    @click="confirmDelete(job)"
                                    class="text-red-500 dark:text-red-400 hover:text-red-700"
                                >
                                    Eliminar
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <!-- Paginación -->
                <div class="px-6 py-4 flex items-center justify-between border-t border-gray-200 dark:border-gray-700">
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        <span v-if="count > 0">{{ pageStart }}–{{ pageEnd }} de {{ count }} jobs</span>
                    </p>
                    <div class="flex space-x-2">
                        <button @click="prevPage" :disabled="!previous"
                            class="px-3 py-1 text-sm rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-40 dark:text-gray-300 disabled:cursor-not-allowed">
                            Previous
                        </button>
                        <span class="px-3 py-1 text-sm text-gray-600 dark:text-gray-400">Página {{ currentPage }}</span>
                        <button @click="nextPage" :disabled="!next"
                            class="px-3 py-1 text-sm rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-40 dark:text-gray-300 disabled:cursor-not-allowed">
                            Next
                        </button>
                    </div>
                </div>
            </template>
        </div>

        <!-- Modal detalle -->
        <div v-if="selectedJob" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40" @click.self="selectedJob = null">
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
                <div class="flex items-start justify-between mb-4">
                    <div>
                        <h2 class="text-lg font-medium text-gray-900 dark:text-white">{{ shortName(selectedJob.task_name) }}</h2>
                        <p class="text-xs text-gray-400 font-mono mt-1">{{ selectedJob.task_id }}</p>
                    </div>
                    <span class="px-2 py-1 text-xs font-medium rounded-full" :class="statusClass(selectedJob.status)">
                        {{ selectedJob.status }}
                    </span>
                </div>
                <div class="space-y-4 text-sm">
                    <div class="grid grid-cols-2 gap-4 text-gray-600 dark:text-gray-400">
                        <div><span class="font-medium">Creado:</span> {{ formatDate(selectedJob.date_created) }}</div>
                        <div><span class="font-medium">Completado:</span> {{ formatDate(selectedJob.date_done) }}</div>
                        <div><span class="font-medium">Duración:</span> {{ selectedJob.duration_seconds != null ? `${selectedJob.duration_seconds}s` : '—' }}</div>
                        <div><span class="font-medium">Worker:</span> {{ selectedJob.worker || '—' }}</div>
                    </div>
                    <div v-if="selectedJob.result">
                        <p class="font-medium text-gray-700 dark:text-gray-300 mb-1">Resultado:</p>
                        <pre class="text-xs bg-gray-50 dark:bg-gray-900 p-3 rounded overflow-x-auto text-gray-800 dark:text-gray-200">{{ formatResult(selectedJob.result) }}</pre>
                    </div>
                    <div v-if="selectedJob.traceback">
                        <p class="font-medium text-red-600 dark:text-red-400 mb-1">Error:</p>
                        <pre class="text-xs bg-red-50 dark:bg-red-900 p-3 rounded overflow-x-auto text-red-800 dark:text-red-200">{{ selectedJob.traceback }}</pre>
                    </div>
                </div>
                <div class="flex justify-end mt-4">
                    <button @click="selectedJob = null" class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700">
                        Cerrar
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { jobsApi } from "@/api/jobs";
import NotificationBanner from "@/components/NotificationBanner.vue";

const jobs = ref([]);
const count = ref(0);
const next = ref(null);
const previous = ref(null);
const loading = ref(false);
const error = ref(null);
const currentPage = ref(1);
const pageSize = 20;
const search = ref("");
const statusFilter = ref("");
const selectedJob = ref(null);

let searchTimeout = null;

const pageStart = computed(() => (currentPage.value - 1) * pageSize + 1);
const pageEnd = computed(() => Math.min(currentPage.value * pageSize, count.value));

function buildParams() {
    const params = { page: currentPage.value };
    if (search.value) params.search = search.value;
    if (statusFilter.value) params.status = statusFilter.value;
    return params;
}

async function load() {
    loading.value = true;
    error.value = null;
    try {
        const response = await jobsApi.list(buildParams());
        const data = response.data;
        jobs.value = data.results ?? data;
        count.value = data.count ?? data.length;
        next.value = data.next ?? null;
        previous.value = data.previous ?? null;
    } catch (e) {
        error.value = e.response?.data?.detail || "Error al cargar jobs";
    } finally {
        loading.value = false;
    }
}

watch(search, () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => { currentPage.value = 1; load(); }, 400);
});
watch(statusFilter, () => { currentPage.value = 1; load(); });

function nextPage() { if (next.value) { currentPage.value++; load(); } }
function prevPage() { if (previous.value) { currentPage.value--; load(); } }

function resetFilters() {
    search.value = "";
    statusFilter.value = "";
    currentPage.value = 1;
    load();
}

function shortName(name) {
    if (!name) return "—";
    return name.split(".").pop();
}

function formatDate(dateStr) {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleString();
}

function formatResult(result) {
    try { return JSON.stringify(JSON.parse(result), null, 2); }
    catch { return result; }
}

function statusClass(s) {
    const map = {
        SUCCESS: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
        FAILURE: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
        STARTED: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
        PENDING: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
        REVOKED: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
    };
    return map[s] || "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300";
}

function openDetail(job) { selectedJob.value = job; }

async function confirmDelete(job) {
    if (!confirm(`¿Eliminar job ${shortName(job.task_name)}?`)) return;
    try {
        await jobsApi.delete(job.task_id);
        load();
    } catch (e) {
        error.value = e.response?.data?.detail || "Error al eliminar job";
    }
}

onMounted(load);
</script>
