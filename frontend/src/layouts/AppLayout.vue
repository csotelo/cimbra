<template>
    <div class="flex h-screen bg-gray-100 dark:bg-gray-900">

        <!-- Sidebar -->
        <aside
            class="sidebar bg-white dark:bg-gray-800 shadow-md flex flex-shrink-0 transition-all duration-300 ease-in-out overflow-hidden"
            :class="sidebarOpen ? 'w-64' : 'w-10'"
        >
            <!-- Strip mínimo siempre visible: botón toggle alineado al header -->
            <div class="flex flex-col flex-shrink-0" :class="sidebarOpen ? 'hidden' : 'w-10 items-center pt-4'">
                <button
                    @click="toggleSidebar"
                    class="w-8 h-8 rounded-md flex items-center justify-center text-gray-400 dark:text-gray-500
                           hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                    title="Expandir menú"
                >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                </button>
            </div>

            <!-- Contenido del sidebar completo -->
            <div v-show="sidebarOpen" class="flex flex-col flex-1 w-64 min-w-0 overflow-hidden">
            <div class="h-16 flex items-center px-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0 gap-3">
                <span class="text-xl font-bold text-gray-900 dark:text-white truncate flex-1">{{ appName }}</span>
                <!-- Botón colapsar dentro del header -->
                <button
                    @click="toggleSidebar"
                    class="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center text-gray-400 dark:text-gray-500
                           hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                    title="Colapsar menú"
                >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
                    </svg>
                </button>
            </div>

            <nav class="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">

                <!-- Items fijos -->
                <router-link to="/dashboard" v-bind="linkProps">Dashboard</router-link>
                <router-link v-if="!singleTenantMode" to="/tenants" v-bind="linkProps">Tenants</router-link>
                <router-link to="/jobs"      v-bind="linkProps">Jobs</router-link>
                <router-link v-if="user?.is_superuser" to="/watchdog" v-bind="linkProps">Watchdog</router-link>

                <!-- Items de módulos sin grupo -->
                <template v-if="standaloneItems.length">
                    <div class="my-2 border-t border-gray-200 dark:border-gray-700" />
                    <router-link
                        v-for="item in standaloneItems"
                        :key="item.name"
                        :to="item.path"
                        v-bind="linkProps"
                    >{{ item.meta.label }}</router-link>
                </template>

                <!-- Grupos colapsables -->
                <template v-if="groupedItems.length">
                    <div class="my-2 border-t border-gray-200 dark:border-gray-700" />
                    <div v-for="group in groupedItems" :key="group.id" class="mb-0.5">

                        <!-- Cabecera del grupo -->
                        <button
                            @click="toggleGroup(group.id)"
                            class="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold uppercase tracking-wider rounded-md
                                   text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            :class="{ 'text-indigo-600 dark:text-indigo-400': isGroupActive(group) }"
                        >
                            <span>{{ group.label }}</span>
                            <svg
                                class="w-3.5 h-3.5 transition-transform duration-200"
                                :class="openGroups.has(group.id) ? 'rotate-90' : ''"
                                fill="none" stroke="currentColor" viewBox="0 0 24 24"
                            >
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                            </svg>
                        </button>

                        <!-- Sub-items -->
                        <div v-show="openGroups.has(group.id)" class="ml-2 mt-0.5 space-y-0.5 border-l-2 border-gray-100 dark:border-gray-700 pl-2">
                            <router-link
                                v-for="item in group.items"
                                :key="item.name"
                                :to="item.path"
                                class="flex items-center px-3 py-1.5 text-sm rounded-md text-gray-600 dark:text-gray-400
                                       hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white transition-colors"
                                active-class="bg-indigo-50 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300 font-medium"
                            >
                                {{ item.meta.label }}
                            </router-link>
                        </div>
                    </div>
                </template>

            </nav>
            </div><!-- fin contenido sidebar -->
        </aside>

        <!-- Panel derecho -->
        <div class="flex-1 flex flex-col overflow-hidden">

            <!-- Header -->
            <header class="h-16 bg-white dark:bg-gray-800 shadow-sm flex items-center justify-end px-6 space-x-4 flex-shrink-0">

                <button
                    @click="toggleDark"
                    class="p-2 rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                    :title="isDark ? 'Modo claro' : 'Modo oscuro'"
                >
                    <svg v-if="isDark" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 7a5 5 0 100 10A5 5 0 0012 7z"/>
                    </svg>
                    <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
                    </svg>
                </button>

                <NotificationBell />
                <div class="h-6 w-px bg-gray-200 dark:bg-gray-600"></div>

                <div class="flex items-center space-x-3">
                    <router-link
                        to="/profile"
                        class="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400"
                    >
                        <div class="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
                            <span class="text-xs font-medium text-indigo-700 dark:text-indigo-300">{{ userInitial }}</span>
                        </div>
                        <span class="hidden md:block">{{ user?.email }}</span>
                    </router-link>

                    <button
                        @click="logout"
                        class="p-2 rounded-md text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                        title="Cerrar sesión"
                    >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                        </svg>
                    </button>
                </div>
            </header>

            <main class="main-content flex-1 overflow-y-auto p-6">
                <router-view />
            </main>
        </div>

        <ToastContainer />
    </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuth } from "@/composables/useAuth";
