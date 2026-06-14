<template>
    <div class="max-w-5xl">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-1">Gestión de Usuarios</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
            Administra usuarios e invitaciones.
            <span v-if="!configStore.allowSelfRegistration"
                  class="ml-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/30
                         text-amber-700 dark:text-amber-400 text-xs font-medium">
                Registro cerrado — solo por invitación
            </span>
        </p>

        <!-- Toast -->
        <div v-if="toast"
             class="mb-4 p-3 rounded-lg flex items-center gap-2 text-sm"
             :class="toast.type === 'ok'
                ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400'
                : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400'">
            {{ toast.msg }}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

            <!-- Invitar usuario -->
            <div class="lg:col-span-1">
                <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
                    <h2 class="text-sm font-semibold text-gray-900 dark:text-white mb-4">Invitar usuario</h2>
                    <form @submit.prevent="sendInvitation" class="space-y-3">
                        <div>
                            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Correo electrónico</label>
                            <input v-model="inviteEmail" type="email" required
                                placeholder="nuevo@usuario.com"
                                class="block w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-900 dark:text-white
                                       shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm transition-colors" />
                        </div>
                        <button type="submit" :disabled="inviting"
                            class="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg
                                   bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium
                                   disabled:opacity-60 disabled:cursor-not-allowed transition-colors">
                            <svg v-if="inviting" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                            </svg>
                            {{ inviting ? "Enviando..." : "Enviar invitación" }}
                        </button>
                    </form>

                    <!-- Invitaciones pendientes -->
                    <div class="mt-5 border-t border-gray-100 dark:border-gray-700 pt-4">
                        <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
                            Invitaciones ({{ invitations.length }})
                        </h3>
                        <div v-if="loadingInv" class="text-xs text-gray-400 py-2">Cargando...</div>
                        <div v-else-if="!invitations.length" class="text-xs text-gray-400 py-2">Sin invitaciones.</div>
                        <ul v-else class="space-y-2">
                            <li v-for="inv in invitations" :key="inv.id"
                                class="flex items-start justify-between gap-2 text-xs">
                                <div class="min-w-0">
                                    <p class="font-medium text-gray-800 dark:text-gray-200 truncate">{{ inv.email }}</p>
                                    <p class="text-gray-400">{{ inv.created_at.slice(0, 10) }}</p>
                                </div>
                                <div class="flex items-center gap-2 shrink-0">
                                    <span class="inline-flex px-1.5 py-0.5 rounded text-xs font-medium"
                                          :class="{
                                              'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400': inv.status === 'accepted',
                                              'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400': inv.status === 'pending',
                                              'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400': inv.status === 'expired',
                                          }">
                                        {{ inv.status === 'accepted' ? 'Aceptada' : inv.status === 'pending' ? 'Pendiente' : 'Expirada' }}
                                    </span>
                                    <button v-if="inv.status === 'pending'"
                                        @click="cancelInvitation(inv.id)"
                                        class="text-gray-400 hover:text-red-500 transition-colors"
                                        title="Cancelar invitación">
                                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                                        </svg>
                                    </button>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Lista de usuarios -->
            <div class="lg:col-span-2">
                <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <div class="px-5 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
                        <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
                            Usuarios ({{ users.length }})
                        </h2>
                        <input v-model="search" type="search" placeholder="Buscar por email..."
                            class="text-sm rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-900 dark:text-white
                                   shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-1.5 pl-3 pr-3 w-52 transition-colors" />
                    </div>

                    <div v-if="loadingUsers" class="p-8 text-center text-sm text-gray-400">Cargando usuarios...</div>

                    <table v-else class="min-w-full divide-y divide-gray-100 dark:divide-gray-700">
                        <thead class="bg-gray-50 dark:bg-gray-900/50">
                            <tr>
                                <th class="px-5 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Email</th>
                                <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Estado</th>
                                <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Rol</th>
                                <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Alta</th>
                                <th class="px-3 py-3"></th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
                            <tr v-if="!filteredUsers.length">
                                <td colspan="5" class="px-5 py-6 text-center text-sm text-gray-400">Sin resultados.</td>
                            </tr>
                            <tr v-for="u in filteredUsers" :key="u.id"
                                class="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                                <td class="px-5 py-3 text-sm text-gray-800 dark:text-gray-200 font-medium">{{ u.email }}</td>
                                <td class="px-3 py-3">
                                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                                          :class="u.is_active
                                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                            : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'">
                                        {{ u.is_active ? "Activo" : "Inactivo" }}
                                    </span>
                                </td>
                                <td class="px-3 py-3 text-xs text-gray-500 dark:text-gray-400">
                                    <span v-if="u.is_superuser"
                                          class="px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 font-medium">
                                        Superadmin
                                    </span>
                                    <span v-else>Usuario</span>
                                </td>
                                <td class="px-3 py-3 text-xs text-gray-400">{{ u.date_joined.slice(0, 10) }}</td>
                                <td class="px-3 py-3 text-right">
                                    <button v-if="!u.is_superuser"
                                        @click="toggleUser(u)"
                                        :title="u.is_active ? 'Desactivar' : 'Activar'"
                                        class="text-xs px-2.5 py-1 rounded-md border transition-colors"
                                        :class="u.is_active
                                            ? 'border-red-200 text-red-600 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-900/20'
                                            : 'border-green-200 text-green-600 hover:bg-green-50 dark:border-green-800 dark:text-green-400 dark:hover:bg-green-900/20'">
                                        {{ u.is_active ? "Desactivar" : "Activar" }}
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { api } from "@/api/index";
import { useConfigStore } from "@/stores/config";

