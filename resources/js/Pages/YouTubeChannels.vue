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
        confirmButtonColor: '#00f0ff',
        cancelButtonColor: '#333333',
        confirmButtonText: 'Reconnect',
        cancelButtonText: 'Cancel',
        background: '#111111',
        color: '#ffffff'
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
        confirmButtonColor: '#00f0ff',
        cancelButtonColor: '#333333',
        confirmButtonText: 'Refresh',
        cancelButtonText: 'Cancel',
        background: '#111111',
        color: '#ffffff'
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
        confirmButtonColor: '#ff00ff',
        cancelButtonColor: '#333333',
        confirmButtonText: 'Disconnect',
        cancelButtonText: 'Cancel',
        background: '#111111',
        color: '#ffffff'
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
        return { text: 'Expired', color: 'text-[#ff00ff] bg-[#1a1a1a] border border-[#ff00ff]/30' };
    } else if (diffHours < 24) {
        return { text: 'Expiring Soon', color: 'text-[#ffaa00] bg-[#1a1a1a] border border-[#ffaa00]/30' };
    } else {
        return { text: 'Active', color: 'text-[#00ff41] bg-[#1a1a1a] border border-[#00ff41]/30' };
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
            <button @click="handleConnectChannel" class="group cyber-btn px-4 py-2.5 font-semibold flex items-center gap-2 text-sm">
                <svg class="w-4 h-4 transition-transform duration-300 group-hover:rotate-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
                Link Channel
            </button>
        </template>

        <div class="relative overflow-hidden rounded-sm border border-[#222222] bg-[#111111] px-6 py-8 mb-8 shadow-[0_0_30px_rgba(0,240,255,0.05)] holographic">
            <div class="absolute inset-0 bg-gradient-to-br from-[#00f0ff]/5 via-transparent to-transparent"></div>
            <div class="relative">
                <p class="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#00f0ff] font-terminal">Channel Registry</p>
                <h1 class="text-3xl font-black text-white mt-2 font-cyber">Connected YouTube Channels</h1>
                <p class="text-sm text-[#666666] mt-2 max-w-2xl">A curated hub for access tokens, refresh controls, and channel status intelligence.</p>
            </div>
        </div>

        <div v-if="loading" class="flex justify-center py-16">
            <div class="relative w-12 h-12">
                <div class="absolute inset-0 border-4 border-[#00f0ff]/20 rounded-sm"></div>
                <div class="absolute inset-0 border-4 border-[#00f0ff] border-t-transparent animate-spin rounded-sm"></div>
            </div>
        </div>

        <div v-else-if="channels.length === 0" class="text-center py-16 bg-[#1a1a1a] rounded-sm border border-[#222222] shadow-[0_0_30px_rgba(0,240,255,0.08)]">
            <svg class="w-14 h-14 mx-auto text-[#333333] mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <h3 class="text-base font-bold text-white mb-2 font-cyber">No channels connected</h3>
            <p class="text-[#666666] mb-4 text-sm">Link a channel to unlock automated publishing and analytics.</p>
            <button @click="handleConnectChannel" class="cyber-btn px-5 py-2.5 font-semibold">Link Channel</button>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-5 theme-scrollbar">
            <div v-for="channel in channels" :key="channel.id"
                 class="group bg-[#1a1a1a] rounded-sm shadow-[0_0_30px_rgba(0,240,255,0.08)] border border-[#222222] overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:border-[#00f0ff]/30">
                <div class="p-5 space-y-4">
                    <div class="flex items-start justify-between">
                        <div class="flex items-center space-x-3">
                            <div class="relative">
                                <img
                                    :src="getChannelThumbnail(channel.channel_thumbnail)"
                                    :alt="channel.channel_title"
                                    class="w-12 h-12 rounded-sm object-cover ring-1 ring-[#333333]"
                                    onerror="this.src='/img/youtube-placeholder.svg'"
                                />
                                <div class="absolute -bottom-1 -right-1 rounded-sm bg-[#00ff41] text-[#0a0a0a] text-[9px] font-semibold px-1.5 py-0.5 neon-glow-green">
                                    Live
                                </div>
                            </div>
                            <div>
                                <h3 class="text-base font-bold text-white">
                                    {{ channel.channel_title }}
                                </h3>
                                <p class="text-xs text-[#666666] font-terminal">
                                    {{ channel.channel_id }}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-3 gap-2 text-xs">
                        <div class="rounded-sm border border-[#333333] bg-[#222222] px-2 py-2.5 text-center">
                            <div class="text-[9px] uppercase tracking-[0.2em] text-[#666666] font-terminal">Status</div>
                            <div class="mt-1 text-xs font-semibold" :class="getTokenStatus(channel)">
                                {{ getTokenStatus(channel).text }}
                            </div>
                        </div>
                        <div class="rounded-sm border border-[#333333] bg-[#222222] px-2 py-2.5 text-center">
                            <div class="text-[9px] uppercase tracking-[0.2em] text-[#666666] font-terminal">Expires</div>
                            <div class="mt-1 text-xs font-semibold text-white">
                                {{ new Date(channel.expires_at).toLocaleDateString() }}
                            </div>
                        </div>
                        <div class="rounded-sm border border-[#333333] bg-[#222222] px-2 py-2.5 text-center">
                            <div class="text-[9px] uppercase tracking-[0.2em] text-[#666666] font-terminal">Connected</div>
                            <div class="mt-1 text-xs font-semibold text-white">
                                {{ new Date(channel.created_at).toLocaleDateString() }}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="px-5 py-3 bg-[#0a0a0a]/80 border-t border-[#222222]">
                    <div class="flex items-center justify-between gap-2">
                        <button
                            @click="handleRefresh(channel)"
                            class="flex-1 inline-flex items-center justify-center px-2 py-2 text-xs font-semibold text-white bg-[#222222] border border-[#333333] hover:border-[#00ff41] hover:text-[#00ff41] rounded-sm transition-all duration-300"
                        >
                            <svg class="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            Refresh
                        </button>
                        <button
                            @click="handleReconnect(channel)"
                            class="flex-1 inline-flex items-center justify-center px-2 py-2 text-xs font-semibold text-white bg-[#222222] border border-[#333333] hover:border-[#00f0ff] hover:text-[#00f0ff] rounded-sm transition-all duration-300"
                        >
                            <svg class="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                            </svg>
                            Reconnect
                        </button>
                        <button
                            @click="handleDisconnect(channel)"
                            class="flex-1 inline-flex items-center justify-center px-2 py-2 text-xs font-semibold text-white bg-[#222222] border border-[#333333] hover:border-[#ff00ff] hover:text-[#ff00ff] rounded-sm transition-all duration-300"
                        >
                            <svg class="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
