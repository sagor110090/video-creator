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

const toLocalISOString = (date) => {
    const pad = (num) => (num < 10 ? '0' + num : num);
    const year = date.getFullYear();
    const month = pad(date.getMonth() + 1);
    const day = pad(date.getDate());
    const hours = pad(date.getHours());
    const minutes = pad(date.getMinutes());
    return `${year}-${month}-${day}T${hours}:${minutes}`;
};

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
                <div @click="emit('close')" class="fixed inset-0 bg-[#0a0a0a]/90 backdrop-blur-md transition-opacity" aria-hidden="true"></div>

                <!-- This element is to trick browser into centering modal contents. -->
                <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                <div class="relative inline-block align-bottom bg-[#1a1a1a] rounded-sm text-left overflow-hidden shadow-[0_0_50px_rgba(255,170,0,0.2)] transform transition-all sm:my-8 sm:align-middle sm:max-w-lg w-full border border-[#222222] neon-glow-amber">
                    <div class="bg-[#1a1a1a] px-5 py-5">
                        <h3 class="text-lg font-bold text-white mb-4 font-cyber">Schedule Upload</h3>

                        <div class="space-y-4">
                            <!-- Quick Schedule Options -->
                            <div>
                                <label class="block text-[#a0a0a0] text-xs font-semibold mb-2">Quick Schedule</label>
                                <div class="grid grid-cols-2 gap-2">
                                    <button v-for="(option, index) in quickScheduleOptions" :key="index"
                                            @click="selectQuickSchedule(option)"
                                            class="px-2.5 py-2 bg-[#222222] hover:bg-[#ffaa00]/20 border border-[#333333] hover:border-[#ffaa00]/50 text-[10px] font-medium text-white hover:text-[#ffaa00] transition-all text-left rounded-sm font-terminal">
                                        {{ option.label }}
                                    </button>
                                </div>
                            </div>

                            <!-- Scheduled Time -->
                            <div>
                                <label class="block text-[#a0a0a0] text-xs font-semibold mb-2">Date & Time</label>
                                <div class="relative">
                                    <input v-model="form.scheduled_for" type="datetime-local"
                                           class="w-full px-3.5 py-2.5 bg-[#222222] border border-[#333333] rounded-sm focus:border-[#ffaa00] focus:neon-glow-amber outline-none text-xs text-white">
                                    <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                                        <svg class="w-4 h-4 text-[#666666]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                        </svg>
                                    </div>
                                </div>
                                <div class="flex items-center justify-between mt-1.5">
                                    <p class="text-[10px] text-[#666666] font-terminal">{{ timezone }}</p>
                                    <p v-if="form.scheduled_for" class="text-[10px] text-[#ffaa00] font-medium font-cyber">
                                        {{ formatDisplayDate(form.scheduled_for) }}
                                    </p>
                                </div>
                            </div>

                            <!-- Channel Selection -->
                            <div>
                                <label class="block text-[#a0a0a0] text-xs font-semibold mb-2">YouTube Channel</label>
                                <select v-model="form.youtube_token_id"
                                        class="w-full px-3.5 py-2.5 bg-[#222222] border border-[#333333] rounded-sm focus:border-[#ffaa00] focus:neon-glow-amber outline-none text-xs text-white">
                                    <option v-for="channel in channels" :key="channel.id" :value="channel.id">
                                        {{ channel.channel_title }}
                                    </option>
                                </select>
                            </div>

                            <!-- Title -->
                            <div>
                                <label class="block text-[#a0a0a0] text-xs font-semibold mb-2">Video Title</label>
                                <input v-model="form.youtube_title" type="text"
                                       class="w-full px-3.5 py-2.5 bg-[#222222] border border-[#333333] rounded-sm focus:border-[#ffaa00] focus:neon-glow-amber outline-none text-xs text-white"
                                       placeholder="Enter video title...">
                            </div>
                        </div>
                    </div>

                    <div class="bg-[#0a0a0a]/80 px-5 py-4 flex flex-row-reverse space-x-2 space-x-reverse border-t border-[#222222]">
                        <button @click="confirm"
                                class="cyber-btn flex-1 py-2.5 font-bold flex items-center justify-center space-x-1.5">
                            <span>Schedule</span>
                        </button>
                        <button @click="emit('close')"
                                class="flex-1 bg-[#1a1a1a] hover:bg-[#222222] text-white font-bold py-2.5 px-6 border border-[#333333] hover:border-[#ffaa00]/50 rounded-sm transition-all">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>
