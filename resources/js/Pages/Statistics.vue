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
                <div class="flex items-center gap-2 rounded-full border border-[#e6dccf] dark:border-slate-700 bg-white/80 dark:bg-slate-900/60 px-3 py-2 shadow-[0_10px_30px_-20px_rgba(15,23,42,0.4)]">
                    <span class="text-[11px] font-bold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-300">Window</span>
                    <div class="flex gap-1">
                        <button v-for="d in [7, 14, 30, 60, 90]" :key="d"
                                @click="days = d; fetchStatistics()"
                                :class="['px-3 py-1.5 rounded-full text-[11px] font-semibold transition-all duration-300',
                                         days === d ? 'bg-[#0b1021] text-[#f7f2e8] shadow-[0_10px_20px_-12px_rgba(11,16,33,0.6)]' : 'text-[#6a5d4d] dark:text-slate-300 hover:text-[#2b2218] dark:hover:text-white hover:bg-[#f2ebe0] dark:hover:bg-slate-800']">
                            {{ d }}d
                        </button>
                    </div>
                </div>
            </div>
        </template>

        <div class="space-y-8">
            <div class="relative overflow-hidden rounded-[32px] border border-[#e6dccf] dark:border-slate-800 bg-[#f7f2e8] dark:bg-slate-900/70 px-8 py-10 shadow-[0_30px_60px_-40px_rgba(15,23,42,0.4)]">
                <div class="absolute inset-0 bg-gradient-to-br from-[#fff7ee] via-transparent to-transparent dark:from-slate-900/50"></div>
                <div class="relative flex flex-col gap-3">
                    <p class="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#6a5d4d] dark:text-slate-400">Intelligence Stream</p>
                    <h2 class="text-3xl font-black text-[#15131a] dark:text-white tracking-tight">Upload Overview</h2>
                    <p class="text-sm text-[#6a5d4d] dark:text-slate-400 max-w-2xl">A polished view of publishing momentum, tuned for quick decisions and clean reporting.</p>
                </div>
            </div>

            <div v-if="loading" class="flex justify-center items-center py-20">
                <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-[#0b1021] dark:border-white"></div>
            </div>

            <div v-else class="space-y-8">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
                    <div class="group relative overflow-hidden rounded-[26px] border border-[#e6dccf] dark:border-slate-800 bg-white dark:bg-slate-900/70 p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_30px_60px_-35px_rgba(15,23,42,0.45)]">
                        <div class="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-[#0b1021] via-[#4b3f2f] to-[#c78c4a]"></div>
                        <p class="text-[11px] font-semibold uppercase tracking-[0.25em] text-[#6a5d4d] dark:text-slate-400">Total</p>
                        <div class="mt-4 flex items-end justify-between">
                            <div class="text-4xl font-black text-[#0b1021] dark:text-white">{{ summary.total_videos }}</div>
                            <div class="rounded-full bg-[#f2ebe0] dark:bg-slate-800 px-3 py-1 text-[11px] font-semibold text-[#6a5d4d] dark:text-slate-300">Videos</div>
                        </div>
                    </div>
                    <div class="group relative overflow-hidden rounded-[26px] border border-[#e6dccf] dark:border-slate-800 bg-white dark:bg-slate-900/70 p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_30px_60px_-35px_rgba(15,23,42,0.45)]">
                        <div class="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-[#551d1b] via-[#b9382a] to-[#ff7a59]"></div>
                        <p class="text-[11px] font-semibold uppercase tracking-[0.25em] text-[#6a5d4d] dark:text-slate-400">YouTube</p>
                        <div class="mt-4 flex items-end justify-between">
                            <div class="text-4xl font-black text-[#551d1b] dark:text-white">{{ summary.youtube_videos }}</div>
                            <div class="rounded-full bg-[#fde7dd] dark:bg-slate-800 px-3 py-1 text-[11px] font-semibold text-[#8a3a2f] dark:text-slate-300">Uploads</div>
                        </div>
                    </div>
                    <div class="group relative overflow-hidden rounded-[26px] border border-[#e6dccf] dark:border-slate-800 bg-white dark:bg-slate-900/70 p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_30px_60px_-35px_rgba(15,23,42,0.45)]">
                        <div class="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-[#1a2a2f] via-[#2f6c73] to-[#6dd3ce]"></div>
                        <p class="text-[11px] font-semibold uppercase tracking-[0.25em] text-[#6a5d4d] dark:text-slate-400">Channels</p>
                        <div class="mt-4 flex items-end justify-between">
                            <div class="text-4xl font-black text-[#1a2a2f] dark:text-white">{{ summary.total_channels }}</div>
                            <div class="rounded-full bg-[#e3f5f4] dark:bg-slate-800 px-3 py-1 text-[11px] font-semibold text-[#2f6c73] dark:text-slate-300">Connected</div>
                        </div>
                    </div>
                </div>

                <div class="rounded-[28px] border border-[#e6dccf] dark:border-slate-800 bg-white dark:bg-slate-900/70 overflow-hidden shadow-[0_30px_60px_-40px_rgba(15,23,42,0.35)]">
                    <div class="flex items-center justify-between px-8 py-6 bg-[#f7f2e8] dark:bg-slate-900/80 border-b border-[#e6dccf] dark:border-slate-800">
                        <div>
                            <p class="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#6a5d4d] dark:text-slate-400">Cadence</p>
                            <h3 class="text-lg font-black text-[#15131a] dark:text-white">Daily Upload History</h3>
                        </div>
                    </div>
                    <div class="divide-y divide-[#efe6d8] dark:divide-slate-800">
                        <div v-for="day in dailyStats" :key="day.date" class="px-8 py-6 transition-all duration-300 hover:bg-[#fbf7f1] dark:hover:bg-slate-900/60">
                            <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
                                <span class="text-sm font-semibold text-[#15131a] dark:text-white">{{ formatDate(day.date) }}</span>
                                <div class="flex items-center gap-2">
                                    <span class="text-2xl font-black" :class="day.total > 0 ? 'text-[#0b1021] dark:text-white' : 'text-[#b3a799] dark:text-slate-600'">{{ day.total }}</span>
                                    <span class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400">Videos</span>
                                </div>
                            </div>
                            <div v-if="day.channels.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                <div v-for="channel in day.channels" :key="channel.name"
                                     class="flex items-center gap-3 rounded-2xl border border-[#efe6d8] dark:border-slate-800 bg-[#fbf7f1] dark:bg-slate-900/60 p-3 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_20px_40px_-30px_rgba(15,23,42,0.35)]">
                                    <div v-if="channel.thumbnail" class="w-9 h-9 rounded-full overflow-hidden flex-shrink-0 ring-2 ring-white dark:ring-slate-800">
                                        <img :src="channel.thumbnail" class="w-full h-full object-cover">
                                    </div>
                                    <div v-else class="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center text-white font-bold text-xs"
                                         :class="channel.type === 'youtube' ? 'bg-gradient-to-br from-[#b9382a] to-[#ff7a59]' : 'bg-gradient-to-br from-[#2f6c73] to-[#6dd3ce]'">
                                        {{ channel.name.charAt(0) }}
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <div class="text-sm font-semibold text-[#15131a] dark:text-white truncate">{{ channel.name }}</div>
                                        <div class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400">{{ channel.type }}</div>
                                    </div>
                                    <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
                                         :class="channel.type === 'youtube' ? 'bg-[#fde7dd] text-[#b9382a] dark:bg-slate-800 dark:text-slate-200' : 'bg-[#e3f5f4] text-[#2f6c73] dark:bg-slate-800 dark:text-slate-200'">
                                        {{ channel.count }}
                                    </div>
                                </div>
                            </div>
                            <div v-else class="text-sm text-[#b3a799] dark:text-slate-500 italic">No uploads</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
