<template>
    <div>
        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Empleados de Campo</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                    Personal registrado para monitoreo y alertas de tormenta.
                </p>
            </div>
            <button @click="openCreate"
                class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors">
                + Nuevo empleado
            </button>
        </div>

        <!-- Buscador -->
        <div class="mb-4">
            <input v-model="search" type="text" placeholder="Buscar por nombre..."
                class="w-full sm:w-72 px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                       dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>

        <!-- Error -->
        <div v-if="error" class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800
                                  text-sm text-red-700 dark:text-red-400">
            {{ error }}
        </div>

        <!-- Tabla -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
            <div v-if="loading" class="py-16 text-center text-gray-500 dark:text-gray-400">
                Cargando empleados...
            </div>
            <template v-else>
                <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead class="bg-gray-50 dark:bg-gray-900">
                        <tr>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Nombre</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Documento</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Device ID</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Estado</th>
                            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Acciones</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                        <tr v-for="emp in filtered" :key="emp.id" class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                            <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ emp.full_name }}</td>
                            <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{{ emp.document_number }}</td>
                            <td class="px-4 py-3 text-sm font-mono text-gray-500 dark:text-gray-400">{{ emp.device_id }}</td>
                            <td class="px-4 py-3">
                                <span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium"
                                    :class="emp.is_active
                                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                        : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'">
                                    {{ emp.is_active ? 'Activo' : 'Inactivo' }}
                                </span>
                            </td>
                            <td class="px-4 py-3 text-right">
                                <div class="flex items-center justify-end gap-2">
                                    <button @click="openEdit(emp)"
                                        class="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600
                                               text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
                                        Editar
                                    </button>
                                    <button @click="toggleEmployee(emp)"
                                        :disabled="toggling === emp.id"
                                        class="text-xs px-2 py-1 rounded border transition-colors"
                                        :class="emp.is_active
                                            ? 'border-red-300 text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-900/20'
                                            : 'border-green-300 text-green-600 hover:bg-green-50 dark:border-green-700 dark:text-green-400 dark:hover:bg-green-900/20'">
                                        {{ emp.is_active ? 'Desactivar' : 'Activar' }}
                                    </button>
                                </div>
                            </td>
                        </tr>
                        <tr v-if="filtered.length === 0">
                            <td colspan="5" class="px-4 py-12 text-center text-sm text-gray-500 dark:text-gray-400">
                                {{ search ? 'Sin resultados para "' + search + '"' : 'No hay empleados registrados aún.' }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </template>
        </div>

        <!-- Modal crear / editar -->
        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md">
                <div class="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                        {{ editing ? 'Editar empleado' : 'Nuevo empleado' }}
                    </h3>
                    <button @click="closeModal" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                <form @submit.prevent="save" class="p-5 space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre completo *</label>
                        <input v-model="form.full_name" type="text" required
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Número de documento *</label>
                        <input v-model="form.document_number" type="text" required
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Código de dispositivo (Device ID) *
                        </label>
                        <input v-model="form.device_id" type="text" required
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            placeholder="ej. EMP-001 o UUID del dispositivo" />
                        <p class="mt-1 text-xs text-gray-400">Identificador único del dispositivo móvil para MQTT</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">FCM Token</label>
                        <input v-model="form.fcm_token" type="text"
                            class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                                   dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            placeholder="Token para notificaciones push (opcional)" />
                    </div>

                    <div v-if="formError" class="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800
                                                   text-sm text-red-700 dark:text-red-400">
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
import { ref, computed, onMounted } from "vue";
import { api } from "@/api/index";

const employees = ref([]);
const loading = ref(true);
const error = ref(null);
const search = ref("");
const showModal = ref(false);
const editing = ref(null);
const saving = ref(false);
const toggling = ref(null);
const formError = ref(null);

const form = ref({ full_name: "", document_number: "", device_id: "", fcm_token: "" });

const filtered = computed(() => {
    if (!search.value) return employees.value;
    const q = search.value.toLowerCase();
    return employees.value.filter(e => e.full_name.toLowerCase().includes(q));
});

async function load() {
    loading.value = true;
    error.value = null;
    try {
        const res = await api.get("/api/field/employees/");
        employees.value = res.data.results ?? res.data;
    } catch {
        error.value = "Error al cargar empleados.";
    } finally {
        loading.value = false;
    }
}

function openCreate() {
    editing.value = null;
    form.value = { full_name: "", document_number: "", device_id: "", fcm_token: "" };
    formError.value = null;
    showModal.value = true;
}

function openEdit(emp) {
    editing.value = emp;
    form.value = { full_name: emp.full_name, document_number: emp.document_number, device_id: emp.device_id, fcm_token: emp.fcm_token || "" };
    formError.value = null;
    showModal.value = true;
}

function closeModal() {
    showModal.value = false;
    editing.value = null;
}

async function save() {
    saving.value = true;
    formError.value = null;
    try {
        if (editing.value) {
            const res = await api.patch(`/api/field/employees/${editing.value.id}/`, form.value);
            const idx = employees.value.findIndex(e => e.id === editing.value.id);
            if (idx !== -1) employees.value[idx] = res.data;
        } else {
            const res = await api.post("/api/field/employees/", form.value);
            employees.value.unshift(res.data);
        }
        closeModal();
    } catch (err) {
        const data = err.response?.data;
        if (data?.device_id) formError.value = data.device_id[0];
        else formError.value = "Error al guardar. Verifica los datos.";
    } finally {
        saving.value = false;
    }
}

async function toggleEmployee(emp) {
    toggling.value = emp.id;
    try {
        const res = await api.post(`/api/field/employees/${emp.id}/toggle/`);
        emp.is_active = res.data.is_active;
    } catch {
        error.value = "Error al cambiar el estado del empleado.";
    } finally {
        toggling.value = null;
    }
}

onMounted(load);
</script>