const configStore = useConfigStore();

const users = ref([]);
const invitations = ref([]);
const loadingUsers = ref(true);
const loadingInv = ref(true);
const inviteEmail = ref("");
const inviting = ref(false);
const search = ref("");
const toast = ref(null);

const filteredUsers = computed(() => {
    const q = search.value.trim().toLowerCase();
    if (!q) return users.value;
    return users.value.filter(u => u.email.toLowerCase().includes(q));
});

function showToast(msg, type = "ok") {
    toast.value = { msg, type };
    setTimeout(() => { toast.value = null; }, 4000);
}

async function loadUsers() {
    loadingUsers.value = true;
    try {
        const { data } = await api.get("/api/users/list/");
        users.value = data.results;
    } catch {
        showToast("Error al cargar usuarios.", "err");
    } finally {
        loadingUsers.value = false;
    }
}

async function loadInvitations() {
    loadingInv.value = true;
    try {
        const { data } = await api.get("/api/users/invitations/list/");
        invitations.value = data.results;
    } catch {
        // silencioso
    } finally {
        loadingInv.value = false;
    }
}

async function sendInvitation() {
    inviting.value = true;
    try {
        await api.post("/api/users/invitations/", { email: inviteEmail.value });
        inviteEmail.value = "";
        showToast(`Invitación enviada.`);
        await loadInvitations();
    } catch (err) {
        const msg = err.response?.data?.detail || "Error al enviar la invitación.";
        showToast(msg, "err");
    } finally {
        inviting.value = false;
    }
}

async function cancelInvitation(id) {
    try {
        await api.delete(`/api/users/invitations/list/?id=${id}`);
        showToast("Invitación cancelada.");
        invitations.value = invitations.value.filter(i => i.id !== id);
    } catch {
        showToast("Error al cancelar la invitación.", "err");
    }
}

async function toggleUser(u) {
    try {
        const { data } = await api.patch(`/api/users/${u.id}/toggle/`);
        u.is_active = data.is_active;
        showToast(`Usuario ${data.is_active ? "activado" : "desactivado"}.`);
    } catch (err) {
        showToast(err.response?.data?.detail || "Error al cambiar estado.", "err");
    }
}

onMounted(() => {
    loadUsers();
    loadInvitations();
});
</script>
