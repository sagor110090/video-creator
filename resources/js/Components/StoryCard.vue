<script setup>
import { computed } from 'vue';

const props = defineProps({
    story: {
        type: Object,
        required: true
    }
});

const emit = defineEmits(['regenerate', 'delete', 'upload']);

const statusClass = (status) => {
    switch (status) {
        case 'completed': return 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400';
        case 'processing': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400';
        case 'pending': return 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400';
        case 'failed': return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400';
        default: return 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-400';
    }
};

const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return new Intl.RelativeTimeFormat('en', { numeric: 'auto' }).format(
        Math.ceil((date - new Date()) / (1000 * 60 * 60 * 24)),
        'day'
    );
};
</script>

<template>
    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-xl transition-all duration-300 group flex flex-col h-full">
        <!-- Video Preview Area -->
        <div class="relative rounded-t-2xl overflow-hidden bg-slate-900 dark:bg-black aspect-video flex items-center justify-center">
            <video v-if="story.status === 'completed' && story.video_path"
                   controls class="w-full h-full object-contain"
                   :class="story.aspect_ratio === '9:16' ? 'max-w-[180px] mx-auto' : ''">
                <source :src="'/storage/' + story.video_path" type="video/mp4">
            </video>

            <!-- Status Overlay for Processing -->
            <div v-if="story.status === 'processing' || story.status === 'pending'"
                 class="absolute inset-0 bg-slate-900/80 dark:bg-black/80 flex flex-col items-center justify-center p-6 text-center">
                <div class="relative w-16 h-16 mb-4">
                    <div class="absolute inset-0 rounded-full border-4 border-indigo-500/20"></div>
                    <div class="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
                </div>
                <h4 class="text-white font-bold mb-1">AI is working...</h4>
                <p class="text-indigo-300 text-[10px] uppercase tracking-widest">
                    {{ story.scenes_count > 0 ? 'Parsing Scenes' : 'Initializing' }}
                </p>
            </div>

            <!-- Failed State Overlay -->
            <div v-if="story.status === 'failed'" class="absolute inset-0 bg-red-900/20 dark:bg-red-900/40 flex flex-col items-center justify-center">
                <svg class="w-12 h-12 text-red-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <span class="text-red-700 dark:text-red-400 font-bold">Generation Failed</span>
            </div>

            <!-- Actions Badge -->
            <div class="absolute top-4 right-4 flex space-x-2">
                <button v-if="story.status === 'completed' || story.status === 'failed'"
                        @click="emit('regenerate', story)"
                        class="p-2 bg-white/10 hover:bg-indigo-500 text-white rounded-lg backdrop-blur-md transition-all group/btn"
                        title="Regenerate Video">
                    <svg class="w-4 h-4 group-hover/btn:rotate-180 transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                </button>
                <button @click="emit('delete', story)"
                        class="p-2 bg-white/10 hover:bg-red-500 text-white rounded-lg backdrop-blur-md transition-all"
                        title="Delete Story">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
            </div>
        </div>

        <!-- Content Area -->
        <div class="p-6 flex-1 flex flex-col">
            <div class="flex justify-between items-start mb-3">
                <h3 class="font-bold text-slate-900 dark:text-white line-clamp-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">{{ story.title || 'Untitled Story' }}</h3>
                <span :class="statusClass(story.status)" class="text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-wider">
                    {{ story.status }}
                </span>
            </div>

            <p class="text-slate-500 dark:text-slate-400 text-sm line-clamp-2 mb-6 leading-relaxed">{{ story.content }}</p>

            <div class="mt-auto space-y-4">
                <!-- Progress Steps for Processing -->
                <div v-if="story.status === 'processing' || story.status === 'pending'" class="grid grid-cols-4 gap-1">
                    <div v-for="step in 4" :key="step" class="h-1 rounded-full"
                         :class="story.scenes_count >= step ? 'bg-indigo-500' : 'bg-slate-100 dark:bg-slate-800'"></div>
                </div>

                <!-- Actions for Completed -->
                <div v-if="story.status === 'completed'" class="space-y-3">
                    <div class="flex items-center justify-between text-xs text-slate-400 dark:text-slate-500">
                        <span>Created {{ formatDate(story.created_at) }}</span>
                        <span class="font-bold text-slate-600 dark:text-slate-400 uppercase">{{ story.aspect_ratio }}</span>
                    </div>

                    <div class="grid grid-cols-2 gap-2">
                        <a :href="'/storage/' + story.video_path" download
                           class="flex items-center justify-center space-x-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold py-2 rounded-xl transition-all text-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                            <span>Save</span>
                        </a>
                        <button v-if="!story.youtube_upload_status || story.youtube_upload_status === 'failed'"
                                @click="emit('upload', story)"
                                class="flex items-center justify-center space-x-2 bg-red-600 hover:bg-red-700 text-white font-bold py-2 rounded-xl transition-all text-sm">
                            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                            <span>Publish</span>
                        </button>
                        <div v-else class="col-span-2">
                            <div v-if="story.youtube_upload_status === 'completed'" class="w-full flex items-center justify-between p-2 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 rounded-xl border border-blue-100 dark:border-blue-900/30">
                                <div class="flex items-center">
                                    <img :src="story.youtube_channel?.channel_thumbnail" class="w-5 h-5 rounded-full mr-2">
                                    <span class="text-[10px] font-bold">LIVE ON YOUTUBE</span>
                                </div>
                                <a :href="'https://youtube.com/watch?v=' + story.youtube_video_id" target="_blank" class="text-[10px] underline font-bold">WATCH</a>
                            </div>
                            <div v-else-if="story.youtube_upload_status === 'uploading'" class="w-full flex items-center justify-center p-2 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 rounded-xl border border-yellow-100 dark:border-yellow-900/30">
                                <svg class="animate-spin h-3 w-3 mr-2" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                <span class="text-[10px] font-bold">UPLOADING...</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
