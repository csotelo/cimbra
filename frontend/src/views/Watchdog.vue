<template>
    <div>
        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Watchdog</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Estado y ejecución de tareas de infraestructura</p>
            </div>
            <button
                @click="loadHealth"
                class="px-3 py-1.5 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
                Actualizar
            </button>
        </div>

        <NotificationBanner v-if="error" type="error" :message="error" @close="error = null" />

        <!-- Estado de servicios -->
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-5 mb-5">
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Estado de servicios</p>
            <div v-if="loadingHealth" class="text-sm text-gray-500 dark:text-gray-400">Cargando...</div>
            <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div
                    v-for="(svc, name) in health.services"
                    :key="name"
                    class="flex items-center justify-between px-4 py-3 rounded-lg border border-gray-100 dark:border-gray-700"
                >
                    <div class="flex items-center gap-2">
                        <span
                            class="w-2.5 h-2.5 rounded-full flex-shrink-0"
                            :class="svc.status === 'ok' ? 'bg-green-500' : 'bg-red-500'"
                        ></span>
                        <span class="text-sm font-medium text-gray-800 dark:text-gray-200 capitalize">{{ name }}</span>
                    </div>
                    <span class="text-xs text-gray-400">
                        {{ svc.latency_ms != null ? `${svc.latency_ms}ms` : '—' }}
                    </span>
                </div>
                <div v-if="!health.services || Object.keys(health.services).length === 0" class="text-sm text-gray-400 col-span-2">
                    Sin datos de estado.
                </div>
            </div>
        </div>

        <!-- Tareas programadas -->
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-5 mb-5">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tareas programadas</p>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Cron jobs propios — cada ejecución aparece en Jobs.</p>
                </div>
                <button @click="showCreateForm = !showCreateForm"
                    class="px-3 py-1.5 text-sm font-medium bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                    + Nueva
                </button>
            </div>

            <!-- Formulario de creación -->
            <div v-if="showCreateForm" class="mb-4 p-4 rounded-lg border border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-950">
                <p class="text-xs font-medium text-indigo-700 dark:text-indigo-300 uppercase tracking-wider mb-3">Nueva tarea programada</p>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Tarea</label>
                        <select v-model="newSchedule.task_key"
                            class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm shadow-sm">
                            <option value="">Selecciona una tarea</option>
                            <option v-for="t in availableTasks" :key="t.key" :value="t.key">{{ t.label }}</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Cada</label>
                        <input v-model.number="newSchedule.every" type="number" min="1" placeholder="1"
                            class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm shadow-sm" />
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Período</label>
                        <select v-model="newSchedule.period"
                            class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm shadow-sm">
                            <option value="minutes">Minutos</option>
                            <option value="hours">Horas</option>
                            <option value="days">Días</option>
                        </select>
                    </div>
                </div>
                <div class="flex gap-2 mt-3">
                    <button @click="createSchedule" :disabled="creating"
                        class="px-4 py-2 text-sm font-medium bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50">
                        {{ creating ? 'Guardando...' : 'Guardar' }}
                    </button>
                    <button @click="showCreateForm = false"
                        class="px-4 py-2 text-sm font-medium border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700">
                        Cancelar
                    </button>
                </div>
            </div>

            <!-- Lista de schedules -->
            <div v-if="schedules.length === 0 && !showCreateForm" class="text-sm text-gray-400 py-2">
                Sin tareas programadas. Crea una con "+ Nueva".
            </div>
            <div v-else class="space-y-2">
                <div v-for="s in schedules" :key="s.id"
                    class="flex items-center justify-between px-4 py-3 rounded-lg border border-gray-100 dark:border-gray-700">
                    <div class="flex items-center gap-3 flex-1 min-w-0">
                        <span class="w-2 h-2 rounded-full flex-shrink-0"
                            :class="s.enabled ? 'bg-green-500' : 'bg-gray-400'"></span>
                        <div class="min-w-0">
                            <p class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ s.label }}</p>
                            <p class="text-xs text-gray-400">
                                Cada {{ s.every }} {{ s.period }}
                                <span v-if="s.last_run_at"> · Último: {{ new Date(s.last_run_at).toLocaleString() }}</span>
                                <span v-if="s.total_run_count"> · {{ s.total_run_count }} ejecuciones</span>
                            </p>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 flex-shrink-0 ml-3">
                        <!-- Editar frecuencia -->
                        <template v-if="editingId === s.id">
                            <input v-model.number="editEvery" type="number" min="1"
                                class="w-16 rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm shadow-sm text-center" />
                            <select v-model="editPeriod"
                                class="rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm shadow-sm">
                                <option value="minutes">min</option>
                                <option value="hours">h</option>
                                <option value="days">d</option>
                            </select>
                            <button @click="saveEdit(s.id)" class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">Guardar</button>
                            <button @click="editingId = null" class="text-xs text-gray-400 hover:underline">Cancelar</button>
                        </template>
                        <template v-else>
                            <button @click="startEdit(s)" class="text-xs text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400">
                                Editar
                            </button>
                            <button @click="toggleSchedule(s)"
                                class="text-xs px-2 py-0.5 rounded border"
                                :class="s.enabled ? 'border-yellow-400 text-yellow-600 dark:text-yellow-400' : 'border-green-400 text-green-600 dark:text-green-400'">
                                {{ s.enabled ? 'Pausar' : 'Activar' }}
                            </button>
                            <button @click="deleteSchedule(s.id)" class="text-xs text-red-500 hover:text-red-700">Eliminar</button>
                        </template>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tarea interna -->
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-5 mb-5">
            <div class="flex items-start justify-between mb-3">
                <div>
                    <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tarea interna — Verificación de salud</p>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Verifica conectividad con Redis. El resultado aparece en Jobs.</p>
                </div>
                <button
                    @click="runInternalTask"
                    :disabled="runningInternal"
                    class="px-4 py-2 text-sm font-medium bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 flex-shrink-0"
                >
                    {{ runningInternal ? 'Enviando...' : 'Ejecutar' }}
                </button>
            </div>
            <p v-if="internalTaskId" class="text-xs font-mono text-gray-400 mt-2">
                Enviado — task_id: {{ internalTaskId }}
            </p>
        </div>

        <!-- Comandos externos (watchdog) -->
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-5">
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Comandos externos — Watchdog</p>

            <div class="space-y-3">
                <!-- system_info -->
                <div class="flex items-center justify-between px-4 py-3 rounded-lg border border-gray-100 dark:border-gray-700">
                    <div>
                        <p class="text-sm font-medium text-gray-800 dark:text-gray-200">Información del sistema</p>
                        <p class="text-xs text-gray-400">Plataforma, Python, hostname del agente</p>
                    </div>
                    <button
                        @click="runCommand('system_info')"
                        :disabled="pendingCommands['system_info']"
                        class="px-3 py-1.5 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
                    >
                        {{ pendingCommands['system_info'] ? 'Ejecutando...' : 'Ejecutar' }}
                    </button>
                </div>

                <!-- ping -->
                <div class="flex items-center justify-between px-4 py-3 rounded-lg border border-gray-100 dark:border-gray-700">
                    <div>
                        <p class="text-sm font-medium text-gray-800 dark:text-gray-200">Ping al agente</p>
                        <p class="text-xs text-gray-400">Verifica conectividad de red desde watchdog</p>
                    </div>
                    <button
                        @click="runCommand('ping', { host: 'redis' })"
                        :disabled="pendingCommands['ping']"
                        class="px-3 py-1.5 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
                    >
                        {{ pendingCommands['ping'] ? 'Ejecutando...' : 'Ejecutar' }}
                    </button>
                </div>

                <!-- echo -->
                <div class="flex items-start justify-between gap-4 px-4 py-3 rounded-lg border border-gray-100 dark:border-gray-700">
                    <div class="flex-1">
                        <p class="text-sm font-medium text-gray-800 dark:text-gray-200">Echo</p>
                        <p class="text-xs text-gray-400 mb-2">Devuelve el payload recibido</p>
                        <input
                            v-model="echoMessage"
                            type="text"
                            placeholder="Mensaje de prueba"
                            class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        />
                    </div>
                    <button
                        @click="runCommand('echo', { message: echoMessage || 'ping' })"
                        :disabled="pendingCommands['echo']"
                        class="mt-6 px-3 py-1.5 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 flex-shrink-0"
                    >
                        {{ pendingCommands['echo'] ? 'Ejecutando...' : 'Ejecutar' }}
                    </button>
                </div>
            </div>

            <!-- Resultados de comandos externos -->
            <div v-if="commandResults.length > 0" class="mt-5 space-y-2">
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Resultados</p>
                <div
                    v-for="result in commandResults"
                    :key="result.command_id"
                    class="rounded-lg border border-gray-100 dark:border-gray-700 p-3"
                >
                    <div class="flex items-center justify-between mb-1">
                        <span class="text-xs font-medium text-gray-600 dark:text-gray-300 capitalize">{{ result.action }}</span>
                        <span
                            class="text-xs px-1.5 py-0.5 rounded"
                            :class="result.status === 'ok' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' : result.status === 'pending' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'"
                        >{{ result.status }}</span>
                    </div>
                    <pre v-if="result.output" class="text-xs bg-gray-50 dark:bg-gray-900 p-2 rounded overflow-x-auto text-gray-700 dark:text-gray-300">{{ JSON.stringify(result.output, null, 2) }}</pre>
                    <p v-else class="text-xs text-gray-400">Esperando resultado...</p>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { watchdogApi } from "@/api/watchdog";
