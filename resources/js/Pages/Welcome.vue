<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { Head, Link } from '@inertiajs/vue3';
import { useForm } from '@inertiajs/vue3';
import axios from 'axios';
import AppLayout from '@/Layouts/AppLayout.vue';
import StoryCard from '@/Components/StoryCard.vue';
import PublishModal from '@/Components/PublishModal.vue';
import ScheduleModal from '@/Components/ScheduleModal.vue';
import ScenesModal from '@/Components/ScenesModal.vue';
import { useToast } from 'vue-toast-notification';
import Swal from 'sweetalert2';

const props = defineProps({
    auth: Object
});

const toast = useToast();
const stories = ref([]);
const pagination = ref(null);
const loading = ref(false);
const generating = ref(false);
const searching_news = ref(false);
const news_results = ref([]);
const showYoutubeSettings = ref(false);
const showPublishModal = ref(false);
const showScheduleModal = ref(false);
const showScenesModal = ref(false);
const publishingStory = ref(null);
const schedulingStory = ref(null);
const editingScenesStory = ref(null);
const channels = ref([]);
const selectedChannelId = ref(null);
const isDark = ref(false);
const loadingChannels = ref(false);
const sortBy = ref('latest');
const styleTab = ref('script'); // 'script' or 'talking'

const newStory = ref({
    title: '',
    content: '',
    style: 'story',
    talking_style: 'none',
    aspect_ratio: '16:9',
    youtube_title: '',
    youtube_description: '',
    youtube_tags: '',
    youtube_token_id: null,
    search_query: ''
});

const searchConfig = computed(() => {
    const style = newStory.value.style;
    if (style === 'hollywood_hype') {
        return {
            visible: true,
            borderClass: 'border-l-4 border-l-[#b9382a]',
            iconBg: 'bg-[#fde7dd] dark:bg-red-900/20 border-[#b9382a]/20 text-[#b9382a] dark:text-[#ff7a59]',
            title: 'Hollywood News',
            placeholder: 'e.g. Dakota Johnson latest news...'
        };
    } else if (style === 'bollywood_masala') {
        return {
            visible: true,
            borderClass: 'border-l-4 border-l-[#c7a36c]',
            iconBg: 'bg-[#fff7ee] dark:bg-orange-900/20 border-[#c7a36c]/20 text-[#c7a36c] dark:text-[#f0c05a]',
            title: 'Bollywood Masala News',
            placeholder: 'e.g. SRK new movie, Pathaan box office...'
        };
    } else if (style === 'trade_wave') {
        return {
            visible: true,
            borderClass: 'border-l-4 border-l-[#2f6c73]',
            iconBg: 'bg-[#e3f5f4] dark:bg-emerald-900/20 border-[#2f6c73]/20 text-[#2f6c73] dark:text-[#6dd3ce]',
            title: 'Market Updates',
            placeholder: 'e.g. Bitcoin price action today...'
        };
    }
    return { visible: false };
});

const fetchStories = async (page = 1) => {
    try {
        let url = `/api/stories?page=${page}`;
        if (selectedChannelId.value) {
            url += `&channel_id=${selectedChannelId.value}`;
        }
        const response = await axios.get(url);
        stories.value = response.data.data;
        pagination.value = response.data;
        sortStories();
    } catch (error) {
        console.error('Error fetching stories:', error);
    }
};

const sortStories = () => {
    if (sortBy.value === 'latest') {
        stories.value.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } else if (sortBy.value === 'oldest') {
        stories.value.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    } else if (sortBy.value === 'schedule') {
        stories.value.sort((a, b) => {
            if (!a.scheduled_at && !b.scheduled_at) return 0;
            if (!a.scheduled_at) return 1;
            if (!b.scheduled_at) return -1;
            return new Date(a.scheduled_at) - new Date(b.scheduled_at);
        });
    }
};

const selectChannel = (channelId) => {
    if (selectedChannelId.value === channelId) {
        selectedChannelId.value = null;
    } else {
        selectedChannelId.value = channelId;
    }
    fetchStories(1);
};

const fetchChannels = async () => {
    loadingChannels.value = true;
    try {
        const response = await axios.get('/api/youtube/channels');
        channels.value = response.data;
    } catch (error) {
        console.error('Error fetching channels:', error);
    } finally {
        loadingChannels.value = false;
    }
};

onMounted(() => {
    isDark.value = document.documentElement.classList.contains('dark');
    fetchStories();
    fetchChannels();
    setInterval(() => fetchStories(pagination.value?.current_page || 1), 5000);
});

