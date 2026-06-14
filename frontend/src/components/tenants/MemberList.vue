<template>
    <div>
        <div v-if="loading" class="text-center py-4">
            <p class="text-sm text-gray-500">Loading members...</p>
        </div>

        <div v-else-if="members.length === 0" class="text-center py-4">
            <p class="text-sm text-gray-500">No members found</p>
        </div>

        <div v-else class="space-y-3">
            <div
                v-for="member in members"
                :key="member.user?.id"
                class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                        <span class="text-sm font-medium text-indigo-600">
                            {{ getInitials(member.user) }}
                        </span>
                    </div>
                    <div>
                        <p class="text-sm font-medium text-gray-900">
                            {{ member.user?.email }}
                        </p>
                        <p class="text-xs text-gray-500 capitalize">{{ member.role }}</p>
                    </div>
                </div>
                <div v-if="canManage && member.role !== 'owner'" class="relative">
                    <select
                        :value="member.role"
                        @change="handleRoleChange(member.user.id, $event.target.value)"
                        class="text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    >
                        <option value="member">Member</option>
                        <option value="admin">Admin</option>
                    </select>
                    <button
                        @click="handleRemove(member.user.id)"
                        class="ml-2 text-red-600 hover:text-red-800 text-sm"
                        title="Remove member"
                    >
                        &times;
                    </button>
                </div>
            </div>
        </div>

        <div v-if="canManage" class="mt-4 pt-4 border-t border-gray-200 space-y-2">
            <div v-if="!showAddForm && !showInviteForm" class="flex gap-2">
                <button
                    @click="showAddForm = true"
                    class="flex-1 px-4 py-2 border border-dashed border-gray-300 rounded-lg text-sm text-gray-600 hover:border-gray-400 hover:text-gray-900"
                >
                    + Agregar (usuario existente)
                </button>
                <button
                    @click="showInviteForm = true"
                    class="flex-1 px-4 py-2 border border-dashed border-indigo-300 rounded-lg text-sm text-indigo-600 hover:border-indigo-500 hover:text-indigo-800"
                >
                    ✉ Invitar por email
                </button>
            </div>

            <form v-if="showAddForm" @submit.prevent="handleAddMember" class="space-y-3">
                <input
                    v-model="newMember.email"
                    type="email"
                    placeholder="Email del usuario existente"
                    required
                    class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
                <select
                    v-model="newMember.role"
                    class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                    <option value="member">Member</option>
                    <option value="admin">Admin</option>
                </select>
                <div class="flex space-x-2">
                    <button type="submit" :disabled="adding"
                        class="flex-1 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50">
                        {{ adding ? "Agregando..." : "Agregar" }}
                    </button>
                    <button type="button" @click="cancelAdd"
                        class="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 hover:bg-gray-50">
                        Cancelar
                    </button>
                </div>
            </form>

            <form v-if="showInviteForm" @submit.prevent="handleInvite" class="space-y-3">
                <p class="text-xs text-gray-500">El usuario recibirá un email con un link para crear su cuenta.</p>
                <input
                    v-model="inviteEmail"
                    type="email"
                    placeholder="Email a invitar"
                    required
                    class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
                <div v-if="inviteSuccess" class="text-sm text-green-600">{{ inviteSuccess }}</div>
                <div class="flex space-x-2">
                    <button type="submit" :disabled="inviting"
                        class="flex-1 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50">
                        {{ inviting ? "Enviando..." : "Enviar invitación" }}
                    </button>
                    <button type="button" @click="cancelInvite"
                        class="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 hover:bg-gray-50">
                        Cancelar
                    </button>
                </div>
            </form>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { tenantApi } from "@/api/tenant";
import { api } from "@/api/index";

const props = defineProps({
    tenantId: { type: [String, Number], required: true },
    members: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    canManage: { type: Boolean, default: false },
});

const emit = defineEmits(["refresh", "error"]);

const showAddForm = ref(false);
const adding = ref(false);
const newMember = reactive({ email: "", role: "member" });

const showInviteForm = ref(false);
const inviting = ref(false);
const inviteEmail = ref("");
const inviteSuccess = ref(null);

function getInitials(user) {
    if (!user?.email) return "?";
    return user.email.charAt(0).toUpperCase();
}

function cancelAdd() {
    showAddForm.value = false;
    newMember.email = "";
    newMember.role = "member";
}

function cancelInvite() {
    showInviteForm.value = false;
    inviteEmail.value = "";
    inviteSuccess.value = null;
}

async function handleInvite() {
    inviting.value = true;
    inviteSuccess.value = null;
    try {
        await api.post("/api/users/invitations/", { email: inviteEmail.value });
        inviteSuccess.value = `Invitación enviada a ${inviteEmail.value}`;
        inviteEmail.value = "";
    } catch (e) {
        emit("error", e.response?.data?.detail || "Error al enviar invitación");
    } finally {
        inviting.value = false;
    }
}

async function handleAddMember() {
    adding.value = true;
    try {
        await tenantApi.addMember(props.tenantId, newMember);
        emit("refresh");
        cancelAdd();
    } catch (e) {
        emit("error", e.response?.data?.detail || "Failed to add member");
    } finally {
        adding.value = false;
    }
}

async function handleRemove(userId) {
    if (!confirm("Are you sure you want to remove this member?")) return;
    try {
        await tenantApi.removeMember(props.tenantId, userId);
        emit("refresh");
    } catch (e) {
        emit("error", e.response?.data?.detail || "Failed to remove member");
    }
}

async function handleRoleChange(userId, role) {
    try {
        await tenantApi.changeRole(props.tenantId, userId, role);
        emit("refresh");
    } catch (e) {
        emit("error", e.response?.data?.detail || "Failed to change role");
    }
}
</script>