import NotificationBanner from "@/components/NotificationBanner.vue";

const error = ref(null);
const loadingHealth = ref(false);
const health = ref({ overall: null, services: {} });

const schedules = ref([]);
const availableTasks = ref([]);
const showCreateForm = ref(false);
const creating = ref(false);
const newSchedule = ref({ task_key: "", every: 1, period: "hours" });
const editingId = ref(null);
const editEvery = ref(1);
const editPeriod = ref("hours");

const runningInternal = ref(false);
const internalTaskId = ref(null);

const echoMessage = ref("");
const pendingCommands = reactive({});
const commandResults = ref([]);

async function loadSchedules() {
    try {
        const [sRes, tRes] = await Promise.all([
            watchdogApi.getSchedules(),
            watchdogApi.getSchedulableTasks(),
        ]);
        schedules.value = sRes.data;
        availableTasks.value = tRes.data;
    } catch { /* silent */ }
}

async function createSchedule() {
    if (!newSchedule.value.task_key || !newSchedule.value.every) return;
    creating.value = true;
    error.value = null;
    try {
        await watchdogApi.createSchedule(newSchedule.value);
        newSchedule.value = { task_key: "", every: 1, period: "hours" };
        showCreateForm.value = false;
        await loadSchedules();
    } catch (e) {
        error.value = e.response?.data?.detail || "Error al crear la tarea";
    } finally {
        creating.value = false;
    }
}

