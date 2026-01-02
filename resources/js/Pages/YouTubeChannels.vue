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
        confirmButtonColor: '#6366f1',
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
        confirmButtonColor: '#6366f1',
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
        confirmButtonColor: '#ef4444',
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
        return { text: 'Expired', color: 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-400' };
    } else if (diffHours < 24) {
        return { text: 'Expiring Soon', color: 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-400' };
    } else {
        return { text: 'Active', color: 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400' };
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
            <button @click="handleConnectChannel" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg transition-all shadow-sm flex items-center gap-2 text-sm">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
                Connect Channel
            </button>
        </template>

        <div class="mb-8">
            <h1 class="text-3xl font-bold text-slate-900 dark:text-white mb-2">Connected YouTube Channels</h1>
            <p class="text-slate-600 dark:text-slate-400">Manage your YouTube channel connections and access tokens</p>
        </div>

        <div v-if="loading" class="flex justify-center py-20">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>

        <div v-else-if="channels.length === 0" class="text-center py-20 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
            <svg class="w-16 h-16 mx-auto text-slate-300 dark:text-slate-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <h3 class="text-lg font-bold text-slate-700 dark:text-slate-300 mb-2">No channels connected</h3>
            <p class="text-slate-500 dark:text-slate-400 mb-4">Connect your YouTube channel to start uploading videos</p>
            <button @click="handleConnectChannel" class="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg">Connect Channel</button>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6 theme-scrollbar">
            <div v-for="channel in channels" :key="channel.id"
                 class="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
                <div class="p-6">
                    <div class="flex items-start justify-between mb-4">
                        <div class="flex items-center space-x-4">
                            <img
                                :src="getChannelThumbnail(channel.channel_thumbnail)"
                                :alt="channel.channel_title"
                                class="w-14 h-14 rounded-full object-cover ring-2 ring-slate-200 dark:ring-slate-700"
                                onerror="this.src='/img/youtube-placeholder.svg'"
                            />
                            <div>
                                <h3 class="text-lg font-bold text-slate-900 dark:text-white">
                                    {{ channel.channel_title }}
                                </h3>
                                <p class="text-sm text-slate-500 dark:text-slate-400 font-mono">
                                    {{ channel.channel_id }}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div class="space-y-3">
                        <div class="flex items-center justify-between text-sm">
                            <span class="text-slate-600 dark:text-slate-400">Status</span>
                            <span class="px-2 py-1 rounded-full text-xs font-bold" :class="getTokenStatus(channel)">
                                {{ getTokenStatus(channel).text }}
                            </span>
                        </div>
                        <div class="flex items-center justify-between text-sm">
                            <span class="text-slate-600 dark:text-slate-400">Expires</span>
                            <span class="font-bold text-slate-900 dark:text-white">
                                {{ new Date(channel.expires_at).toLocaleDateString() }}
                            </span>
                        </div>
                        <div class="flex items-center justify-between text-sm">
                            <span class="text-slate-600 dark:text-slate-400">Connected</span>
                            <span class="font-bold text-slate-900 dark:text-white">
                                {{ new Date(channel.created_at).toLocaleDateString() }}
                            </span>
                        </div>
                    </div>
                </div>

                <div class="px-6 py-3 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-800">
                    <div class="flex items-center justify-between gap-2">
                        <button
                            @click="handleRefresh(channel)"
                            class="flex-1 inline-flex items-center justify-center px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-200 dark:bg-slate-700 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 hover:text-indigo-600 dark:hover:text-indigo-400 rounded-lg transition-colors"
                        >
                            <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            Refresh
                        </button>
                        <button
                            @click="handleReconnect(channel)"
                            class="flex-1 inline-flex items-center justify-center px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-200 dark:bg-slate-700 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 hover:text-indigo-600 dark:hover:text-indigo-400 rounded-lg transition-colors"
                        >
                            <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                            </svg>
                            Reconnect
                        </button>
                        <button
                            @click="handleDisconnect(channel)"
                            class="flex-1 inline-flex items-center justify-center px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-200 dark:bg-slate-700 hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-600 dark:hover:text-red-400 rounded-lg transition-colors"
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
