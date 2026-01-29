<script setup>
import { ref, onMounted } from 'vue';
import { Head } from '@inertiajs/vue3';
import axios from 'axios';
import AppLayout from '@/Layouts/AppLayout.vue';

const loading = ref(true);
const days = ref(30);
const dailyStats = ref([]);
const summary = ref({
    total_videos: 0,
    youtube_videos: 0,
    total_channels: 0,
});

const fetchStatistics = async () => {
    loading.value = true;
    try {
        const response = await axios.get(`/api/statistics?days=${days.value}`);
        dailyStats.value = response.data.daily_stats;
        summary.value = response.data.summary;
    } catch (error) {
        console.error('Error fetching statistics:', error);
    } finally {
        loading.value = false;
    }
};

const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

const getTotalForDay = (day) => {
    return day.channels.reduce((sum, channel) => sum + channel.count, 0);
};

onMounted(() => {
    fetchStatistics();
});
</script>

<template>
    <AppLayout>
        <Head title="Statistics" />

        <template #header>
            Statistics
        </template>

        <template #actions>
            <div class="flex items-center gap-3">
                <div class="flex items-center gap-2 rounded-sm border border-[#222222] bg-[#1a1a1a]/60 px-3 py-2 shadow-[0_0_20px_rgba(0,240,255,0.1)]">
                    <span class="text-[10px] font-bold uppercase tracking-[0.2em] text-[#666666] font-terminal">Window</span>
                    <div class="flex gap-1">
                        <button v-for="d in [7, 14, 30, 60, 90]" :key="d"
                                @click="days = d; fetchStatistics()"
                                :class="['px-2.5 py-1 text-[10px] font-semibold transition-all duration-300 rounded-sm',
                                         days === d ? 'bg-[#00f0ff] text-[#0a0a0a] neon-glow-cyan' : 'text-[#666666] hover:text-[#00f0ff] hover:bg-[#222222]']">
                            {{ d }}d
                        </button>
                    </div>
                </div>
            </div>
        </template>

        <div class="space-y-8">
            <div class="relative overflow-hidden rounded-sm border border-[#222222] bg-[#111111] px-6 py-8 shadow-[0_0_30px_rgba(0,240,255,0.05)] holographic">
                <div class="absolute inset-0 bg-gradient-to-br from-[#00f0ff]/5 via-transparent to-transparent"></div>
                <div class="relative flex flex-col gap-2">
                    <p class="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#00f0ff] font-terminal">Intelligence Stream</p>
                    <h2 class="text-3xl font-black text-white tracking-tight font-cyber">Upload Overview</h2>
                    <p class="text-sm text-[#666666] max-w-2xl">A polished view of publishing momentum, tuned for quick decisions and clean reporting.</p>
                </div>
            </div>

            <div v-if="loading" class="flex justify-center items-center py-16">
                <div class="relative w-10 h-10">
                    <div class="absolute inset-0 border-4 border-[#00f0ff]/20 rounded-sm"></div>
                    <div class="absolute inset-0 border-4 border-[#00f0ff] border-t-transparent animate-spin rounded-sm"></div>
                </div>
            </div>

            <div v-else class="space-y-8">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="group relative overflow-hidden rounded-sm border border-[#222222] bg-[#1a1a1a] p-5 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_0_30px_rgba(0,240,255,0.15)] hover:border-[#00f0ff]/30">
                        <div class="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-[#00f0ff] via-[#0080ff] to-[#bf00ff]"></div>
                        <p class="text-[11px] font-semibold uppercase tracking-[0.25em] text-[#666666] font-terminal">Total</p>
                        <div class="mt-3 flex items-end justify-between">
                            <div class="text-4xl font-black text-white font-cyber">{{ summary.total_videos }}</div>
                            <div class="rounded-sm bg-[#222222] px-2 py-1 text-[10px] font-semibold text-[#666666] border border-[#333333]">Videos</div>
                        </div>
                    </div>
                    <div class="group relative overflow-hidden rounded-sm border border-[#222222] bg-[#1a1a1a] p-5 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_0_30px_rgba(255,0,255,0.15)] hover:border-[#ff00ff]/30">
                        <div class="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-[#ff00ff] via-[#ff5500] to-[#ffaa00]"></div>
                        <p class="text-[11px] font-semibold uppercase tracking-[0.25em] text-[#666666] font-terminal">YouTube</p>
                        <div class="mt-3 flex items-end justify-between">
                            <div class="text-4xl font-black text-white font-cyber">{{ summary.youtube_videos }}</div>
                            <div class="rounded-sm bg-[#222222] px-2 py-1 text-[10px] font-semibold text-[#666666] border border-[#333333]">Uploads</div>
                        </div>
                    </div>
                    <div class="group relative overflow-hidden rounded-sm border border-[#222222] bg-[#1a1a1a] p-5 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_0_30px_rgba(0,255,65,0.15)] hover:border-[#00ff41]/30">
                        <div class="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-[#00ff41] via-[#00f0ff] to-[#0080ff]"></div>
                        <p class="text-[11px] font-semibold uppercase tracking-[0.25em] text-[#666666] font-terminal">Channels</p>
                        <div class="mt-3 flex items-end justify-between">
                            <div class="text-4xl font-black text-white font-cyber">{{ summary.total_channels }}</div>
                            <div class="rounded-sm bg-[#222222] px-2 py-1 text-[10px] font-semibold text-[#666666] border border-[#333333]">Connected</div>
                        </div>
                    </div>
                </div>

                <div class="rounded-sm border border-[#222222] bg-[#1a1a1a] overflow-hidden shadow-[0_0_30px_rgba(0,240,255,0.08)]">
                    <div class="flex items-center justify-between px-6 py-5 bg-[#111111]/80 border-b border-[#222222]">
                        <div>
                            <p class="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#00f0ff] font-terminal">Cadence</p>
                            <h3 class="text-base font-black text-white font-cyber">Daily Upload History</h3>
                        </div>
                    </div>
                    <div class="divide-y divide-[#222222]">
                        <div v-for="day in dailyStats" :key="day.date" class="px-6 py-5 transition-all duration-300 hover:bg-[#0a0a0a]/40">
                            <div class="flex flex-wrap items-center justify-between gap-3 mb-3">
                                <span class="text-sm font-semibold text-white">{{ formatDate(day.date) }}</span>
                                <div class="flex items-center gap-2">
                                    <span class="text-2xl font-black" :class="day.total > 0 ? 'text-[#00f0ff] font-cyber' : 'text-[#333333]'">{{ day.total }}</span>
                                    <span class="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#666666] font-terminal">Videos</span>
                                </div>
                            </div>
                            <div v-if="day.channels.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                <div v-for="channel in day.channels" :key="channel.name"
                                     class="flex items-center gap-2.5 rounded-sm border border-[#222222] bg-[#222222] p-2.5 transition-all duration-300 hover:-translate-y-0.5 hover:border-[#00f0ff]/30 hover:shadow-[0_0_20px_rgba(0,240,255,0.1)]">
                                    <div v-if="channel.thumbnail" class="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 ring-1 ring-[#333333]">
                                        <img :src="channel.thumbnail" class="w-full h-full object-cover">
                                    </div>
                                    <div v-else class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-white font-bold text-xs"
                                         :class="channel.type === 'youtube' ? 'bg-gradient-to-br from-[#ff00ff] to-[#ff5500]' : 'bg-gradient-to-br from-[#00ff41] to-[#00f0ff]'">
                                        {{ channel.name.charAt(0) }}
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <div class="text-sm font-semibold text-white truncate">{{ channel.name }}</div>
                                        <div class="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#666666] font-terminal">{{ channel.type }}</div>
                                    </div>
                                    <div class="w-7 h-7 rounded-sm flex items-center justify-center text-xs font-bold"
                                         :class="channel.type === 'youtube' ? 'bg-[#1a1a1a] text-[#ff00ff] border border-[#ff00ff]/30' : 'bg-[#1a1a1a] text-[#00ff41] border border-[#00ff41]/30'">
                                        {{ channel.count }}
                                    </div>
                                </div>
                            </div>
                            <div v-else class="text-sm text-[#333333] font-terminal italic">No uploads</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
