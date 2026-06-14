<template>
    <div>
        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Suscriptores Telegram</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    Los usuarios se suscriben enviando <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">/start</code> al bot.
                </p>
            </div>
            <span class="text-sm text-gray-500">{{ subscribers.length }} activos</span>
        </div>

        <!-- Instrucciones del bot -->
        <div class="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <p class="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">Comandos del bot</p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-1 text-xs text-blue-700 dark:text-blue-400 font-mono">
                <span>/start — suscribirse (todos los departamentos, nivel ≥2)</span>
                <span>/suscribir &lt;depto&gt; &lt;nivel&gt; — filtrar</span>
                <span>/alertas — ver alertas activas ahora</span>
                <span>/estado — ver suscripción actual</span>
                <span>/cancelar — cancelar suscripción</span>
            </div>
        </div>

        <div v-if="loading" class="text-center py-12 text-gray-500">Cargando suscriptores...</div>

        <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <table v-if="subscribers.length" class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-700">
                    <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Usuario</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Chat ID</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Departamento</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Nivel mín.</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Desde</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                    <tr v-for="sub in subscribers" :key="sub.id" class="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                            {{ sub.username ? '@' + sub.username : '—' }}
                        </td>
                        <td class="px-4 py-3 text-sm font-mono text-gray-500">{{ sub.chat_id }}</td>
                        <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                            {{ sub.department || '— todos —' }}
                        </td>
                        <td class="px-4 py-3">
                            <span class="inline-flex px-2 py-0.5 rounded-full text-xs font-semibold text-white"
                                :style="{ background: levelColor(sub.min_level) }">
                                Nivel {{ sub.min_level }}
                            </span>
                        </td>
                        <td class="px-4 py-3 text-sm text-gray-500">
                            {{ new Date(sub.created_at).toLocaleDateString('es-PE') }}
                        </td>
                    </tr>
                </tbody>
            </table>
            <div v-else class="p-8 text-center text-gray-500">
                Sin suscriptores activos. Los usuarios deben enviar <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">/start</code> al bot de Telegram.
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { api } from "@/api/index";

const subscribers = ref([]);
const loading = ref(true);

const COLORS = { 1: "#22c55e", 2: "#eab308", 3: "#f97316", 4: "#ef4444" };
function levelColor(level) { return COLORS[level] || "#6b7280"; }

onMounted(async () => {
    try {
        const res = await api.get("/api/weather/telegram/subscriptions/");
        subscribers.value = res.data.results ?? res.data;
    } finally {
        loading.value = false;
    }
});
</script>
