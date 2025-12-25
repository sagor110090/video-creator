<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
    show: Boolean,
    story: Object,
    channels: Array
});

const emit = defineEmits(['close', 'confirm']);

const form = ref({
    youtube_title: '',
    youtube_description: '',
    youtube_tags: '',
    youtube_token_id: null
});

watch(() => props.story, (newStory) => {
    if (newStory) {
        form.value = {
            youtube_title: newStory.youtube_title || newStory.title || '',
            youtube_description: newStory.youtube_description || newStory.content || '',
            youtube_tags: newStory.youtube_tags || 'ai, story, animation',
            youtube_token_id: newStory.youtube_token_id || (props.channels.length > 0 ? props.channels[0].id : null)
        };
    }
}, { immediate: true });

const confirm = () => {
    emit('confirm', { ...form.value });
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

                <!-- Modal panel -->
                <div class="inline-block align-bottom bg-white dark:bg-slate-900 rounded-3xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full relative z-10">
                    <div class="bg-white dark:bg-slate-900 px-6 pt-6 pb-8">
                    <div class="flex items-center justify-between mb-6">
                        <h3 class="text-2xl font-bold text-slate-900 dark:text-white" id="modal-title">Publish to YouTube</h3>
                        <button @click="emit('close')" class="text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                        </button>
                    </div>

                    <div class="space-y-5">
                        <!-- Channel Selection -->
                        <div>
                            <label class="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-2">Select Channel</label>
                            <div class="grid grid-cols-2 gap-3">
                                <div v-for="channel in channels" :key="channel.id"
                                     @click="form.youtube_token_id = channel.id"
                                     :class="['flex items-center p-3 border rounded-xl cursor-pointer transition-all',
                                              form.youtube_token_id === channel.id ? 'border-red-500 bg-red-50 dark:bg-red-900/20 ring-2 ring-red-100 dark:ring-red-900/40' : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-red-300']">
                                    <img :src="channel.channel_thumbnail" class="w-8 h-8 rounded-full shadow-sm mr-3">
                                    <span class="text-xs font-bold truncate text-slate-700 dark:text-slate-300">{{ channel.channel_title }}</span>
                                </div>
                            </div>
                        </div>

                        <!-- Title -->
                        <div>
                            <label class="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-2">YouTube Title</label>
                            <input v-model="form.youtube_title" type="text"
                                   class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 transition-all text-slate-900 dark:text-white placeholder:text-slate-400"
                                   placeholder="Enter a catchy title...">
                        </div>

                        <!-- Tags -->
                        <div>
                            <label class="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-2">Tags (comma separated)</label>
                            <input v-model="form.youtube_tags" type="text"
                                   class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 transition-all text-slate-900 dark:text-white placeholder:text-slate-400"
                                   placeholder="ai, story, animation...">
                        </div>

                        <!-- Description -->
                        <div>
                            <label class="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-2">Description</label>
                            <textarea v-model="form.youtube_description" rows="4"
                                      class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 transition-all text-sm text-slate-900 dark:text-white placeholder:text-slate-400"
                                      placeholder="Enter video description..."></textarea>
                        </div>
                    </div>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800/50 px-6 py-4 flex flex-row-reverse space-x-3 space-x-reverse">
                    <button @click="confirm"
                            class="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg shadow-red-100 dark:shadow-none flex items-center justify-center space-x-2">
                        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                        <span>Start Upload</span>
                    </button>
                    <button @click="emit('close')"
                            class="flex-1 bg-white hover:bg-slate-50 text-slate-700 font-bold py-3 px-6 rounded-xl border border-slate-200 transition-all">
                        Cancel
                    </button>
                </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>
