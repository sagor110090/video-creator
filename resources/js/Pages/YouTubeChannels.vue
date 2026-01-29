<script setup>
import { ref, onMounted } from 'vue';
import { Head } from '@inertiajs/vue3';
import AppLayout from '@/Layouts/AppLayout.vue';
import axios from 'axios';
import { useToast } from 'vue-toast-notification';
import Swal from 'sweetalert2';

const toast = useToast();
const channels = ref([]);
const loading = ref(false);
const isDark = ref(document.documentElement.classList.contains('dark'));

const fetchChannels = async () => {
    loading.value = true;
    try {
        const response = await axios.get('/api/youtube/channels');
        channels.value = response.data;
    } catch (error) {
        console.error('Error fetching channels:', error);
        toast.error('Failed to load channels');
    } finally {
        loading.value = false;
    }
};

const handleConnectChannel = () => {
    window.location.href = '/youtube/auth';
};

const handleReconnect = async (channel) => {
    const result = await Swal.fire({
        title: 'Reconnect Channel?',
        text: `You will be redirected to YouTube to re-authenticate the channel "${channel.channel_title}"`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#0b1021',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Reconnect',
        cancelButtonText: 'Cancel',
        background: isDark.value ? '#0f172a' : '#ffffff',
        color: isDark.value ? '#f8fafc' : '#0f172a'
    });

    if (result.isConfirmed) {
        window.location.href = `/youtube/reconnect/${channel.id}`;
    }
};

const handleRefresh = async (channel) => {
    const result = await Swal.fire({
        title: 'Refresh Token?',
        text: `This will attempt to refresh the access token for "${channel.channel_title}"`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#0b1021',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Refresh',
        cancelButtonText: 'Cancel',
        background: isDark.value ? '#0f172a' : '#ffffff',
        color: isDark.value ? '#f8fafc' : '#0f172a'
    });

    if (result.isConfirmed) {
        try {
            loading.value = true;
            const response = await axios.post(`/api/youtube/refresh/${channel.id}`);
            toast.success('Token refreshed successfully');
            await fetchChannels();
        } catch (error) {
            console.error('Error refreshing token:', error);
            toast.error(error.response?.data?.error || 'Failed to refresh token');
        } finally {
            loading.value = false;
        }
    }
};

