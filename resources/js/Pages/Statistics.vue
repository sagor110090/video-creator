<script setup>
import { ref, onMounted } from 'vue';
import { Head } from '@inertiajs/vue3';
import axios from 'axios';

const loading = ref(true);
const days = ref(30);
const dailyStats = ref([]);
const summary = ref({
    total_videos: 0,
    youtube_videos: 0,
    facebook_videos: 0,
    total_channels: 0,
    total_pages: 0,
});

const isDark = ref(false);

const toggleDarkMode = () => {
    isDark.value = !isDark.value;
    if (isDark.value) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
    }
};

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
    const savedTheme = localStorage.getItem('theme');
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && systemDark)) {
        isDark.value = true;
        document.documentElement.classList.add('dark');
    }

    fetchStatistics();
});
</script>

<template>
    <Head title="Statistics" />

    <div class="min-h-screen bg-[#f8fafc] dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-300">
        <nav class="sticky top-0 z-50 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
            <div class="container mx-auto px-4 max-w-6xl">
                <div class="flex items-center justify-between h-16">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-200/50 dark:shadow-indigo-900/20">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                        </div>
                        <span class="text-lg font-bold tracking-tight text-slate-800 dark:text-white">Video<span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600">AI</span> <span class="text-slate-400 dark:text-slate-500">Statistics</span></span>
                    </div>

                    <div class="flex items-center gap-3">
                        <a href="/" class="text-sm font-semibold text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                            Back to Home
                        </a>
                        <button @click="toggleDarkMode" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-all">
                            <svg v-if="isDark" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M16.243 17.243l.707.707M7.757 7.757l.707-.707M12 7a5 5 0 100 10 5 5 0 000-10z"></path></svg>
                            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path></svg>
                        </button>
                    </div>
                </div>
            </div>
        </nav>

        <main class="container mx-auto px-4 max-w-6xl py-8">
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-slate-900 dark:text-white mb-2">Upload Statistics</h1>
                <p class="text-slate-600 dark:text-slate-400">Track your daily video uploads by channel and page</p>
            </div>

            <div class="mb-6 flex items-center gap-4">
                <span class="text-sm font-semibold text-slate-600 dark:text-slate-400">Show last:</span>
                <div class="flex gap-2">
                    <button v-for="d in [7, 14, 30, 60, 90]" :key="d"
                            @click="days = d; fetchStatistics()"
                            :class="['px-4 py-2 rounded-lg text-sm font-bold transition-all',
                                     days === d ? 'bg-indigo-600 text-white' : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700']">
                        {{ d }} days
                    </button>
                </div>
            </div>

            <div v-if="loading" class="flex justify-center items-center py-20">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>

            <div v-else class="space-y-8">
                <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
                        <div class="text-3xl font-bold text-indigo-600 dark:text-indigo-400 mb-1">{{ summary.total_videos }}</div>
                        <div class="text-sm text-slate-600 dark:text-slate-400">Total Videos</div>
                    </div>
                    <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
                        <div class="text-3xl font-bold text-red-600 dark:text-red-400 mb-1">{{ summary.youtube_videos }}</div>
                        <div class="text-sm text-slate-600 dark:text-slate-400">YouTube Uploads</div>
                    </div>
                    <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
                        <div class="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-1">{{ summary.facebook_videos }}</div>
                        <div class="text-sm text-slate-600 dark:text-slate-400">Facebook Uploads</div>
                    </div>
                    <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
                        <div class="text-3xl font-bold text-violet-600 dark:text-violet-400 mb-1">{{ summary.total_channels }}</div>
                        <div class="text-sm text-slate-600 dark:text-slate-400">YouTube Channels</div>
                    </div>
                    <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
                        <div class="text-3xl font-bold text-cyan-600 dark:text-cyan-400 mb-1">{{ summary.total_pages }}</div>
                        <div class="text-sm text-slate-600 dark:text-slate-400">Facebook Pages</div>
                    </div>
                </div>

                <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
                    <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                        <h2 class="font-bold text-slate-800 dark:text-white">Daily Upload History</h2>
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
                            <div v-if="day.channels.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <div v-for="channel in day.channels" :key="channel.name" 
                                     class="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                                    <div v-if="channel.thumbnail" class="w-10 h-10 rounded-full overflow-hidden flex-shrink-0">
                                        <img :src="channel.thumbnail" class="w-full h-full object-cover">
                                    </div>
                                    <div v-else class="w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center text-white font-bold text-sm"
                                         :class="channel.type === 'youtube' ? 'bg-gradient-to-br from-red-500 to-red-600' : 'bg-gradient-to-br from-blue-500 to-blue-600'">
                                        {{ channel.name.charAt(0) }}
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <div class="text-sm font-semibold text-slate-800 dark:text-white truncate">{{ channel.name }}</div>
                                        <div class="text-xs text-slate-500 dark:text-slate-400 capitalize">{{ channel.type }}</div>
                                    </div>
                                    <div class="flex items-center gap-1">
                                        <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
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
        </main>
    </div>
</template>