import { useNotifications } from "@/composables/useNotifications";
import { useConfigStore } from "@/stores/config";
import { useHead } from "@/composables/useHead";
import NotificationBell from "@/components/NotificationBell.vue";
import ToastContainer from "@/components/ToastContainer.vue";

const { user, logout } = useAuth();
const configStore = useConfigStore();
const singleTenantMode = computed(() => configStore.singleTenantMode);
useHead();

// --- sidebar colapsable ---
const sidebarOpen = ref(localStorage.getItem("sidebar_open") !== "false");
function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value;
    localStorage.setItem("sidebar_open", sidebarOpen.value ? "true" : "false");
}

const linkProps = {
    class: "flex items-center px-3 py-2 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors",
    activeClass: "bg-indigo-50 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300",
};
const router = useRouter();
const route  = useRoute();

const appName = computed(() => configStore.appName || import.meta.env.VITE_APP_NAME || "Ximbra");

// --- estructura de menú ---
const allMenuRoutes = computed(() =>
    router.getRoutes().filter(r => r.meta?.menu)
);

const standaloneItems = computed(() =>
    allMenuRoutes.value
        .filter(r => !r.meta.group)
        .sort((a, b) => (a.meta.order ?? 99) - (b.meta.order ?? 99))
);

const groupedItems = computed(() => {
    const map = {};
    for (const r of allMenuRoutes.value.filter(r => r.meta.group)) {
        const g = r.meta.group;
        if (!map[g]) {
            map[g] = {
                id: g,
                label: r.meta.groupLabel ?? g,
                order: r.meta.groupOrder ?? 99,
                items: [],
            };
        }
        map[g].items.push(r);
    }
    for (const g of Object.values(map)) {
        g.items.sort((a, b) => (a.meta.order ?? 99) - (b.meta.order ?? 99));
    }
    return Object.values(map).sort((a, b) => a.order - b.order);
});

// --- estado abierto/cerrado de grupos ---
// reactive(Set) sí trackea .add() y .delete() — ref(Set) no
const openGroups = reactive(new Set());

function restoreOpenGroups() {
    try {
        const saved = JSON.parse(localStorage.getItem("menu_open_groups") || "[]");
        saved.forEach(id => openGroups.add(id));
    } catch { /* noop */ }
    expandActiveGroup();
}

function expandActiveGroup() {
    const current = route.path;
    for (const group of groupedItems.value) {
        if (group.items.some(i => current.startsWith("/" + i.path))) {
            openGroups.add(group.id);
        }
    }
}

function toggleGroup(id) {
    if (openGroups.has(id)) {
        openGroups.delete(id);
    } else {
        openGroups.add(id);
    }
    localStorage.setItem("menu_open_groups", JSON.stringify([...openGroups]));
}

function isGroupActive(group) {
    const current = route.path;
    return group.items.some(i => current.startsWith("/" + i.path));
}

// expandir grupo activo al navegar
watch(() => route.path, expandActiveGroup);

// --- dark mode ---
const isDark = ref(false);

onMounted(() => {
    isDark.value = localStorage.getItem("theme") === "dark" ||
        (!localStorage.getItem("theme") && window.matchMedia("(prefers-color-scheme: dark)").matches);
    applyTheme();
    restoreOpenGroups();
    configStore.fetchConfig();
});

const { connectWebSocket, disconnect, loadUnreadCount } = useNotifications();

watch(user, (u) => {
    if (u) { loadUnreadCount(); connectWebSocket(u.id); }
    else    { disconnect(); }
}, { immediate: true });

onUnmounted(disconnect);

function toggleDark() {
    isDark.value = !isDark.value;
    localStorage.setItem("theme", isDark.value ? "dark" : "light");
    applyTheme();
}

function applyTheme() {
    document.documentElement.classList.toggle("dark", isDark.value);
}

const userInitial = computed(() => (user.value?.email || "").charAt(0).toUpperCase());
</script>
