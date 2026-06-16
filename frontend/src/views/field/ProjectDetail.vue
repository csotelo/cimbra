<template>
    <div>
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
            <router-link :to="{ name: 'project-list' }"
                class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
                </svg>
            </router-link>
            <div v-if="project">
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ project.name }}</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                    {{ project.description || 'Sin descripción' }} ·
                    Inicio: {{ formatDate(project.start_date) }}
                    <span v-if="project.end_date"> · Fin: {{ formatDate(project.end_date) }}</span>
                </p>
            </div>
            <div v-else class="text-gray-500">Cargando...</div>
        </div>

        <div v-if="error" class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 text-sm text-red-700">
            {{ error }}
        </div>

        <!-- Empleados asignados -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow p-5">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Empleados asignados</h2>
                <button @click="openAssign"
                    class="text-sm px-3 py-1.5 text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors">
                    Gestionar asignación
                </button>
            </div>

            <div v-if="loadingProject" class="py-8 text-center text-gray-500">Cargando...</div>
            <template v-else>
                <div v-if="project?.employees_detail?.length" class="space-y-2">
                    <div v-for="emp in project.employees_detail" :key="emp.id"
                        class="flex items-center justify-between py-2 px-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                        <div>
                            <p class="text-sm font-medium text-gray-900 dark:text-white">{{ emp.full_name }}</p>
                            <p class="text-xs text-gray-500 dark:text-gray-400">{{ emp.document_number }}</p>
                        </div>
                    </div>
                </div>
                <p v-else class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
                    Sin empleados asignados. Usa "Gestionar asignación" para agregar.
                </p>
            </template>
        </div>

        <!-- Modal asignación de empleados -->
        <div v-if="showAssign" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg">
                <div class="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Asignar empleados</h3>
                    <button @click="showAssign = false" class="text-gray-400 hover:text-gray-600">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                <div class="p-5">
                    <p class="text-sm text-gray-500 dark:text-gray-400 mb-3">
                        Selecciona los empleados activos del tenant a asignar a este proyecto:
                    </p>
                    <div v-if="loadingEmployees" class="py-4 text-center text-gray-500">Cargando empleados...</div>
                    <div v-else class="max-h-72 overflow-y-auto space-y-1">
                        <label v-for="emp in allEmployees" :key="emp.id"
                            class="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer
                                   hover:bg-gray-50 dark:hover:bg-gray-700/50">
                            <input type="checkbox" :value="emp.id" v-model="selectedIds"
                                class="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
                            <span class="text-sm text-gray-900 dark:text-white">{{ emp.full_name }}</span>
                            <span class="text-xs text-gray-400 dark:text-gray-500">{{ emp.document_number }}</span>
                        </label>
                        <p v-if="!allEmployees.length" class="py-4 text-center text-sm text-gray-500">
                            No hay empleados activos en este tenant.
                        </p>
                    </div>

                    <div class="flex justify-end gap-3 mt-4">
                        <button @click="showAssign = false"
                            class="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50">
                            Cancelar
                        </button>
                        <button @click="saveAssignment" :disabled="savingAssign"
                            class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700
                                   rounded-lg disabled:opacity-50 transition-colors">
                            {{ savingAssign ? 'Guardando...' : 'Guardar asignación' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { api } from "@/api/index";

const route = useRoute();
const project = ref(null);
const loadingProject = ref(true);
const error = ref(null);
const showAssign = ref(false);
const allEmployees = ref([]);
const loadingEmployees = ref(false);
const selectedIds = ref([]);
const savingAssign = ref(false);

function formatDate(d) {
    if (!d) return "—";
    return new Date(d + "T00:00:00").toLocaleDateString("es-PE");
}

async function loadProject() {
    loadingProject.value = true;
    error.value = null;
    try {
        const res = await api.get(`/api/field/projects/${route.params.id}/`);
        project.value = res.data;
    } catch {
        error.value = "Error al cargar el proyecto.";
    } finally {
        loadingProject.value = false;
    }
}

async function openAssign() {
    showAssign.value = true;
    loadingEmployees.value = true;
    selectedIds.value = (project.value?.employees_detail || []).map(e => e.id);
    try {
        const res = await api.get("/api/field/employees/?is_active=true");
        allEmployees.value = res.data.results ?? res.data;
    } finally {
        loadingEmployees.value = false;
    }
}

async function saveAssignment() {
    savingAssign.value = true;
    try {
        await api.post(`/api/field/projects/${route.params.id}/assign_employees/`, {
            employee_ids: selectedIds.value,
        });
        showAssign.value = false;
        await loadProject();
    } catch {
        error.value = "Error al guardar asignación.";
    } finally {
        savingAssign.value = false;
    }
}

onMounted(loadProject);
</script>