const handleDisconnect = async (channel) => {
    const result = await Swal.fire({
        title: 'Disconnect Channel?',
        text: `Are you sure you want to disconnect "${channel.channel_title}"? This action cannot be undone.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#b9382a',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Disconnect',
        cancelButtonText: 'Cancel',
        background: isDark.value ? '#0f172a' : '#ffffff',
        color: isDark.value ? '#f8fafc' : '#0f172a'
    });

    if (result.isConfirmed) {
        try {
            await axios.delete(`/api/youtube/channels/${channel.id}`);
            toast.success('Channel disconnected successfully');
            await fetchChannels();
        } catch (error) {
            console.error('Error disconnecting channel:', error);
            toast.error('Failed to disconnect channel');
        }
    }
};

const getChannelThumbnail = (thumbnail) => {
    if (!thumbnail) return '/img/youtube-placeholder.svg';
    return thumbnail;
};

const getTokenStatus = (token) => {
    const expiresAt = new Date(token.expires_at);
    const now = new Date();
    const diffHours = (expiresAt - now) / (1000 * 60 * 60);

    if (diffHours < 0) {
        return { text: 'Expired', color: 'text-[#b9382a] bg-[#fde7dd] dark:bg-slate-800 dark:text-slate-300' };
    } else if (diffHours < 24) {
        return { text: 'Expiring Soon', color: 'text-[#c78c4a] bg-[#f2ebe0] dark:bg-slate-800 dark:text-slate-300' };
    } else {
        return { text: 'Active', color: 'text-[#2f6c73] bg-[#e3f5f4] dark:bg-slate-800 dark:text-slate-200' };
    }
};

onMounted(() => {
    fetchChannels();
});
</script>

<template>
    <Head title="YouTube Channels" />

    <AppLayout>
        <template #header>
            YouTube Channels
        </template>

        <template #actions>
            <button @click="handleConnectChannel" class="group px-5 py-2.5 rounded-full bg-[#0b1021] hover:bg-[#141a2f] text-[#f7f2e8] font-semibold transition-all duration-300 shadow-[0_18px_40px_-24px_rgba(11,16,33,0.7)] flex items-center gap-2 text-sm active:scale-95">
                <svg class="w-4 h-4 transition-transform duration-300 group-hover:rotate-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
                Link Channel
            </button>
        </template>

        <div class="relative overflow-hidden rounded-[32px] border border-[#e6dccf] dark:border-slate-800 bg-[#f7f2e8] dark:bg-slate-900/70 px-8 py-10 mb-10 shadow-[0_30px_60px_-40px_rgba(15,23,42,0.4)]">
            <div class="absolute inset-0 bg-gradient-to-br from-[#fff7ee] via-transparent to-transparent dark:from-slate-900/60"></div>
            <div class="relative">
                <p class="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#6a5d4d] dark:text-slate-400">Channel Registry</p>
                <h1 class="text-3xl font-black text-[#15131a] dark:text-white mt-2">Connected YouTube Channels</h1>
                <p class="text-sm text-[#6a5d4d] dark:text-slate-400 mt-2 max-w-2xl">A curated hub for access tokens, refresh controls, and channel status intelligence.</p>
            </div>
        </div>

        <div v-if="loading" class="flex justify-center py-20">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-[#0b1021] dark:border-white"></div>
        </div>

        <div v-else-if="channels.length === 0" class="text-center py-20 bg-white dark:bg-slate-900 rounded-[28px] border border-[#e6dccf] dark:border-slate-800 shadow-[0_30px_60px_-40px_rgba(15,23,42,0.35)]">
            <svg class="w-16 h-16 mx-auto text-[#d7c9ba] dark:text-slate-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <h3 class="text-lg font-bold text-[#4b3f2f] dark:text-slate-300 mb-2">No channels connected</h3>
            <p class="text-[#6a5d4d] dark:text-slate-400 mb-4">Link a channel to unlock automated publishing and analytics.</p>
            <button @click="handleConnectChannel" class="px-6 py-2.5 bg-[#0b1021] hover:bg-[#141a2f] text-[#f7f2e8] font-semibold rounded-full transition-all duration-300 active:scale-95">Link Channel</button>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6 theme-scrollbar">
            <div v-for="channel in channels" :key="channel.id"
                 class="group bg-white dark:bg-slate-900 rounded-[28px] shadow-[0_30px_60px_-40px_rgba(15,23,42,0.35)] border border-[#e6dccf] dark:border-slate-800 overflow-hidden transition-all duration-300 hover:-translate-y-1">
                <div class="p-6 space-y-5">
                    <div class="flex items-start justify-between">
                        <div class="flex items-center space-x-4">
                            <div class="relative">
                                <img
                                    :src="getChannelThumbnail(channel.channel_thumbnail)"
                                    :alt="channel.channel_title"
                                    class="w-14 h-14 rounded-2xl object-cover ring-2 ring-[#f0e6d8] dark:ring-slate-700"
                                    onerror="this.src='/img/youtube-placeholder.svg'"
                                />
                                <div class="absolute -bottom-2 -right-2 rounded-full bg-[#0b1021] text-[#f7f2e8] text-[10px] font-semibold px-2 py-0.5 shadow-[0_10px_30px_-20px_rgba(11,16,33,0.7)]">
                                    Live
                                </div>
                            </div>
                            <div>
                                <h3 class="text-lg font-bold text-[#15131a] dark:text-white">
                                    {{ channel.channel_title }}
                                </h3>
                                <p class="text-xs text-[#6a5d4d] dark:text-slate-400 font-mono">
                                    {{ channel.channel_id }}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-3 gap-3 text-xs">
                        <div class="rounded-2xl border border-[#efe6d8] dark:border-slate-800 bg-[#fbf7f1] dark:bg-slate-900/60 px-3 py-3 text-center">
                            <div class="text-[10px] uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400">Status</div>
                            <div class="mt-1 text-sm font-semibold" :class="getTokenStatus(channel)">
                                {{ getTokenStatus(channel).text }}
                            </div>
                        </div>
                        <div class="rounded-2xl border border-[#efe6d8] dark:border-slate-800 bg-[#fbf7f1] dark:bg-slate-900/60 px-3 py-3 text-center">
                            <div class="text-[10px] uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400">Expires</div>
                            <div class="mt-1 text-sm font-semibold text-[#15131a] dark:text-white">
                                {{ new Date(channel.expires_at).toLocaleDateString() }}
                            </div>
                        </div>
                        <div class="rounded-2xl border border-[#efe6d8] dark:border-slate-800 bg-[#fbf7f1] dark:bg-slate-900/60 px-3 py-3 text-center">
                            <div class="text-[10px] uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400">Connected</div>
                            <div class="mt-1 text-sm font-semibold text-[#15131a] dark:text-white">
                                {{ new Date(channel.created_at).toLocaleDateString() }}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="px-6 py-4 bg-[#f7f2e8] dark:bg-slate-900/80 border-t border-[#e6dccf] dark:border-slate-800">
                    <div class="flex items-center justify-between gap-2">
                        <button
                            @click="handleRefresh(channel)"
                            class="flex-1 inline-flex items-center justify-center px-3 py-2 text-xs font-semibold text-[#15131a] dark:text-slate-200 bg-white dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 hover:border-[#c7a36c] dark:hover:border-[#c7a36c] hover:text-[#7a4b2a] rounded-full transition-all duration-300 active:scale-95"
                        >
                            <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            Refresh
                        </button>
                        <button
                            @click="handleReconnect(channel)"
                            class="flex-1 inline-flex items-center justify-center px-3 py-2 text-xs font-semibold text-[#15131a] dark:text-slate-200 bg-white dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 hover:border-[#6dd3ce] dark:hover:border-[#6dd3ce] hover:text-[#2f6c73] rounded-full transition-all duration-300 active:scale-95"
                        >
                            <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                            </svg>
                            Reconnect
                        </button>
                        <button
                            @click="handleDisconnect(channel)"
                            class="flex-1 inline-flex items-center justify-center px-3 py-2 text-xs font-semibold text-[#15131a] dark:text-slate-200 bg-white dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 hover:border-[#ff7a59] dark:hover:border-[#ff7a59] hover:text-[#b9382a] rounded-full transition-all duration-300 active:scale-95"
                        >
                            <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                            </svg>
                            Disconnect
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
