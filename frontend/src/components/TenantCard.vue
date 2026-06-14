<template>
    <div class="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-lg transition-shadow">
        <div class="flex justify-between items-start">
            <div>
                <h3 class="text-lg font-medium text-gray-900">{{ tenant.name }}</h3>
                <p class="text-sm text-gray-500">{{ tenant.slug }}</p>
            </div>
            <span
                v-if="tenant.is_active"
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
            >
                Active
            </span>
            <span
                v-else
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
            >
                Inactive
            </span>
        </div>
        <div class="mt-4 flex justify-between items-center text-sm text-gray-500">
            <span>{{ memberCount || 0 }} members</span>
            <span class="text-indigo-600">View details →</span>
        </div>
    </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
    tenant: {
        type: Object,
        required: true,
    },
    memberCount: {
        type: Number,
        default: 0,
    },
});
</script>