function startEdit(s) {
    editingId.value = s.id;
    editEvery.value = s.every;
    editPeriod.value = s.period;
}

async function saveEdit(id) {
    try {
        await watchdogApi.updateSchedule(id, { every: editEvery.value, period: editPeriod.value });
        editingId.value = null;
        await loadSchedules();
    } catch (e) {
        error.value = e.response?.data?.detail || "Error al actualizar";
    }
}

async function toggleSchedule(s) {
    try {
        await watchdogApi.updateSchedule(s.id, { enabled: !s.enabled });
        await loadSchedules();
    } catch (e) {
        error.value = e.response?.data?.detail || "Error al cambiar estado";
    }
}

async function deleteSchedule(id) {
    if (!confirm("¿Eliminar esta tarea programada?")) return;
    try {
        await watchdogApi.deleteSchedule(id);
        await loadSchedules();
    } catch (e) {
        error.value = e.response?.data?.detail || "Error al eliminar";
    }
}

async function loadHealth() {
    loadingHealth.value = true;
    error.value = null;
    try {
        const response = await watchdogApi.getHealth();
        health.value = response.data;
    } catch (e) {
        error.value = e.response?.data?.detail || "Error al cargar estado de servicios";
    } finally {
        loadingHealth.value = false;
    }
}

async function runInternalTask() {
    runningInternal.value = true;
    error.value = null;
    internalTaskId.value = null;
    try {
        const response = await watchdogApi.dispatchInternalTask();
        internalTaskId.value = response.data.task_id;
    } catch (e) {
        error.value = e.response?.data?.detail || "Error al ejecutar la tarea";
    } finally {
        runningInternal.value = false;
    }
}

async function runCommand(action, payload = {}) {
    pendingCommands[action] = true;
    error.value = null;

    const entry = reactive({ command_id: null, action, status: "pending", output: null });
    commandResults.value.unshift(entry);

    try {
        const sent = await watchdogApi.sendCommand(action, payload);
        entry.command_id = sent.data.command_id;
        pollResult(entry);
    } catch (e) {
        error.value = e.response?.data?.detail || `Error al ejecutar ${action}`;
        entry.status = "error";
        pendingCommands[action] = false;
    }
}

function pollResult(entry, attempts = 0) {
    if (attempts >= 10) {
        entry.status = "timeout";
        pendingCommands[entry.action] = false;
        return;
    }
    setTimeout(async () => {
        try {
            const res = await watchdogApi.getCommandResult(entry.command_id);
            if (res.status === 202) {
                pollResult(entry, attempts + 1);
            } else {
                entry.status = res.data.status;
                entry.output = res.data.output;
                pendingCommands[entry.action] = false;
            }
        } catch {
            pollResult(entry, attempts + 1);
        }
    }, 800);
}

onMounted(() => { loadHealth(); loadSchedules(); });
</script>
