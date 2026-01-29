<script setup>
import { ref, watch } from 'vue';
import axios from 'axios';
import { useToast } from 'vue-toast-notification';

const props = defineProps({
    show: Boolean,
    story: Object,
});

const emit = defineEmits(['close', 'refresh']);
const toast = useToast();
const scenes = ref([]);
const loading = ref(false);
const regeneratingId = ref(null);
const savingId = ref(null);

const fetchScenes = async () => {
    if (!props.story) return;
    loading.value = true;
    try {
        const response = await axios.get(`/api/stories/${props.story.id}`);
        scenes.value = response.data.scenes;
    } catch (error) {
        console.error("Failed to fetch scenes", error);
        toast.error("Failed to load scenes");
    } finally {
        loading.value = false;
    }
};

watch(() => props.show, (newVal) => {
    if (newVal) {
        fetchScenes();
    }
});

const saveScene = async (scene) => {
    savingId.value = scene.id;
    try {
        await axios.patch(`/api/scenes/${scene.id}`, {
            narration: scene.narration,
            image_prompt: scene.image_prompt
        });
        toast.success("Scene saved successfully");
    } catch (error) {
        console.error("Failed to save scene", error);
        toast.error("Failed to save scene");
    } finally {
        savingId.value = null;
    }
};

const regenerateScene = async (scene) => {
    if (!confirm("Are you sure? This will delete current scene files and regenerate them.")) return;

    regeneratingId.value = scene.id;
    try {
        await axios.post(`/api/scenes/${scene.id}/regenerate`, {
            narration: scene.narration,
            image_prompt: scene.image_prompt
        });
        toast.success("Scene regeneration started. Video will update shortly.");
        emit('refresh');
    } catch (error) {
        console.error("Failed to regenerate", error);
        toast.error("Failed to start regeneration");
    } finally {
        regeneratingId.value = null;
    }
};

const getSceneImage = (scene) => {
    return `/storage/videos/${props.story.id}/scene_${scene.order}_img.jpg?t=${new Date().getTime()}`;
};

const getSceneVideo = (scene) => {
    return `/storage/videos/${props.story.id}/scene_${scene.order}_vid.mp4?t=${new Date().getTime()}`;
};

</script>

<template>
    <Teleport to="body">
        <div v-if="show" class="fixed inset-0 z-[100] overflow-y-auto" role="dialog" aria-modal="true">
             <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div @click="emit('close')" class="fixed inset-0 bg-[#0a0a0a]/90 backdrop-blur-md transition-opacity"></div>
                <span class="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

                <div class="inline-block align-bottom bg-[#1a1a1a] rounded-sm text-left overflow-hidden shadow-[0_0_50px_rgba(0,128,255,0.2)] transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full relative z-10 border border-[#222222] neon-glow-blue">
                    <div class="bg-[#1a1a1a] px-5 pt-5 pb-5">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-xl font-bold text-white font-cyber">Edit Scenes</h3>
                            <button @click="emit('close')" class="text-[#666666] hover:text-[#00f0ff] transition-colors">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                            </button>
                        </div>

                        <div v-if="loading" class="text-center py-8">
                            <p class="text-[#666666] font-terminal">Loading scenes...</p>
                        </div>

                        <div v-else class="space-y-4 max-h-[70vh] overflow-y-auto pr-2 custom-scrollbar">
                            <div v-for="scene in scenes" :key="scene.id" class="flex flex-col md:flex-row gap-3 p-3 rounded-sm bg-[#222222] border border-[#333333] hover:border-[#00f0ff]/30 transition-all">
                                <!-- Media Preview -->
                                <div class="w-full md:w-1/3 space-y-1.5">
                                    <div class="aspect-video bg-[#0a0a0a] rounded-sm overflow-hidden relative group">
                                         <img :src="getSceneImage(scene)" class="w-full h-full object-cover" @error="$event.target.style.display='none'">
                                          <!-- Play icon overlay for video -->
                                          <a :href="getSceneVideo(scene)" target="_blank" class="absolute inset-0 flex items-center justify-center bg-[#0a0a0a]/50 opacity-0 group-hover:opacity-100 transition-opacity">
                                             <svg class="w-8 h-8 text-[#00f0ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                          </a>
                                    </div>
                                    <div class="text-[10px] text-center text-[#666666] font-terminal">Scene {{ scene.order + 1 }}</div>
                                </div>

                                <!-- Content -->
                                <div class="w-full md:w-2/3 space-y-2.5">
                                    <div>
                                        <label class="block text-[10px] font-bold text-[#666666] uppercase mb-1 font-terminal">Narration</label>
                                        <textarea v-model="scene.narration" rows="2" class="w-full px-3 py-2 text-xs rounded-sm bg-[#1a1a1a] border border-[#333333] focus:border-[#0080ff] focus:neon-glow-blue outline-none text-white"></textarea>
                                    </div>
                                    <div>
                                        <label class="block text-[10px] font-bold text-[#666666] uppercase mb-1 font-terminal">Image Prompt</label>
                                        <textarea v-model="scene.image_prompt" rows="2" class="w-full px-3 py-2 text-xs rounded-sm bg-[#1a1a1a] border border-[#333333] focus:border-[#0080ff] focus:neon-glow-blue outline-none text-white"></textarea>
                                    </div>
                                    <div class="flex justify-end pt-2 space-x-2">
                                        <button
                                            @click="saveScene(scene)"
                                            :disabled="savingId === scene.id || regeneratingId === scene.id"
                                            class="px-3 py-2 bg-[#222222] hover:bg-[#333333] text-white hover:text-[#00f0ff] text-xs font-medium rounded-sm transition-colors flex items-center disabled:opacity-50 disabled:cursor-not-allowed border border-[#333333] hover:border-[#00f0ff]/30">
                                            <svg v-if="savingId === scene.id" class="animate-spin -ml-1 mr-1.5 h-3 w-3" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                            <svg v-else class="w-3 h-3 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>
                                            Save
                                        </button>
                                        <button
                                            @click="regenerateScene(scene)"
                                            :disabled="regeneratingId === scene.id || savingId === scene.id"
                                            class="px-3 py-2 bg-[#0080ff] hover:bg-[#0060cc] text-white text-xs font-medium rounded-sm transition-colors flex items-center disabled:opacity-50 disabled:cursor-not-allowed border border-[#0080ff]">
                                            <svg v-if="regeneratingId === scene.id" class="animate-spin -ml-1 mr-1.5 h-3 w-3 text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                            <svg v-else class="w-3 h-3 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                                            Regenerate Scene
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>
