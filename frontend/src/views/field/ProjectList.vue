<template>
    <div>
        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Proyectos de Campo</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Obras y frentes de trabajo activos.</p>
            </div>
            <button @click="openCreate"
                class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors">
                + Nuevo proyecto
            </button>
        </div>

        <div v-if="error" class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800
                                  text-sm text-red-700 dark:text-red-400">{{ error }}</div>

        <div v-if="loading" class="py-16 text-center text-gray-500 dark:text-gray-400">Cargando proyectos...</div>

        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="proj in projects" :key="proj.id"
                class="bg-white dark:bg-gray-800 rounded-xl shadow p-5 border border-gray-100 dark:border-gray-700
                       hover:shadow-md transition-shadow">
                <div class="flex items-start justify-between mb-3">
                    <h3 class="font-semibold text-gray-900 dark:text-white">{{ proj.name }}</h3>
                    <span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium ml-2 shrink-0"
                        :class="proj.is_active
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'">
                        {{ proj.is_active ? 'Activo' : 'Inactivo' }}
                    </span>
                </div>
                <p v-if="proj.description" class="text-sm text-gray-500 dark:text-gray-400 mb-3 line-clamp-2">
                    {{ proj.description }}
                </p>
                <div class="text-xs text-gray-400 dark:text-gray-500 space-y-1 mb-4">
                    <div>Inicio: {{ formatDate(proj.start_date) }}</div>
                    <div v-if="proj.end_date">Fin: {{ formatDate(proj.end_date) }}</div>
                    <div>Empleados: <strong class="text-gray-600 dark:text-gray-300">{{ proj.employee_count }}</strong></div>
                </div>
                <div class="flex gap-2">
                    <router-link :to="{ name: 'project-detail', params: { id: proj.id } }"
                        class="flex-1 text-center text-xs px-3 py-1.5 rounded-lg border border-indigo-300 text-indigo-600
                               dark:border-indigo-700 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20">
                        Ver detalle
                    </router-link>
                    <button @click="openEdit(proj)"
                        class="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600
                               text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700">
                        Editar
                    </button>
                </div>
            </div>

            <div v-if="projects.length === 0"
                class="col-span-full py-16 text-center text-gray-500 dark:text-gray-400">
                No hay proyectos registrados aún.
            </div>
        </div>

        <!-- Modal crear / editar proyecto -->
        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md">
                <div class="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                        {{ editing ? 'Editar proyecto' : 'Nuevo proyecto' }}
                    </h3>
                    <button @click="closeModal" class="text-gray-400 hover:text-gray-600">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                <form @submit.prevent="save" class="p-5 space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre del proyecto *</label>
                        <input v-model="form.name" type="text" required
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descripción</label>
                        <textarea v-model="form.description" rows="3"
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"></textarea>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fecha inicio *</label>
                            <input v-model="form.start_date" type="date" required
                                class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                       dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fecha fin</label>
                            <input v-model="form.end_date" type="date"
                                class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                       dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                        </div>
                    </div>

                    <div v-if="formError" class="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 text-sm text-red-700 dark:text-red-400">
                        {{ formError }}
                    </div>

                    <div class="flex justify-end gap-3 pt-2">
                        <button type="button" @click="closeModal"
                            class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-600
                                   rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                            Cancelar
                        </button>
                        <button type="submit" :disabled="saving"
                            class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700
                                   rounded-lg disabled:opacity-50 transition-colors">
                            {{ saving ? 'Guardando...' : 'Guardar' }}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { api } from "@/api/index";

const projects = ref([]);
const loading = ref(true);
const error = ref(null);
const showModal = ref(false);
const editing = ref(null);
const saving = ref(false);
const formError = ref(null);
const form = ref({ name: "", description: "", start_date: "", end_date: "" });

function formatDate(d) {
    if (!d) return "—";
    return new Date(d + "T00:00:00").toLocaleDateString("es-PE");
}

async function load() {
    loading.value = true;
    error.value = null;
    try {
        const res = await api.get("/api/field/projects/");
        projects.value = res.data.results ?? res.data;
    } catch {
        error.value = "Error al cargar proyectos.";
    } finally {
        loading.value = false;
    }
}

function openCreate() {
    editing.value = null;
    form.value = { name: "", description: "", start_date: "", end_date: "" };
    formError.value = null;
    showModal.value = true;
}

function openEdit(proj) {
    editing.value = proj;
    form.value = { name: proj.name, description: proj.description, start_date: proj.start_date, end_date: proj.end_date || "" };
    formError.value = null;
    showModal.value = true;
}

function closeModal() { showModal.value = false; editing.value = null; }

async function save() {
    saving.value = true;
    formError.value = null;
    const payload = { ...form.value };
    if (!payload.end_date) delete payload.end_date;
    try {
        if (editing.value) {
            const res = await api.patch(`/api/field/projects/${editing.value.id}/`, payload);
            const idx = projects.value.findIndex(p => p.id === editing.value.id);
            if (idx !== -1) projects.value[idx] = res.data;
        } else {
            const res = await api.post("/api/field/projects/", payload);
            projects.value.unshift(res.data);
        }
        closeModal();
    } catch (err) {
        formError.value = err.response?.data?.name?.[0] || "Error al guardar.";
    } finally {
        saving.value = false;
    }
}

onMounted(load);
</script>