watch(() => newStory.value.style, (newStyle) => {
    if (channels.value.length === 0) return;
    let targetTitle = '';
    if (newStyle === 'science_short') targetTitle = 'The 60s Lab';
    else if (newStyle === 'hollywood_hype') targetTitle = 'Hollywood Hype';
    else if (newStyle === 'bollywood_masala') targetTitle = 'Bollywood Masala';
    else if (newStyle === 'trade_wave') targetTitle = 'TradeWave';

    if (targetTitle) {
        const channel = channels.value.find(c => c.channel_title.includes(targetTitle));
        if (channel) newStory.value.youtube_token_id = channel.id;
    }
});

watch(sortBy, () => {
    sortStories();
});

const submitStory = async () => {
    if (!newStory.value.content || newStory.value.content.length < 10) {
        toast.error('Please provide a longer story description.');
        return;
    }
    loading.value = true;
    try {
        await axios.post('/api/stories', newStory.value);
        toast.success('Story created successfully!');

        const currentStyle = newStory.value.style;
        const currentTalkingStyle = newStory.value.talking_style;
        const currentAspectRatio = newStory.value.aspect_ratio;
        const currentYoutubeTokenId = newStory.value.youtube_token_id;

        newStory.value = {
            title: '',
            content: '',
            style: currentStyle,
            talking_style: currentTalkingStyle,
            aspect_ratio: currentAspectRatio,
            youtube_title: '',
            youtube_description: '',
            youtube_tags: '',
            youtube_token_id: currentYoutubeTokenId,
            search_query: ''
        };
        fetchStories();
    } catch (error) {
        console.error('Error creating story:', error);
    } finally {
        loading.value = false;
    }
};

const generateStory = async () => {
    generating.value = true;
    try {
        const response = await axios.post('/api/ai/generate-story', {
            title: newStory.value.title || 'a random interesting story',
            style: newStory.value.style,
            talking_style: newStory.value.talking_style,
            aspect_ratio: newStory.value.aspect_ratio
        });

        if (!newStory.value.title && response.data.title) {
            newStory.value.title = response.data.title;
        }

        newStory.value.content = response.data.content;

        newStory.value.youtube_title = response.data.youtube_title || response.data.title;
        newStory.value.youtube_description = response.data.youtube_description || response.data.content;
        newStory.value.youtube_tags = response.data.youtube_tags || 'ai, story, animation';

        showYoutubeSettings.value = true;
    } catch (error) {
        console.error('Error generating story:', error);
    } finally {
        generating.value = false;
    }
};

const searchNews = async () => {
    if (!newStory.value.search_query) {
        toast.warning('Please enter a search query');
        return;
    }
    searching_news.value = true;
    news_results.value = []; // Clear previous results
    try {
        const response = await axios.post('/api/ai/search-news', {
            query: newStory.value.search_query,
            style: newStory.value.style
        });

        console.log('News API Response:', response.data);

        let results = [];

        // Handle various response formats
        if (Array.isArray(response.data)) {
            results = response.data;
        } else if (response.data && typeof response.data === 'object') {
            // Check for common wrapper keys
            const possibleKeys = ['news', 'results', 'items', 'data', 'articles'];
            for (const key of possibleKeys) {
                if (Array.isArray(response.data[key])) {
                    results = response.data[key];
                    break;
                }
            }
            // Check for error
            if (response.data.error) {
                toast.error(response.data.error);
                return;
            }
        }

        // Filter to ensure each item has title and snippet
        news_results.value = results.filter(item => item && item.title && item.snippet);

        console.log('Parsed news results:', news_results.value);

        if (news_results.value.length === 0) {
            toast.info('No news found for this query. Try a different search term.');
        } else {
            toast.success(`Found ${news_results.value.length} news items!`);
        }
    } catch (error) {
        console.error('Error searching news:', error);
        if (error.response && error.response.data && error.response.data.error) {
            toast.error(error.response.data.error);
        } else if (error.message) {
            toast.error('Search failed: ' + error.message);
        } else {
            toast.error('Failed to search news. Please try again.');
        }
    } finally {
        searching_news.value = false;
    }
};

const selectNews = (news) => {
    newStory.value.title = news.title;
    newStory.value.content = news.snippet;
    news_results.value = [];
};

