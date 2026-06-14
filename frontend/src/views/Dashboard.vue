<template>
    <div>
        <div class="flex items-center justify-between mb-6">
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        </div>

        <div v-if="loading" class="text-center py-12 text-gray-400 dark:text-gray-500">
            Cargando widgets...
        </div>

        <div v-else-if="visibleWidgets.length === 0" class="text-center py-12 text-gray-400 dark:text-gray-500">
            No hay widgets activos.
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <component
                v-for="widget in visibleWidgets"
                :key="widget.id"
                :is="resolveComponent(widget.vue_component)"
            />
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, defineAsyncComponent } from "vue";
import { dashboardApi } from "@/api/dashboard.js";

// Auto-discover widgets from Ximbra (components/widgets/) y módulos Vigilo (modules/*/widgets/)
const _coreWidgets = import.meta.glob('../components/widgets/*.vue')
const _moduleWidgets = import.meta.glob('../modules/*/widgets/*.vue')
const WIDGET_COMPONENTS = Object.fromEntries(
    Object.entries({ ..._coreWidgets, ..._moduleWidgets }).map(([path, loader]) => {
        const name = path.split('/').pop().replace('.vue', '')
        return [name, defineAsyncComponent(loader)]
    })
);

const widgets = ref([]);
const loading = ref(true);

const visibleWidgets = computed(() =>
    widgets.value
        .filter(w => w.is_visible)
        .sort((a, b) => a.position - b.position)
);

function resolveComponent(name) {
    return WIDGET_COMPONENTS[name] ?? null;
}

onMounted(async () => {
    try {
        const res = await dashboardApi.getWidgets();
        widgets.value = res.data;
    } catch { /* widget list unavailable */ }
    loading.value = false;
});
</script>
