<template>
    <div>
        <div v-if="loading" class="text-center py-4">
            <p class="text-sm text-gray-500 dark:text-gray-400">Loading token...</p>
        </div>

        <!-- Token existente -->
        <template v-else-if="token">
            <!-- Mostrar token recién creado -->
            <div v-if="showToken && tokenValue" class="mb-4 p-4 bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 rounded-lg">
                <div class="flex items-start justify-between mb-2">
                    <p class="text-xs font-medium text-green-700 dark:text-green-300">Token generado — cópialo ahora, no se mostrará de nuevo</p>
                    <button @click="showToken = false" class="text-green-600 dark:text-green-400 hover:text-green-800 text-xs">Ocultar</button>
                </div>
                <code class="block text-sm font-mono break-all text-green-900 dark:text-green-100 bg-green-100 dark:bg-green-800 p-2 rounded">{{ tokenValue }}</code>
                <button
                    @click="copyToken"
                    class="mt-2 text-xs text-green-700 dark:text-green-300 hover:text-green-900 font-medium"
                >
                    {{ copied ? '✓ Copiado' : 'Copiar al portapapeles' }}
                </button>
            </div>

            <!-- Info del token -->
            <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg mb-4">
                <div class="space-y-1">
                    <div class="flex items-center space-x-2">
                        <span class="w-2 h-2 rounded-full bg-green-500"></span>
                        <p class="text-sm font-medium text-gray-900 dark:text-white">Token activo</p>
                    </div>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Creado: {{ formatDate(token.created_at) }}</p>
                    <p v-if="token.expires_at" class="text-xs text-gray-500 dark:text-gray-400">Expira: {{ formatDate(token.expires_at) }}</p>
                </div>
                <button
                    v-if="canManage"
                    @click="confirmRevoke"
                    class="px-3 py-1.5 text-sm font-medium text-red-600 dark:text-red-400 border border-red-300 dark:border-red-700 rounded-md hover:bg-red-50 dark:hover:bg-red-900"
                >
                    Revocar
                </button>
            </div>

            <button
                v-if="canManage"
                @click="handleCreate"
                :disabled="creating"
                class="w-full px-4 py-2 text-sm font-medium text-indigo-600 dark:text-indigo-400 border border-indigo-300 dark:border-indigo-700 rounded-md hover:bg-indigo-50 dark:hover:bg-indigo-900 disabled:opacity-50"
            >
                {{ creating ? 'Generando...' : 'Regenerar token' }}
            </button>
        </template>

        <!-- Sin token -->
        <template v-else>
            <div class="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg mb-4 flex items-center space-x-3">
                <span class="w-2 h-2 rounded-full bg-gray-400"></span>
                <p class="text-sm text-gray-500 dark:text-gray-400">Sin token activo. Crea uno para integrar con la API.</p>
            </div>
            <button
                v-if="canManage"
                @click="handleCreate"
                :disabled="creating"
                class="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md disabled:opacity-50"
            >
                {{ creating ? 'Creando...' : 'Crear API Token' }}
            </button>
            <p v-else class="text-sm text-gray-400 dark:text-gray-500 text-center">Solo el owner puede gestionar tokens.</p>
        </template>
    </div>
</template>

<script setup>
import { ref } from "vue";
import { tenantApi } from "@/api/tenant";

const props = defineProps({
    tenantId: { type: [String, Number], required: true },
    canManage: { type: Boolean, default: false },
});

const emit = defineEmits(["error"]);

const token = ref(null);
const tokenValue = ref(null);
const loading = ref(false);
const creating = ref(false);
const showToken = ref(false);
const copied = ref(false);

async function loadToken() {
    loading.value = true;
    try {
        const response = await tenantApi.getToken(props.tenantId);
        token.value = response.data;
    } catch (e) {
        if (e.response?.status !== 404) {
            emit("error", e.response?.data?.detail || "Failed to load token");
        }
    } finally {
        loading.value = false;
    }
}

async function handleCreate() {
    creating.value = true;
    try {
        const response = await tenantApi.createToken(props.tenantId);
        token.value = response.data;
        tokenValue.value = response.data.token || null;
        showToken.value = true;
    } catch (e) {
        emit("error", e.response?.data?.detail || "Failed to create token");
    } finally {
        creating.value = false;
    }
}

function confirmRevoke() {
    if (window.confirm("¿Revocar este token? Las integraciones que lo usen dejarán de funcionar.")) {
        handleRevoke();
    }
}

async function handleRevoke() {
    try {
        await tenantApi.revokeToken(props.tenantId);
        token.value = null;
        tokenValue.value = null;
        showToken.value = false;
    } catch (e) {
        emit("error", e.response?.data?.detail || "Failed to revoke token");
    }
}

async function copyToken() {
    if (!tokenValue.value) return;
    await navigator.clipboard.writeText(tokenValue.value);
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
}

function formatDate(dateStr) {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString();
}

loadToken();
</script>