const regenerateVideo = async (story) => {
    const result = await Swal.fire({
        title: 'Regenerate Video?',
        text: 'Re-run AI generation for this story? Existing video will be replaced.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#0b1021',
        cancelButtonColor: '#94a3b8',
        confirmButtonText: 'Yes, regenerate it!',
        background: isDark.value ? '#0f172a' : '#ffffff',
        color: isDark.value ? '#f8fafc' : '#0f172a'
    });

    if (!result.isConfirmed) return;

    try {
        story.status = 'pending';
        await axios.post(`/api/stories/${story.id}/regenerate`);
        toast.info('Video regeneration started.');
        fetchStories();
    } catch (error) {
        console.error('Error regenerating story:', error);
        toast.error('Failed to regenerate video.');
    }
};

const deleteStory = async (story) => {
    const result = await Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#b9382a',
        cancelButtonColor: '#94a3b8',
        confirmButtonText: 'Yes, delete it!',
        background: isDark.value ? '#0f172a' : '#ffffff',
        color: isDark.value ? '#f8fafc' : '#0f172a'
    });

    if (!result.isConfirmed) return;

    try {
        await axios.delete(`/api/stories/${story.id}`);
        toast.success('Story deleted.');
        fetchStories();
    } catch (error) {
        console.error('Error deleting story:', error);
        toast.error('Failed to delete story.');
    }
};

const openPublishModal = (story) => {
    publishingStory.value = story;
    showPublishModal.value = true;
};

const confirmPublish = async (formData) => {
    try {
        showPublishModal.value = false;
        await axios.patch(`/api/stories/${publishingStory.value.id}`, formData);
        await axios.post(`/api/stories/${publishingStory.value.id}/upload`);
        toast.success('Upload queued successfully!');
        fetchStories();
    } catch (error) {
        console.error('Error publishing story:', error);
        toast.error('Failed to start upload. Please try again.');
    }
};

const openScheduleModal = (story) => {
    schedulingStory.value = story;
    showScheduleModal.value = true;
};

const openScenesModal = (story) => {
    editingScenesStory.value = story;
    showScenesModal.value = true;
};

const confirmSchedule = async (scheduleData) => {
    try {
        showScheduleModal.value = false;
        await axios.post(`/api/stories/${schedulingStory.value.id}/schedule`, scheduleData);
        toast.success('Story scheduled successfully!');
        fetchStories();
    } catch (error) {
        console.error('Error scheduling story:', error);
        if (error.response && error.response.data && error.response.data.errors) {
            Object.values(error.response.data.errors).flat().forEach(msg => toast.error(msg));
        } else {
            toast.error('Failed to schedule story.');
        }
    }
};
</script>

