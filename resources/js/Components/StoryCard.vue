<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue';

const props = defineProps({
    story: {
        type: Object,
        required: true
    }
});

const emit = defineEmits(['regenerate', 'delete', 'upload', 'schedule', 'edit-scenes']);
const videoLoaded = ref(false);
const isVisible = ref(false);
const cardRef = ref(null);
const videoError = ref(false);
let observer = null;

const handleVideoLoad = () => {
    videoLoaded.value = true;
    videoError.value = false;
};

const handleVideoError = () => {
    videoError.value = true;
    console.error('Video failed to load:', '/storage/' + props.story.video_path);
};

onMounted(() => {
    observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
            isVisible.value = true;
            observer.disconnect();
        }
    }, {
        rootMargin: '100px',
        threshold: 0.01
    });

    if (cardRef.value) {
        observer.observe(cardRef.value);
    }
});

onUnmounted(() => {
    if (observer) {
        observer.disconnect();
    }
});

const statusClass = (status) => {
    switch (status) {
        case 'completed': return 'bg-[#1a1a1a] text-[#00ff41] border border-[#00ff41]/30';
        case 'processing': return 'bg-[#1a1a1a] text-[#00f0ff] border border-[#00f0ff]/30';
        case 'pending': return 'bg-[#1a1a1a] text-[#ffaa00] border border-[#ffaa00]/30';
        case 'failed': return 'bg-[#1a1a1a] text-[#ff00ff] border border-[#ff00ff]/30';
        case 'scheduled': return 'bg-[#1a1a1a] text-[#bf00ff] border border-[#bf00ff]/30';
        default: return 'bg-[#1a1a1a] text-[#666666] border border-[#333333]';
    }
};

const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = date - now;

    if (diffTime > 0) {
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        if (diffDays <= 1) {
            const diffHours = Math.ceil(diffTime / (1000 * 60 * 60));
            if (diffHours <= 1) {
                 const diffMins = Math.ceil(diffTime / (1000 * 60));
                 return `in ${diffMins}m`;
            }
             return `in ${diffHours}h`;
        }
         return `in ${diffDays}d`;
    }

    const pastDiff = Math.abs(diffTime);
    const diffDays = Math.floor(pastDiff / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
        const diffHours = Math.floor(pastDiff / (1000 * 60 * 60));
        if (diffHours === 0) {
            const diffMins = Math.floor(pastDiff / (1000 * 60));
            return diffMins === 0 ? 'Just now' : `${diffMins}m ago`;
        }
        return `${diffHours}h ago`;
    } else if (diffDays === 1) {
        return 'Yesterday';
    } else if (diffDays < 7) {
        return `${diffDays} days ago`;
    } else {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
};

const formatFullDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
};

const formatProcessingTime = (story) => {
    if (story.status !== 'completed' || !story.created_at || !story.updated_at) return null;

    const created = new Date(story.created_at);
    const updated = new Date(story.updated_at);
    const durationMs = updated - created;

    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);

    if (minutes > 0) {
        return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
};

const formatScheduledDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();

    const isToday = date.toDateString() === now.toDateString();

    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const isTomorrow = date.toDateString() === tomorrow.toDateString();

    const timeStr = date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });

    if (isToday) {
        return `Today at ${timeStr}`;
    } else if (isTomorrow) {
        return `Tomorrow at ${timeStr}`;
    } else {
        const dateStr = date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            weekday: 'short'
        });
        return `${dateStr} at ${timeStr}`;
    }
};
</script>

