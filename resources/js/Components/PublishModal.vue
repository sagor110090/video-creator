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
                <div @click="emit('close')" class="fixed inset-0 bg-[#0a0a0a]/90 backdrop-blur-md transition-opacity" aria-hidden="true"></div>

                <!-- This element is to trick browser into centering modal contents. -->
                <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                <!-- Modal panel -->
                <div class="inline-block align-bottom bg-[#1a1a1a] rounded-sm text-left overflow-hidden shadow-[0_0_50px_rgba(0,240,255,0.2)] transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full relative z-10 border border-[#222222] neon-glow-cyan">
                    <div class="bg-[#1a1a1a] px-5 pt-5 pb-5">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-xl font-bold text-white font-cyber" id="modal-title">Publish to YouTube</h3>
                        <button @click="emit('close')" class="text-[#666666] hover:text-[#00f0ff] transition-colors">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                        </button>
                    </div>

                    <div class="space-y-4">
                        <!-- Error Message -->
                        <div v-if="story?.youtube_error" class="p-3 bg-[#1a1a1a] border border-[#ff00ff]/30 rounded-sm flex items-start space-x-2">
                            <svg class="w-4 h-4 text-[#ff00ff] mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <div>
                                <h4 class="text-xs font-bold text-[#ff00ff]">Previous Upload Failed</h4>
                                <p class="text-[10px] text-[#666666] mt-1 leading-relaxed font-terminal">{{ story.youtube_error }}</p>
                            </div>
                        </div>

                        <!-- Channel Selection -->
                        <div>
                            <label class="block text-[#a0a0a0] text-xs font-semibold mb-2">Select Channel</label>
                            <div class="grid grid-cols-2 gap-2">
                                <div v-for="channel in channels" :key="channel.id"
                                     @click="form.youtube_token_id = channel.id"
                                     :class="['flex items-center p-2.5 border rounded-sm cursor-pointer transition-all',
                                              form.youtube_token_id === channel.id ? 'border-[#ff0000] bg-[#1a1a1a] neon-glow-magenta' : 'bg-[#222222] border-[#333333] hover:border-[#ff0000]/50']">
                                    <img :src="channel.channel_thumbnail" class="w-7 h-7 rounded-full mr-2">
                                    <span class="text-[10px] font-bold truncate text-white font-terminal">{{ channel.channel_title }}</span>
                                </div>
                            </div>
                        </div>

                        <!-- Title -->
                        <div>
                            <label class="block text-[#a0a0a0] text-xs font-semibold mb-2">YouTube Title</label>
                            <input v-model="form.youtube_title" type="text"
                                   class="w-full px-3.5 py-2.5 bg-[#222222] border border-[#333333] rounded-sm focus:border-[#00f0ff] focus:neon-glow-cyan outline-none transition-all text-white text-xs placeholder:text-[#666666]"
                                   placeholder="Enter a catchy title...">
                        </div>

                        <!-- Tags -->
                        <div>
                            <label class="block text-[#a0a0a0] text-xs font-semibold mb-2">Tags (comma separated)</label>
                            <input v-model="form.youtube_tags" type="text"
                                   class="w-full px-3.5 py-2.5 bg-[#222222] border border-[#333333] rounded-sm focus:border-[#00f0ff] focus:neon-glow-cyan outline-none transition-all text-white text-xs placeholder:text-[#666666]"
                                   placeholder="ai, story, animation...">
                        </div>

                        <!-- Description -->
                        <div>
                            <label class="block text-[#a0a0a0] text-xs font-semibold mb-2">Description</label>
                            <textarea v-model="form.youtube_description" rows="3"
                                      class="w-full px-3.5 py-2.5 bg-[#222222] border border-[#333333] rounded-sm focus:border-[#00f0ff] focus:neon-glow-cyan outline-none transition-all text-xs text-white placeholder:text-[#666666]"
                                      placeholder="Enter video description..."></textarea>
                        </div>
                    </div>
                </div>

                <div class="bg-[#0a0a0a]/80 px-5 py-4 flex flex-row-reverse space-x-2 space-x-reverse border-t border-[#222222]">
                    <button @click="confirm"
                            class="cyber-btn flex-1 py-2.5 font-bold flex items-center justify-center space-x-1.5">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                        <span>Start Upload</span>
                    </button>
                    <button @click="emit('close')"
                            class="flex-1 bg-[#1a1a1a] hover:bg-[#222222] text-white font-bold py-2.5 px-6 border border-[#333333] hover:border-[#00f0ff]/50 rounded-sm transition-all">
                        Cancel
                    </button>
                </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>