<template>
    <AppLayout>

        <Head title="Dashboard" />

        <template #header>
            Dashboard
        </template>

        <template #actions>
            <div class="flex items-center gap-3">
                <div v-if="channels.length > 0"
                    class="hidden lg:flex items-center gap-2 pr-3 border-r border-[#e6dccf] dark:border-slate-700 overflow-x-auto max-w-md custom-scrollbar scroll-smooth">
                    <button @click="selectChannel(null)"
                        :class="['px-4 py-2 rounded-full text-[11px] font-semibold uppercase tracking-[0.2em] transition-all whitespace-nowrap',
                            !selectedChannelId ? 'bg-[#0b1021] text-[#f7f2e8] shadow-[0_12px_30px_-20px_rgba(11,16,33,0.7)]' : 'bg-white dark:bg-slate-900 border border-[#efe6d8] dark:border-slate-800 text-[#6a5d4d] dark:text-slate-300 hover:border-[#c7a36c]']">
                        All
                    </button>
                    <button v-for="channel in channels" :key="'yt-' + channel.id" @click="selectChannel(channel.id)"
                        :class="['flex items-center space-x-2 px-3 py-2 rounded-full transition-all border',
                            selectedChannelId === channel.id ? 'bg-[#0b1021] text-[#f7f2e8] border-[#0b1021] shadow-[0_12px_30px_-20px_rgba(11,16,33,0.7)]' : 'bg-white dark:bg-slate-900 border-[#efe6d8] dark:border-slate-800 hover:border-[#c7a36c] text-[#6a5d4d] dark:text-slate-300']"
                        :title="channel.channel_title">
                        <img :src="channel.channel_thumbnail"
                            class="w-5 h-5 rounded-full border border-[#efe6d8] dark:border-slate-700">
                        <span class="text-[11px] font-semibold uppercase tracking-[0.12em]s truncate max-w-[90px]">{{
                            channel.channel_title }}</span>
                    </button>
                </div>
            </div>
        </template>

        <div
            class="relative rounded-[2.5rem] border border-[#e6dccf] dark:border-slate-800 p-6 lg:p-10 overflow-hidden bg-[#f7f2e8] dark:bg-slate-900/70 shadow-[0_40px_80px_-50px_rgba(11,16,33,0.45)]">

            <div class="grid   gap-8">
                <div class="lg:col-span-8 space-y-6">
                    <div
                        class="relative rounded-[2rem] overflow-hidden border border-[#efe6d8] dark:border-slate-800 bg-white/80 dark:bg-slate-900/70 shadow-[0_20px_40px_-30px_rgba(11,16,33,0.45)]">
                        <div
                            class="px-8 py-6 border-b border-[#efe6d8] dark:border-slate-800 bg-white/60 dark:bg-slate-900/60">
                            <div class="flex items-center justify-between">
                                <div>
                                    <p
                                        class="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#6a5d4d] dark:text-slate-400">
                                        Story Forge</p>
                                    <h2 class="text-2xl font-black text-[#15131a] dark:text-white mb-1 tracking-tight">
                                        Create
                                        New Story</h2>
                                    <p class="text-[#6a5d4d] dark:text-slate-400 text-sm">Compose, refine, and publish
                                        in one
                                        continuous flow.</p>
                                </div>
                                <div
                                    class="flex items-center gap-2 rounded-full px-4 py-2 border border-[#efe6d8] dark:border-slate-800 bg-white/80 dark:bg-slate-900/60">
                                    <div class="w-2 h-2 bg-[#6dd3ce] rounded-full"></div>
                                    <span
                                        class="text-[#6a5d4d] dark:text-slate-200 text-xs font-semibold uppercase tracking-[0.2em]">Ready</span>
                                </div>
                            </div>
                        </div>

                        <div class="p-8">
                            <!-- Script Style Section -->
                            <div class="mb-8">
                                <label class="block text-[#15131a] dark:text-white text-sm font-black mb-4">
                                    <span class="flex items-center gap-2">
                                        <svg class="w-4 h-4 text-[#6a5d4d] dark:text-slate-300" fill="none"
                                            stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z">
                                            </path>
                                        </svg>
                                        Content Style
                                    </span>
                                </label>
                                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                                    <div v-for="style in [
                                        { id: 'story', name: 'General Story', desc: 'Any topic', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5S19.832 5.477 21 6.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253', accent: 'text-[#0b1021] dark:text-slate-300', dot: 'bg-[#0b1021]' },
                                        { id: 'science_short', name: '60s Lab', desc: 'Science facts', icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.691.34a2 2 0 01-1.782 0l-.691-.34a6 6 0 00-3.86-.517l-2.387.477a2 2 0 00-1.022.547V18a2 2 0 002 2h12a2 2 0 002-2v-2.572zM12 11V3.5', accent: 'text-[#4b3f2f] dark:text-slate-400', dot: 'bg-[#4b3f2f]' },
                                        { id: 'hollywood_hype', name: 'Hollywood', desc: 'Entertainment', icon: 'M7 4V20M17 4V20M3 8H7M17 8H21M3 12H21M3 16H7M17 16H21M4 20H20C21.1046 20 22 19.1046 22 18V6C22 4.89543 21.1046 4 20 4H4C2.89543 4 2 4.89543 2 6V18C2 19.1046 2.89543 20 4 20Z', accent: 'text-[#b9382a] dark:text-[#ff7a59]', dot: 'bg-[#b9382a]' },
                                        { id: 'bollywood_masala', name: 'Bollywood', desc: 'Masala News', icon: 'M7 4V20M17 4V20M3 8H7M17 8H21M3 12H21M3 16H7M17 16H21M4 20H20C21.1046 20 22 19.1046 22 18V6C22 4.89543 21.1046 4 20 4H4C2.89543 4 2 4.89543 2 6V18C2 19.1046 2.89543 20 4 20Z', accent: 'text-[#c7a36c] dark:text-[#f0c05a]', dot: 'bg-[#c7a36c]' },
                                        { id: 'trade_wave', name: 'TradeWave', desc: 'Finance', icon: 'M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z', accent: 'text-[#2f6c73] dark:text-[#6dd3ce]', dot: 'bg-[#2f6c73]' }
                                    ]" :key="style.id" @click="newStory.style = style.id"
                                        :class="['cursor-pointer p-5 rounded-2xl border transition-all duration-300 flex flex-col items-start text-left space-y-3 group hover:-translate-y-0.5',
                                            newStory.style === style.id ? 'border-[#0b1021] dark:border-white bg-white dark:bg-slate-900 shadow-[0_20px_40px_-30px_rgba(11,16,33,0.45)]' : 'border-[#efe6d8] dark:border-slate-800 hover:border-[#c7a36c] bg-white/70 dark:bg-slate-900/60']">
                                        <div class="w-full flex items-center justify-between">
                                            <div class="flex items-center gap-2">
                                                <div :class="['w-2 h-2 rounded-full', style.dot]"></div>
                                                <span class="text-xs font-bold uppercase tracking-wider"
                                                    :class="style.accent">{{ style.name }}</span>
                                            </div>
                                            <div
                                                :class="['w-10 h-10 rounded-xl flex items-center justify-center border transition-all shrink-0',
                                                    newStory.style === style.id ? 'border-[#efe6d8] dark:border-slate-800 bg-[#f7f2e8] dark:bg-slate-800' : 'border-[#efe6d8] dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 group-hover:bg-[#fbf7f1] dark:group-hover:bg-slate-800']">
                                                <svg :class="['w-7 h-7', style.accent, newStory.style === style.id ? 'opacity-100' : 'opacity-75 group-hover:opacity-95']"
                                                    fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        stroke-width="2" :d="style.icon"></path>
                                                </svg>
                                            </div>
                                        </div>
                                        <p class="text-[11px] text-[#6a5d4d] dark:text-slate-400 leading-snug">{{
                                            style.desc }}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <!-- Talking Style Section -->
                            <div class="mb-8">
                                <label class="block text-[#15131a] dark:text-white text-sm font-black mb-4">
                                    <span class="flex items-center gap-2">
                                        <svg class="w-4 h-4 text-[#6a5d4d] dark:text-slate-300" fill="none"
                                            stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z">
                                            </path>
                                        </svg>
                                        Talking Style <span
                                            class="text-[#b3a799] dark:text-slate-500 font-normal">(Optional)</span>
                                    </span>
                                </label>
                                <div class="grid grid-cols-3 md:grid-cols-6 gap-3">
                                    <div v-for="style in [
                                        { id: 'none', name: 'None', desc: 'Default', icon: 'M6 18L18 6M6 6l12 12' },
                                        { id: 'opinion', name: 'Opinion', desc: 'Hot takes', icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' },
                                        { id: 'storytime', name: 'Storytime', desc: 'Personal', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5S19.832 5.477 21 6.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
                                        { id: 'educational', name: 'Edu', desc: 'Explain', icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z' },
                                        { id: 'reaction', name: 'Reaction', desc: 'React', icon: 'M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
                                        { id: 'vlog', name: 'Vlog', desc: 'Casual', icon: 'M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z' }
                                    ]" :key="style.id" @click="newStory.talking_style = style.id"
                                        :class="['cursor-pointer p-3 rounded-2xl border transition-all duration-300 flex flex-col items-center text-center space-y-1 hover:-translate-y-0.5',
                                            newStory.talking_style === style.id ? 'border-[#0b1021] dark:border-white bg-white dark:bg-slate-900 shadow-[0_20px_40px_-30px_rgba(11,16,33,0.45)]' : 'border-[#efe6d8] dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 hover:border-[#c7a36c]']">
                                        <div
                                            :class="['w-9 h-9 rounded-xl flex items-center justify-center transition-all border',
                                                newStory.talking_style === style.id ? 'border-[#efe6d8] dark:border-slate-800 bg-[#f7f2e8] dark:bg-slate-800 text-[#0b1021] dark:text-white' : 'border-[#efe6d8] dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 text-[#4b3f2f] dark:text-slate-200 group-hover:bg-[#fbf7f1] dark:group-hover:bg-slate-800']">
                                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                    :d="style.icon"></path>
                                            </svg>
                                        </div>
                                        <span
                                            class="block text-[10px] font-bold uppercase tracking-wider text-[#4b3f2f] dark:text-slate-200">{{
                                            style.name }}</span>
                                    </div>
                                </div>
                            </div>

                            <div v-if="searchConfig.visible"
                                class="mb-8 p-6 rounded-2xl animate-in fade-in slide-in-from-top-4 duration-300 bg-white/90 dark:bg-slate-900/70 border border-[#efe6d8] dark:border-slate-800"
                                :class="searchConfig.borderClass">
                                <div class="flex items-center space-x-3 mb-4">
                                    <div
                                        :class="['w-10 h-10 rounded-xl flex items-center justify-center border', searchConfig.iconBg]">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z">
                                            </path>
                                        </svg>
                                    </div>
                                    <h3 class="font-bold text-lg text-[#15131a] dark:text-white">
                                        {{ searchConfig.title }}
                                    </h3>
                                </div>
                                <div class="flex space-x-3 mb-4">
                                    <input v-model="newStory.search_query" type="text"
                                        class="flex-1 px-5 py-3.5 bg-white dark:bg-slate-900 border border-[#efe6d8] dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#c7a36c]/40 transition-all shadow-sm dark:text-white text-sm"
                                        :placeholder="searchConfig.placeholder">
                                    <button @click="searchNews" :disabled="searching_news"
                                        class="px-6 py-3.5 rounded-full font-semibold disabled:opacity-50 text-sm flex items-center bg-[#0b1021] dark:bg-white text-[#f7f2e8] dark:text-slate-900 border border-[#0b1021] dark:border-white hover:bg-[#141a2f] dark:hover:bg-slate-100 transition-colors shadow-[0_18px_40px_-24px_rgba(11,16,33,0.7)]">
                                        <svg v-if="searching_news" class="animate-spin h-5 w-5 mr-2"
                                            viewBox="0 0 24 24">
                                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                                stroke-width="4"></circle>
                                            <path class="opacity-75" fill="currentColor"
                                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                                            </path>
                                        </svg>
                                        <span>{{ searching_news ? 'Searching...' : 'Search' }}</span>
                                    </button>
                                </div>
                                <div v-if="news_results.length > 0"
                                    class="space-y-3 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                                    <div v-for="(news, index) in news_results" :key="index" @click="selectNews(news)"
                                        class="p-4 bg-white dark:bg-slate-900 border border-[#efe6d8] dark:border-slate-800 rounded-xl cursor-pointer hover:shadow-[0_20px_40px_-30px_rgba(11,16,33,0.35)] hover:border-[#c7a36c] transition-all group">
                                        <p
                                            class="font-bold text-[#15131a] dark:text-slate-200 group-hover:text-[#0b1021] dark:group-hover:text-white mb-1 text-sm">
                                            {{ news.title }}</p>
                                        <p
                                            class="text-xs text-[#6a5d4d] dark:text-slate-400 line-clamp-2 leading-relaxed">
                                            {{
                                            news.snippet }}</p>
                                    </div>
                                </div>
                            </div>

                            <div class="space-y-6">
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <label class="block text-[#15131a] dark:text-white text-sm font-bold mb-3">Video
                                            Format</label>
                                        <div
                                            class="flex p-1.5 bg-white/80 dark:bg-slate-900/70 border border-[#efe6d8] dark:border-slate-800 rounded-2xl">
                                            <button v-for="ratio in ['16:9', '9:16']" :key="ratio"
                                                @click="newStory.aspect_ratio = ratio"
                                                :class="['flex-1 py-3 text-sm font-bold rounded-xl transition-all flex items-center justify-center gap-2',
                                                    newStory.aspect_ratio === ratio ? 'bg-[#0b1021] text-[#f7f2e8] shadow-[0_12px_30px_-20px_rgba(11,16,33,0.6)]' : 'text-[#6a5d4d] dark:text-slate-300 hover:text-[#0b1021] dark:hover:text-white']">
                                                <svg class="w-5 h-5" fill="none" stroke="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        stroke-width="2"
                                                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z">
                                                    </path>
                                                </svg>
                                                {{ ratio === '16:9' ? 'Landscape' : 'Shorts' }}
                                            </button>
                                        </div>
                                    </div>
                                    <div>
                                        <label class="block text-[#15131a] dark:text-white text-sm font-bold mb-3">Story
                                            Title</label>
                                        <input v-model="newStory.title" type="text"
                                            class="w-full px-5 py-3.5 bg-white dark:bg-slate-900 border border-[#efe6d8] dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#c7a36c]/40 transition-all dark:text-white text-sm"
                                            placeholder="A magical journey through...">
                                    </div>
                                </div>

                                <div>
                                    <label class="block text-[#15131a] dark:text-white text-sm font-bold mb-3">The
                                        Story</label>
                                    <textarea v-model="newStory.content" rows="6"
                                        class="w-full px-5 py-4 bg-white dark:bg-slate-900 border border-[#efe6d8] dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#c7a36c]/40 transition-all dark:text-white text-sm resize-none"
                                        placeholder="Tell your story in detail... (minimum 10 characters)"></textarea>
                                </div>

                                <div
                                    class="border border-[#efe6d8] dark:border-slate-800 rounded-2xl overflow-hidden bg-[#fbf7f1] dark:bg-slate-900/60">
                                    <button @click="showYoutubeSettings = !showYoutubeSettings"
                                        class="w-full px-6 py-4 flex items-center justify-between hover:bg-[#f2ebe0] dark:hover:bg-slate-900/80 transition-colors">
                                        <div class="flex items-center space-x-3">
                                            <div
                                                class="w-10 h-10 rounded-xl bg-[#b9382a] flex items-center justify-center">
                                                <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                                                    <path
                                                        d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                                                </svg>
                                            </div>
                                            <div class="text-left">
                                                <span class="block font-bold text-[#15131a] dark:text-white">YouTube
                                                    Automations</span>
                                                <span
                                                    class="block text-xs text-[#6a5d4d] dark:text-slate-400">Auto-upload
                                                    with
                                                    AI-optimized metadata</span>
                                            </div>
                                        </div>
                                        <svg :class="{ 'rotate-180': showYoutubeSettings }"
                                            class="w-5 h-5 text-[#b3a799] dark:text-slate-500 transition-transform"
                                            fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M19 9l-7 7-7-7"></path>
                                        </svg>
                                    </button>

                                    <div v-show="showYoutubeSettings" class="px-6 pb-6 space-y-5">
                                        <div v-if="channels.length > 0">
                                            <label
                                                class="block text-[#6a5d4d] dark:text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-3">Target
                                                Channel</label>
                                            <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                                                <div v-for="channel in channels" :key="channel.id"
                                                    @click="newStory.youtube_token_id = channel.id"
                                                    :class="['flex items-center p-3.5 border-2 rounded-xl cursor-pointer transition-all',
                                                        newStory.youtube_token_id === channel.id ? 'border-red-500 bg-red-50 dark:bg-red-950/20 shadow-sm' : 'bg-white dark:bg-slate-900 border-[#efe6d8] dark:border-slate-800 hover:border-[#c7a36c]']">
                                                    <img :src="channel.channel_thumbnail"
                                                        class="w-10 h-10 rounded-full shadow-sm mr-3">
                                                    <span
                                                        class="text-xs font-bold truncate text-[#4b3f2f] dark:text-slate-200">{{
                                                        channel.channel_title }}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <label
                                                    class="block text-[#6a5d4d] dark:text-slate-400 text-[10px] font-bold uppercase mb-2">YouTube
                                                    Title</label>
                                                <input v-model="newStory.youtube_title" type="text"
                                                    class="w-full px-4 py-3 text-sm bg-white dark:bg-slate-900 border border-[#efe6d8] dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-[#c7a36c]/40 outline-none dark:text-white"
                                                    placeholder="Default: Story Title">
                                            </div>
                                            <div>
                                                <label
                                                    class="block text-[#6a5d4d] dark:text-slate-400 text-[10px] font-bold uppercase mb-2">Tags</label>
                                                <input v-model="newStory.youtube_tags" type="text"
                                                    class="w-full px-4 py-3 text-sm bg-white dark:bg-slate-900 border border-[#efe6d8] dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-[#c7a36c]/40 outline-none dark:text-white"
                                                    placeholder="story, ai, animation">
                                            </div>
                                        </div>
                                        <div>
                                            <label
                                                class="block text-[#6a5d4d] dark:text-slate-400 text-[10px] font-bold uppercase mb-2">Description</label>
                                            <textarea v-model="newStory.youtube_description" rows="3"
                                                class="w-full px-4 py-3 text-sm bg-white dark:bg-slate-900 border border-[#efe6d8] dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-[#c7a36c]/40 outline-none dark:text-white resize-none"
                                                placeholder="Default: Story Content"></textarea>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4 mt-10">
                                <button @click="submitStory" :disabled="loading || generating"
                                    class="flex-1 bg-[#0b1021] hover:bg-[#141a2f] dark:bg-white dark:hover:bg-slate-100 text-[#f7f2e8] dark:text-slate-900 font-bold py-4 px-8 rounded-2xl transition-all shadow-[0_18px_40px_-24px_rgba(11,16,33,0.7)] border border-[#0b1021] dark:border-white disabled:opacity-50 flex items-center justify-center space-x-2">
                                    <svg v-if="loading" class="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                            stroke-width="4"></circle>
                                        <path class="opacity-75" fill="currentColor"
                                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                                        </path>
                                    </svg>
                                    <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z">
                                        </path>
                                    </svg>
                                    <span>{{ loading ? 'Processing...' : 'Generate Video' }}</span>
                                </button>
                                <button @click="generateStory" :disabled="loading || generating"
                                    class="flex-1 bg-white hover:bg-[#f7f2e8] dark:bg-slate-900 dark:hover:bg-slate-800 text-[#6a5d4d] dark:text-slate-200 font-bold py-4 px-8 rounded-2xl transition-all shadow-sm border border-[#efe6d8] dark:border-slate-800 disabled:opacity-50 flex items-center justify-center space-x-2">
                                    <svg v-if="generating" class="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                            stroke-width="4"></circle>
                                        <path class="opacity-75" fill="currentColor"
                                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                                        </path>
                                    </svg>
                                    <svg v-else class="w-5 h-5 text-[#b3a799] dark:text-slate-300" fill="none"
                                        stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                                    </svg>
                                    <span>{{ generating ? 'AI is Writing...' : 'AI: Draft Story' }}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="lg:col-span-4 space-y-6">
                <div class="glass-card rounded-[2rem] p-6">
                    <div class="flex items-start space-x-4 mb-4">
                        <div
                            class="w-12 h-12 rounded-xl bg-[#0b1021] dark:bg-white flex items-center justify-center flex-shrink-0">
                            <svg class="w-6 h-6 text-[#f7f2e8] dark:text-slate-900" fill="none" stroke="currentColor"
                                viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                            </svg>
                        </div>
                        <div>
                            <h3 class="font-bold text-lg mb-1 text-[#15131a] dark:text-white">Quick Generate</h3>
                            <p class="text-[#6a5d4d] dark:text-slate-400 text-sm leading-relaxed">Need a starting point?
                                Use
                                “AI: Draft Story”, then edit it in your voice.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <section v-if="stories.length > 0" class="mt-12">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                <div>
                    <h2 class="text-3xl font-bold text-[#15131a] dark:text-white mb-2">Your Gallery</h2>
                    <p class="text-[#6a5d4d] dark:text-slate-400">View and manage your generated videos</p>
                </div>
                <div class="flex items-center gap-3">
                    <div
                        class="bg-white/80 dark:bg-slate-900/70 border border-[#e6dccf] dark:border-slate-800 rounded-xl px-5 py-2.5 text-sm font-medium text-[#6a5d4d] dark:text-slate-300 shadow-sm">
                        {{ stories.length }} Total Stories
                    </div>
                    <div class="relative">
                        <select v-model="sortBy"
                            class="appearance-none bg-white/80 dark:bg-slate-900/70 border border-[#efe6d8] dark:border-slate-800 rounded-xl px-4 py-2.5 text-sm font-medium text-[#6a5d4d] dark:text-slate-300 shadow-sm cursor-pointer hover:border-[#c7a36c] focus:outline-none focus:ring-2 focus:ring-[#c7a36c]/40 transition-all pr-10">
                            <option value="latest">Latest First</option>
                            <option value="oldest">Oldest First</option>
                            <option value="schedule">Scheduled Date</option>
                        </select>
                        <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                            <svg class="w-4 h-4 text-[#b3a799] dark:text-slate-500" fill="none" stroke="currentColor"
                                viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M19 9l-7 7-7-7"></path>
                            </svg>
                        </div>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <StoryCard v-for="story in stories" :key="story.id" :story="story" @regenerate="regenerateVideo"
                    @delete="deleteStory" @upload="openPublishModal" @schedule="openScheduleModal"
                    @edit-scenes="openScenesModal" />
            </div>

            <div v-if="pagination && pagination.last_page > 1" class="mt-12 flex justify-center items-center space-x-2">
                <button v-for="link in pagination.links" :key="link.label"
                    @click="link.url ? fetchStories(parseInt(link.url.match(/page=(\d+)/)?.[1] || 1)) : null"
                    :disabled="!link.url || link.active"
                    class="px-5 py-2.5 rounded-full text-sm font-semibold transition-all duration-300 border shadow-sm flex items-center justify-center min-w-[44px]"
                    :class="[
                        link.active
                            ? 'bg-[#0b1021] text-[#f7f2e8] border-[#0b1021]'
                            : link.url
                                ? 'bg-white dark:bg-slate-900 border-[#efe6d8] dark:border-slate-800 text-[#6a5d4d] dark:text-slate-300 hover:border-[#c7a36c]'
                                : 'bg-[#f2ebe0] dark:bg-slate-900/60 border-[#efe6d8] dark:border-slate-800 text-[#b3a799] dark:text-slate-600 cursor-not-allowed'
                    ]" v-html="link.label">
                </button>
            </div>
        </section>

        <PublishModal :show="showPublishModal" :story="publishingStory" :channels="channels"
            @close="showPublishModal = false" @confirm="confirmPublish" />

        <ScheduleModal :show="showScheduleModal" :story="schedulingStory" :channels="channels"
            @close="showScheduleModal = false" @confirm="confirmSchedule" />

        <ScenesModal :show="showScenesModal" :story="editingScenesStory" @close="showScenesModal = false"
            @refresh="fetchStories" />
    </AppLayout>
</template>
