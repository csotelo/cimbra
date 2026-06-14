<template>
    <div class="min-h-screen flex items-center justify-center p-4 transition-colors duration-300"
         :class="isDark ? 'bg-gray-950' : 'bg-gradient-to-br from-slate-100 via-indigo-50 to-slate-100'">

        <!-- Patrón de fondo decorativo -->
        <div class="absolute inset-0 overflow-hidden pointer-events-none">
            <div class="absolute -top-40 -right-40 w-96 h-96 rounded-full opacity-20 blur-3xl"
                 :class="isDark ? 'bg-indigo-500' : 'bg-indigo-300'"></div>
            <div class="absolute -bottom-40 -left-40 w-96 h-96 rounded-full opacity-20 blur-3xl"
                 :class="isDark ? 'bg-violet-500' : 'bg-violet-300'"></div>
        </div>

        <div class="relative w-full max-w-md">
            <!-- Card -->
            <div class="rounded-2xl shadow-2xl p-8 transition-colors duration-300"
                 :class="isDark ? 'bg-gray-900 border border-gray-800' : 'bg-white'">

                <!-- Toggle dark mode -->
                <div class="flex justify-end mb-2">
                    <button @click="toggleDark" class="p-1.5 rounded-lg transition-colors"
                            :class="isDark
                                ? 'text-gray-400 hover:text-yellow-400 hover:bg-gray-800'
                                : 'text-gray-400 hover:text-indigo-600 hover:bg-gray-100'">
                        <svg v-if="isDark" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 7a5 5 0 100 10A5 5 0 0012 7z"/>
                        </svg>
                        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
                        </svg>
                    </button>
                </div>

                <!-- Logo + Brand -->
                <div class="text-center mb-8">
                    <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4 shadow-lg"
                         :class="isDark ? 'bg-indigo-600' : 'bg-indigo-600'">
                        <svg class="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                        </svg>
                    </div>
                    <h1 class="text-2xl font-bold tracking-tight"
                        :class="isDark ? 'text-white' : 'text-gray-900'">Ximbra</h1>
                    <p class="text-xs mt-1" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                        Sistema de Alertas de Tormentas Eléctricas
                    </p>
                </div>

                <!-- Slot de contenido -->
                <slot />
            </div>

            <!-- Footer -->
            <p class="text-center text-xs mt-4" :class="isDark ? 'text-gray-600' : 'text-gray-400'">
                © {{ new Date().getFullYear() }} Ximbra. Todos los derechos reservados.
            </p>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

const isDark = ref(false);

onMounted(() => {
    isDark.value = localStorage.getItem("theme") === "dark" ||
        (!localStorage.getItem("theme") && window.matchMedia("(prefers-color-scheme: dark)").matches);
    applyTheme();
});

function toggleDark() {
    isDark.value = !isDark.value;
    localStorage.setItem("theme", isDark.value ? "dark" : "light");
    applyTheme();
}

function applyTheme() {
    document.documentElement.classList.toggle("dark", isDark.value);
}
</script>
