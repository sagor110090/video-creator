<script setup>
import { ref, watch, computed } from 'vue';

const props = defineProps({
    show: Boolean,
    story: Object,
    channels: Array
});

const emit = defineEmits(['close', 'confirm']);

const form = ref({
    scheduled_for: '',
    youtube_title: '',
    youtube_description: '',
    youtube_tags: '',
    youtube_token_id: null
});

const timezone = ref(Intl.DateTimeFormat().resolvedOptions().timeZone);

// Quick schedule options
const quickScheduleOptions = [
    { label: 'Tomorrow 9:00 AM', value: () => {
        const date = new Date();
        date.setDate(date.getDate() + 1);
        date.setHours(9, 0, 0, 0);
        return toLocalISOString(date);
    }},
    { label: 'Tomorrow 12:00 PM', value: () => {
        const date = new Date();
        date.setDate(date.getDate() + 1);
        date.setHours(12, 0, 0, 0);
        return toLocalISOString(date);
    }},
    { label: 'Tomorrow 6:00 PM', value: () => {
        const date = new Date();
        date.setDate(date.getDate() + 1);
        date.setHours(18, 0, 0, 0);
        return toLocalISOString(date);
    }},
    { label: 'Next Monday 9:00 AM', value: () => {
        const date = new Date();
        const day = date.getDay();
        const diff = 1 - day + (day === 0 ? 7 : 0);
        date.setDate(date.getDate() + diff + 7);
        date.setHours(9, 0, 0, 0);
        return toLocalISOString(date);
    }},
    { label: 'Next Friday 6:00 PM', value: () => {
        const date = new Date();
        const day = date.getDay();
        const diff = 5 - day + (day === 0 ? 7 : 0);
        date.setDate(date.getDate() + diff + 7);
        date.setHours(18, 0, 0, 0);
        return toLocalISOString(date);
    }}
];

// Format date to local datetime-local string (YYYY-MM-DDTHH:mm)
const toLocalISOString = (date) => {
    const pad = (num) => (num < 10 ? '0' + num : num);
    const year = date.getFullYear();
    const month = pad(date.getMonth() + 1);
    const day = pad(date.getDate());
    const hours = pad(date.getHours());
    const minutes = pad(date.getMinutes());
    return `${year}-${month}-${day}T${hours}:${minutes}`;
};

// Format date for display
const formatDisplayDate = (dateString) => {
    if (!dateString) return 'Not scheduled';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
    });
};

watch(() => props.story, (newStory) => {
    if (newStory) {
        form.value = {
            scheduled_for: newStory.scheduled_for ? newStory.scheduled_for.slice(0, 16) : '',
            youtube_title: newStory.youtube_title || newStory.title || '',
            youtube_description: newStory.youtube_description || newStory.content || '',
            youtube_tags: newStory.youtube_tags || 'ai, story, animation',
            youtube_token_id: newStory.youtube_token_id || (props.channels.length > 0 ? props.channels[0].id : null)
        };

        // If no scheduled time, set default to tomorrow 9 AM
        if (!form.value.scheduled_for) {
             const tomorrow = new Date();
             tomorrow.setDate(tomorrow.getDate() + 1);
             tomorrow.setHours(9, 0, 0, 0);
             form.value.scheduled_for = toLocalISOString(tomorrow);
        }
    }
}, { immediate: true });

const confirm = () => {
    emit('confirm', { ...form.value });
};

const selectQuickSchedule = (option) => {
    form.value.scheduled_for = option.value();
};
</script>

<template>
    <Teleport to="body">
        <div v-if="show" class="fixed inset-0 z-[100] overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <!-- Background overlay -->
                <div @click="emit('close')" class="fixed inset-0 bg-slate-900/75 backdrop-blur-sm transition-opacity" aria-hidden="true"></div>

                <!-- This element is to trick the browser into centering the modal contents. -->
                <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                <div class="relative inline-block align-bottom bg-white dark:bg-slate-900 rounded-2xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg w-full">
                    <div class="bg-white dark:bg-slate-900 px-6 py-6">
                        <h3 class="text-xl font-bold text-slate-900 dark:text-white mb-6">Schedule Upload</h3>

                        <div class="space-y-5">
                            <!-- Quick Schedule Options -->
                            <div>
                                <label class="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-3">Quick Schedule</label>
                                <div class="grid grid-cols-2 gap-2">
                                    <button v-for="(option, index) in quickScheduleOptions" :key="index"
                                            @click="selectQuickSchedule(option)"
                                            class="px-3 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-amber-100 dark:hover:bg-amber-900/30 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:text-amber-700 dark:hover:text-amber-400 transition-all text-left">
                                        {{ option.label }}
                                    </button>
                                </div>
                            </div>

                            <!-- Scheduled Time -->
                            <div>
                                <label class="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-2">Date & Time</label>
                                <div class="relative">
                                    <input v-model="form.scheduled_for" type="datetime-local"
                                           class="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all text-sm text-slate-900 dark:text-white">
                                    <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                                        <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                        </svg>
                                    </div>
                                </div>
                                <div class="flex items-center justify-between mt-2">
                                    <p class="text-xs text-slate-500">{{ timezone }}</p>
                                    <p v-if="form.scheduled_for" class="text-xs text-amber-600 dark:text-amber-400 font-medium">
                                        {{ formatDisplayDate(form.scheduled_for) }}
                                    </p>
                                </div>
                            </div>

                            <!-- Channel Selection -->
                            <div>
                                <label class="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-2">YouTube Channel</label>
                                <select v-model="form.youtube_token_id"
                                        class="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all text-sm text-slate-900 dark:text-white">
                                    <option v-for="channel in channels" :key="channel.id" :value="channel.id">
                                        {{ channel.channel_title }}
                                    </option>
                                </select>
                            </div>

                            <!-- Title -->
                            <div>
                                <label class="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-2">Video Title</label>
                                <input v-model="form.youtube_title" type="text"
                                       class="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all text-sm text-slate-900 dark:text-white"
                                       placeholder="Enter video title...">
                            </div>
                        </div>
                    </div>

                    <div class="bg-slate-50 dark:bg-slate-800/50 px-6 py-4 flex flex-row-reverse space-x-3 space-x-reverse">
                        <button @click="confirm"
                                class="flex-1 bg-amber-500 hover:bg-amber-600 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg shadow-amber-100 dark:shadow-none flex items-center justify-center space-x-2">
                            <span>Schedule</span>
                        </button>
                        <button @click="emit('close')"
                                class="flex-1 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold py-3 px-6 rounded-xl border border-slate-200 dark:border-slate-700 transition-all">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>