<template>
    <div ref="cardRef" class="glass-card group flex flex-col h-full rounded-sm overflow-hidden transition-all duration-300 hover:neon-glow-cyan">
        <!-- Video Preview Area -->
        <div class="relative overflow-hidden bg-[#0a0a0a] aspect-video flex items-center justify-center border-b border-[#222222]">
            <template v-if="story.status === 'completed' && story.video_path">
                <!-- Placeholder / Skeleton -->
                <div v-if="!videoLoaded || !isVisible" class="absolute inset-0 flex flex-col items-center justify-center bg-[#1a1a1a] animate-pulse">
                    <svg class="w-8 h-8 text-[#333333] mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span class="text-[9px] text-[#666666] font-medium uppercase tracking-wider font-terminal">Loading Preview...</span>
                </div>

                <video v-if="isVisible"
                       @loadeddata="handleVideoLoad"
                       @error="handleVideoError"
                       v-show="videoLoaded && !videoError"
                       controls
                       preload="metadata"
                       playsinline
                       class="w-full h-full object-contain"
                       :class="story.aspect_ratio === '9:16' ? 'max-w-[180px] mx-auto' : ''">
                    <source :src="'/storage/' + story.video_path + '?t=' + new Date(story.updated_at).getTime()" type="video/mp4">
                </video>

                <div v-if="videoError" class="absolute inset-0 flex flex-col items-center justify-center bg-[#1a1a1a]">
                    <svg class="w-8 h-8 text-[#ff00ff] mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <p class="text-[#ff00ff] text-xs font-medium">Video failed to load</p>
                    <a :href="'/storage/' + story.video_path" target="_blank" class="mt-1 text-[#0080ff] text-[10px] underline">Open in new tab</a>
                </div>
            </template>

            <!-- Status Overlay for Processing -->
            <div v-if="story.status === 'processing' || story.status === 'pending'"
                 class="absolute inset-0 bg-[#0a0a0a]/90 flex flex-col items-center justify-center p-5 text-center">
                <div class="relative w-12 h-12 mb-3">
                    <div class="absolute inset-0 border-4 border-[#00f0ff]/20 rounded-sm"></div>
                    <div class="absolute inset-0 border-4 border-[#00f0ff] border-t-transparent animate-spin rounded-sm"></div>
                </div>
                <h4 class="text-white font-bold mb-1 font-cyber">AI is working...</h4>
                <p class="text-[#00f0ff] text-[9px] uppercase tracking-widest font-terminal">
                    {{ story.scenes_count > 0 ? 'Parsing Scenes' : 'Initializing' }}
                </p>
            </div>

            <!-- Failed State Overlay -->
            <div v-if="story.status === 'failed' || (story.status === 'completed' && !story.video_path)" class="absolute inset-0 bg-[#ff00ff]/10 flex flex-col items-center justify-center">
                <svg class="w-10 h-10 text-[#ff00ff] mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <span class="text-[#ff00ff] font-bold text-sm">{{ story.status === 'completed' ? 'Video Missing' : 'Generation Failed' }}</span>
            </div>

            <!-- Actions Badge -->
            <div class="absolute top-3 right-3 flex space-x-1.5">
                <button v-if="story.status === 'completed' || story.status === 'failed'"
                        @click="emit('edit-scenes', story)"
                        class="p-1.5 bg-[#1a1a1a]/80 hover:bg-[#00f0ff] hover:text-[#0a0a0a] text-[#00f0ff] rounded-sm backdrop-blur-md transition-all border border-[#333333]"
                        title="Edit Scenes">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                </button>
                <button v-if="story.status === 'completed' || story.status === 'failed'"
                        @click="emit('regenerate', story)"
                        class="p-1.5 bg-[#1a1a1a]/80 hover:bg-[#00ff41] hover:text-[#0a0a0a] text-[#00ff41] rounded-sm backdrop-blur-md transition-all group/btn border border-[#333333]"
                        title="Regenerate Video">
                    <svg class="w-3.5 h-3.5 group-hover/btn:rotate-180 transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                </button>
                <button @click="emit('delete', story)"
                        class="p-1.5 bg-[#1a1a1a]/80 hover:bg-[#ff00ff] hover:text-[#0a0a0a] text-[#ff00ff] rounded-sm backdrop-blur-md transition-all border border-[#333333]"
                        title="Delete Story">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
            </div>
        </div>

        <!-- Content Area -->
        <div class="p-4 flex-1 flex flex-col">
            <!-- Channel Info -->
            <div v-if="story.youtube_channel" class="flex items-center space-x-2 mb-2 pb-2 border-b border-[#222222]">
                <img :src="story.youtube_channel.channel_thumbnail" class="w-5 h-5 rounded-full border border-[#333333]">
                <span class="text-[10px] font-bold text-[#a0a0a0] truncate font-terminal">{{ story.youtube_channel.channel_title }}</span>
            </div>

            <div class="flex justify-between items-start mb-2">
                <h3 class="font-bold text-white line-clamp-1 group-hover:text-[#00f0ff] transition-colors text-sm">{{ story.title || 'Untitled Story' }}</h3>
                <span :class="statusClass(story.status)" class="text-[9px] font-bold px-2 py-0.5 rounded-sm uppercase tracking-wider font-terminal">
                    {{ story.status }}
                </span>
            </div>

            <p class="text-[#666666] text-xs line-clamp-2 mb-4 leading-relaxed">{{ story.content }}</p>

            <div class="mt-auto space-y-3">
                <!-- Progress Steps for Processing -->
                <div v-if="story.status === 'processing' || story.status === 'pending'" class="grid grid-cols-4 gap-0.5">
                    <div v-for="step in 4" :key="step" class="h-0.5 rounded-sm"
                         :class="story.scenes_count >= step ? 'bg-[#00f0ff]' : 'bg-[#333333]'"></div>
                </div>

                <!-- Actions for Completed -->
                <div v-if="story.status === 'completed'" class="space-y-2.5">
                    <div class="flex items-center justify-between text-[10px]">
                        <div class="flex items-center space-x-1.5">
                            <div class="flex items-center space-x-1 bg-[#1a1a1a] px-2 py-1 rounded-sm border border-[#222222]">
                                <svg class="w-3 h-3 text-[#00f0ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                <span class="text-[#00f0ff] font-semibold font-cyber" :title="formatFullDate(story.created_at)">{{ formatDate(story.created_at) }}</span>
                            </div>
                            <div v-if="formatProcessingTime(story)" class="flex items-center space-x-1 bg-[#1a1a1a] px-2 py-1 rounded-sm border border-[#222222]">
                                <svg class="w-3 h-3 text-[#00ff41]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                <span class="text-[#00ff41] font-semibold font-cyber">{{ formatProcessingTime(story) }}</span>
                            </div>
                            <div v-if="story.scheduled_for && !story.is_uploaded_to_youtube" class="flex items-center space-x-1 bg-[#1a1a1a] px-2 py-1 rounded-sm border border-[#222222]">
                                <svg class="w-3 h-3 text-[#ffaa00]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                <span class="text-[#ffaa00] font-semibold font-cyber" title="Scheduled Upload">{{ formatScheduledDate(story.scheduled_for) }}</span>
                            </div>
                        </div>
                        <div class="flex items-center space-x-1 bg-[#1a1a1a] px-2 py-1 rounded-sm border border-[#222222]">
                            <svg class="w-3 h-3 text-[#666666]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                            <span class="text-[#666666] font-semibold uppercase font-terminal">{{ story.aspect_ratio }}</span>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-1.5">
                        <a :href="'/storage/' + story.video_path" download
                           :class="(story.youtube_upload_status === 'failed') ? 'col-span-1' : ''"
                           class="flex items-center justify-center space-x-1.5 bg-[#222222] hover:bg-[#333333] text-white font-bold py-2 rounded-sm transition-all text-[10px] border border-[#333333] hover:border-[#00f0ff]/30">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                            <span>Save</span>
                        </a>

                        <!-- YouTube Upload Button -->
                        <button v-if="story.youtube_upload_status === 'failed'"
                                @click="emit('upload', story)"
                                class="col-span-1 flex items-center justify-center space-x-1.5 bg-[#1a1a1a] hover:bg-[#ff00ff] text-[#ff00ff] hover:text-[#0a0a0a] font-bold py-2 rounded-sm transition-all text-[10px] border border-[#333333] hover:border-[#ff00ff]">
                            <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                            <span>Retry Publish</span>
                        </button>

                        <button v-else-if="!story.youtube_upload_status && !story.is_uploaded_to_youtube"
                                class="flex space-x-1">
                            <!-- Schedule Button -->
                            <button @click="emit('schedule', story)"
                                    class="bg-[#1a1a1a] hover:bg-[#ffaa00] text-[#ffaa00] hover:text-[#0a0a0a] p-1.5 rounded-sm transition-all border border-[#333333] hover:border-[#ffaa00]"
                                    title="Schedule Upload">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                            </button>

                            <!-- Immediate Upload -->
                            <button @click="emit('upload', story)"
                                    class="flex items-center justify-center space-x-1.5 bg-[#1a1a1a] hover:bg-[#ff0000] text-[#ff0000] hover:text-white font-bold py-2 px-3 rounded-sm transition-all text-[10px] border border-[#333333] hover:border-[#ff0000]">
                                <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                                <span>Publish</span>
                            </button>
                        </button>

                        <!-- YouTube Error -->
                        <div v-if="story.youtube_upload_status === 'failed' && story.youtube_error" class="col-span-2 p-1.5 bg-[#1a1a1a] border border-[#ff00ff]/30 rounded-sm">
                            <p class="text-[9px] text-[#ff00ff] leading-tight font-terminal">
                                <span class="font-bold">YT Error:</span> {{ story.youtube_error }}
                            </p>
                        </div>

                        <!-- YouTube Status -->
                        <div v-if="story.youtube_upload_status && story.youtube_upload_status !== 'failed'" class="col-span-2">
                            <div v-if="story.youtube_upload_status === 'completed'" class="w-full flex items-center justify-between p-1.5 bg-[#1a1a1a] text-[#00ff41] rounded-sm border border-[#00ff41]/30">
                                <div class="flex items-center">
                                    <img :src="story.youtube_channel?.channel_thumbnail" class="w-4 h-4 rounded-full mr-1.5">
                                    <span class="text-[9px] font-bold font-cyber">LIVE ON YOUTUBE</span>
                                </div>
                                <a :href="'https://youtube.com/watch?v=' + story.youtube_video_id" target="_blank" class="text-[9px] underline font-bold">WATCH</a>
                            </div>
                            <div v-else-if="story.youtube_upload_status === 'scheduled'" class="w-full flex items-center justify-between p-1.5 bg-[#1a1a1a] text-[#bf00ff] rounded-sm border border-[#bf00ff]/30">
                                <div class="flex items-center">
                                    <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                                    <span class="text-[9px] font-bold font-cyber">SCHEDULED ON YOUTUBE</span>
                                </div>
                                <span class="text-[9px] font-bold font-cyber">{{ formatScheduledDate(story.scheduled_for) }}</span>
                            </div>
                            <div v-else-if="story.youtube_upload_status === 'uploading'" class="w-full flex items-center justify-center p-1.5 bg-[#1a1a1a] text-[#ffaa00] rounded-sm border border-[#ffaa00]/30">
                                <svg class="animate-spin h-2.5 w-2.5 mr-1.5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                <span class="text-[9px] font-bold font-cyber">UPLOADING TO YOUTUBE...</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
