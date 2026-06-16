<template>
    <div>
        <div class="flex items-start justify-between mb-6">
            <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Unidades de Refugio Móvil</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                    Vehículos de evacuación. Su posición en el mapa proviene del conductor asignado.
                </p>
            </div>
            <button @click="openCreate"
                class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600
                       hover:bg-indigo-700 rounded-lg transition-colors">
                + Nueva unidad
            </button>
        </div>

        <div v-if="error" class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 text-sm text-red-700">
            {{ error }}
        </div>

        <div v-if="loading" class="py-12 text-center text-gray-500">Cargando...</div>

        <div v-else class="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-700/50">
                    <tr>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Código</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Placa</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Capacidad</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Conductor</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Proyecto</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Estado</th>
                        <th class="px-4 py-3"></th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                    <tr v-for="unit in units" :key="unit.id"
                        class="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                        <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ unit.code }}</td>
                        <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{{ unit.plate || '—' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{{ unit.capacity }} pers.</td>
                        <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                            {{ unit.conductor_name || '— Sin asignar —' }}
                        </td>
                        <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{{ unit.project_name || '—' }}</td>
                        <td class="px-4 py-3">
                            <span :class="unit.is_active
                                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'"
                                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                                {{ unit.is_active ? 'Activo' : 'Inactivo' }}
                            </span>
                        </td>
                        <td class="px-4 py-3 text-right">
                            <button @click="openEdit(unit)"
                                class="text-sm text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 mr-3">
                                Editar
                            </button>
                            <button @click="toggleUnit(unit)"
                                :class="unit.is_active ? 'text-red-500 hover:text-red-700' : 'text-green-600 hover:text-green-800'"
                                class="text-sm">
                                {{ unit.is_active ? 'Desactivar' : 'Activar' }}
                            </button>
                        </td>
                    </tr>
                    <tr v-if="!units.length">
                        <td colspan="7" class="px-4 py-10 text-center text-sm text-gray-500 dark:text-gray-400">
                            Sin unidades registradas. Crea la primera.
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Modal crear/editar -->
        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md">
                <div class="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                        {{ editing ? 'Editar unidad' : 'Nueva unidad de refugio' }}
                    </h3>
                    <button @click="closeModal" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                <div class="p-5 space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Código *</label>
                            <input v-model="form.code" type="text" placeholder="ej. UR-01"
                                class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                       dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Placa</label>
                            <input v-model="form.plate" type="text" placeholder="ej. ABC-123"
                                class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                       dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Capacidad (personas)</label>
                        <input v-model.number="form.capacity" type="number" min="1" max="100"
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Conductor</label>
                        <select v-model="form.conductor"
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                            <option :value="null">— Sin conductor —</option>
                            <option v-for="emp in employees" :key="emp.id" :value="emp.id">{{ emp.full_name }}</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Proyecto</label>
                        <select v-model="form.project"
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                            <option :value="null">— Sin proyecto —</option>
                            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
                        </select>
                    </div>
                    <div v-if="formError" class="p-3 rounded-lg bg-red-50 text-sm text-red-700 border border-red-200">
                        {{ formError }}
                    </div>
                    <div class="flex justify-end gap-3 pt-2">
                        <button @click="closeModal"
                            class="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50">
                            Cancelar
                        </button>
                        <button @click="saveUnit" :disabled="saving || !form.code"
                            class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700
                                   rounded-lg disabled:opacity-50 transition-colors">
                            {{ saving ? 'Guardando...' : 'Guardar' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { api } from "@/api/index";

const units = ref([]);
const employees = ref([]);
const projects = ref([]);
const loading = ref(true);
const error = ref(null);
const showModal = ref(false);
const editing = ref(null);
const saving = ref(false);
const formError = ref(null);

const emptyForm = () => ({ code: "", plate: "", capacity: 10, conductor: null, project: null });
const form = ref(emptyForm());

async function loadUnits() {
    loading.value = true;
    error.value = null;
    try {
        const res = await api.get("/api/field/refuges/");
        units.value = res.data.results ?? res.data;
    } catch {
        error.value = "Error al cargar las unidades.";
    } finally {
        loading.value = false;
    }
}

async function loadOptions() {
    const [empRes, projRes] = await Promise.all([
        api.get("/api/field/employees/?is_active=true"),
        api.get("/api/field/projects/?is_active=true"),
    ]);
    employees.value = empRes.data.results ?? empRes.data;
    projects.value = projRes.data.results ?? projRes.data;
}

function openCreate() {
    editing.value = null;
    form.value = emptyForm();
    formError.value = null;
    showModal.value = true;
}

function openEdit(unit) {
    editing.value = unit;
    form.value = {
        code: unit.code,
        plate: unit.plate || "",
        capacity: unit.capacity,
        conductor: unit.conductor || null,
        project: unit.project || null,
    };
    formError.value = null;
    showModal.value = true;
}

function closeModal() {
    showModal.value = false;
    editing.value = null;
}

async function saveUnit() {
    if (!form.value.code) return;
    saving.value = true;
    formError.value = null;
    const payload = {
        code: form.value.code,
        plate: form.value.plate,
        capacity: form.value.capacity,
        conductor: form.value.conductor || null,
        project: form.value.project || null,
    };
    try {
        if (editing.value) {
            await api.patch(`/api/field/refuges/${editing.value.id}/`, payload);
        } else {
            await api.post("/api/field/refuges/", payload);
        }
        closeModal();
        await loadUnits();
    } catch (err) {
        formError.value = err.response?.data?.code?.[0]
            || err.response?.data?.detail
            || "Error al guardar la unidad.";
    } finally {
        saving.value = false;
    }
}

async function toggleUnit(unit) {
    try {
        const res = await api.post(`/api/field/refuges/${unit.id}/toggle/`);
        unit.is_active = res.data.is_active;
    } catch {
        error.value = "Error al cambiar el estado.";
    }
}

onMounted(async () => {
    await Promise.all([loadUnits(), loadOptions()]);
});
</script>
