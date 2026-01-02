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
            <div class="flex items-center gap-2">
                <span class="text-sm font-semibold text-slate-600 dark:text-slate-400">Show last:</span>
                <div class="flex gap-1">
                    <button v-for="d in [7, 14, 30, 60, 90]" :key="d"
                            @click="days = d; fetchStatistics()"
                            :class="['px-3 py-1.5 rounded-md text-xs font-bold transition-all',
                                     days === d ? 'bg-indigo-600 text-white shadow-sm' : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700']">
                        {{ d }} days
                    </button>
                </div>
            </div>
        </template>

        <div class="space-y-6">
             <!-- Summary Header -->
            <div>
                <h2 class="text-lg font-medium text-slate-900 dark:text-white">Upload Overview</h2>
                <p class="text-sm text-slate-500 dark:text-slate-400">Track your video uploads across platforms</p>
            </div>

            <div v-if="loading" class="flex justify-center items-center py-20">
                <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
            </div>

            <div v-else class="space-y-6">
                <!-- Stats Grid -->
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
                        <div class="text-3xl font-bold text-indigo-600 dark:text-indigo-400 mb-1">{{ summary.total_videos }}</div>
                        <div class="text-sm text-slate-600 dark:text-slate-400">Total Videos</div>
                    </div>
                    <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
                        <div class="text-3xl font-bold text-red-600 dark:text-red-400 mb-1">{{ summary.youtube_videos }}</div>
                        <div class="text-sm text-slate-600 dark:text-slate-400">YouTube Uploads</div>
                    </div>
                    <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
                        <div class="text-3xl font-bold text-violet-600 dark:text-violet-400 mb-1">{{ summary.total_channels }}</div>
                        <div class="text-sm text-slate-600 dark:text-slate-400">YouTube Channels</div>
                    </div>
                </div>

                <!-- History List -->
                <div class="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
                    <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                        <h3 class="font-bold text-slate-800 dark:text-white">Daily Upload History</h3>
                    </div>
                    <div class="divide-y divide-slate-200 dark:divide-slate-800">
                        <div v-for="day in dailyStats" :key="day.date" class="px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                            <div class="flex items-center justify-between mb-3">
                                <div class="flex items-center gap-3">
                                    <span class="text-sm font-semibold text-slate-800 dark:text-white">{{ formatDate(day.date) }}</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="text-2xl font-bold" :class="day.total > 0 ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'">{{ day.total }}</span>
                                    <span class="text-xs text-slate-500 dark:text-slate-400">videos</span>
                                </div>
                            </div>
                            <div v-if="day.channels.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                <div v-for="channel in day.channels" :key="channel.name"
                                     class="flex items-center gap-3 p-2 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                                    <div v-if="channel.thumbnail" class="w-8 h-8 rounded-full overflow-hidden flex-shrink-0">
                                        <img :src="channel.thumbnail" class="w-full h-full object-cover">
                                    </div>
                                    <div v-else class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-white font-bold text-xs"
                                         :class="channel.type === 'youtube' ? 'bg-gradient-to-br from-red-500 to-red-600' : 'bg-gradient-to-br from-blue-500 to-blue-600'">
                                        {{ channel.name.charAt(0) }}
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <div class="text-sm font-medium text-slate-800 dark:text-white truncate">{{ channel.name }}</div>
                                        <div class="text-xs text-slate-500 dark:text-slate-400 capitalize">{{ channel.type }}</div>
                                    </div>
                                    <div class="flex items-center gap-1">
                                        <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
                                             :class="channel.type === 'youtube' ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400' : 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'">
                                            {{ channel.count }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div v-else class="text-sm text-slate-400 dark:text-slate-600 italic">No uploads</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
