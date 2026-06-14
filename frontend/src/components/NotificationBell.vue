<template>
    <div class="relative" ref="bellRef">
        <button
            @click="toggle"
            class="relative p-2 rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
            title="Notificaciones"
        >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
            </svg>
            <span
                v-if="unreadCount > 0"
                class="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center"
            >{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
        </button>

        <!-- Dropdown -->
        <div
            v-if="open"
            class="absolute right-0 top-10 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-50"
        >
            <!-- Header -->
            <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-700">
                <span class="text-sm font-medium text-gray-900 dark:text-white">Notificaciones</span>
                <div class="flex items-center gap-3">
                    <button
                        v-if="unreadCount > 0"
                        @click="markAllRead"
                        class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
                    >Leer todas</button>
                    <button
                        v-if="hasRead"
                        @click="clearRead"
                        class="text-xs text-red-500 dark:text-red-400 hover:underline"
                    >Limpiar leídas</button>
                </div>
            </div>

            <!-- Lista -->
            <div class="max-h-80 overflow-y-auto">
                <div v-if="notifications.length === 0" class="px-4 py-6 text-sm text-center text-gray-400">
                    Sin notificaciones
                </div>
                <div
                    v-for="n in notifications"
                    :key="n.id"
                    class="px-4 py-3 border-b border-gray-50 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    :class="[
                        !n.is_read ? 'bg-indigo-50 dark:bg-indigo-950' : '',
                        n.action_url ? 'cursor-pointer' : 'cursor-default',
                    ]"
                    @click="handleClick(n)"
                >
                    <div class="flex items-start gap-2">
                        <span
                            class="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0"
                            :class="!n.is_read ? 'bg-indigo-500' : 'bg-transparent'"
                        ></span>
                        <div class="min-w-0 flex-1">
                            <div class="flex items-start justify-between gap-1">
                                <p class="text-sm font-medium text-gray-900 dark:text-white">{{ n.title }}</p>
                                <svg v-if="n.action_url" class="w-3 h-3 text-gray-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                                </svg>
                            </div>
                            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ n.message }}</p>
                            <p class="text-xs text-gray-400 mt-1">{{ formatDate(n.created_at) }}</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Footer con política de retención -->
            <div class="px-4 py-2 border-t border-gray-100 dark:border-gray-700">
                <p class="text-xs text-gray-400 text-center">Leídas se eliminan tras 7 días · máx 20</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { useNotifications } from "@/composables/useNotifications";
import api from "@/api/index";

const router = useRouter();
const { unreadCount, notifications, loadNotifications, markAllRead } = useNotifications();
const open = ref(false);
const bellRef = ref(null);

const hasRead = computed(() => notifications.value.some((n) => n.is_read));

function toggle() {
    open.value = !open.value;
    if (open.value) loadNotifications();
}

async function handleClick(n) {
    if (!n.is_read) {
        try {
            await api.patch(`/api/notifications/${n.id}/read/`);
            n.is_read = true;
            if (unreadCount.value > 0) unreadCount.value--;
        } catch { /* silent */ }
    }
    if (n.action_url) {
        open.value = false;
        router.push(n.action_url);
    }
}

async function clearRead() {
    try {
        await api.delete("/api/notifications/clear-read/");
        notifications.value = notifications.value.filter((n) => !n.is_read);
    } catch { /* silent */ }
}

function formatDate(iso) {
    if (!iso) return "";
    return new Date(iso).toLocaleString();
}

function onClickOutside(e) {
    if (bellRef.value && !bellRef.value.contains(e.target)) open.value = false;
}

onMounted(() => document.addEventListener("click", onClickOutside));
onUnmounted(() => document.removeEventListener("click", onClickOutside));
</script>
