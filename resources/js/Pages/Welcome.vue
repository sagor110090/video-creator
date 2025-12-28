<script setup>
import { ref, onMounted, watch } from 'vue';
import { Head, Link } from '@inertiajs/vue3';
import { useForm } from '@inertiajs/vue3';
import axios from 'axios';
import StoryCard from '@/Components/StoryCard.vue';
import PublishModal from '@/Components/PublishModal.vue';
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
const publishingStory = ref(null);
const channels = ref([]);
const facebookPages = ref([]);
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

const newStory = ref({
    title: '',
    content: '',
    style: 'story',
    aspect_ratio: '16:9',
    youtube_title: '',
    youtube_description: '',
    youtube_tags: '',
    youtube_token_id: null,
    search_query: ''
});

const fetchStories = async (page = 1) => {
    try {
        const response = await axios.get(`/api/stories?page=${page}`);
        stories.value = response.data.data;
        pagination.value = response.data;
    } catch (error) {
        console.error('Error fetching stories:', error);
    }
};

const fetchChannels = async () => {
    try {
        const response = await axios.get('/api/youtube/channels');
        channels.value = response.data;
    } catch (error) {
        console.error('Error fetching channels:', error);
    }
};

const fetchFacebookPages = async () => {
    try {
        const response = await axios.get('/api/facebook/pages');
        facebookPages.value = response.data;
    } catch (error) {
        console.error('Error fetching Facebook pages:', error);
    }
};

onMounted(() => {
    // Check for saved theme or system preference
    const savedTheme = localStorage.getItem('theme');
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && systemDark)) {
        isDark.value = true;
        document.documentElement.classList.add('dark');
    }

    fetchStories();
    fetchChannels();
    fetchFacebookPages();
    setInterval(() => fetchStories(pagination.value?.current_page || 1), 5000);
});

watch(() => newStory.value.style, (newStyle) => {
    if (channels.value.length === 0) return;
    let targetTitle = '';
    if (newStyle === 'science_short') targetTitle = 'The 60s Lab';
    else if (newStyle === 'hollywood_hype') targetTitle = 'Hollywood Hype';
    else if (newStyle === 'trade_wave') targetTitle = 'TradeWave';

    if (targetTitle) {
        const channel = channels.value.find(c => c.channel_title.includes(targetTitle));
        if (channel) newStory.value.youtube_token_id = channel.id;
    }
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
        newStory.value = {
            title: '',
            content: '',
            style: 'story',
            aspect_ratio: '16:9',
            youtube_title: '',
            youtube_description: '',
            youtube_tags: '',
            youtube_token_id: null,
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
            style: newStory.value.style
        });

        // If the AI returned a title but the user didn't provide one, fill it in
        if (!newStory.value.title && response.data.title) {
            newStory.value.title = response.data.title;
        }

        newStory.value.content = response.data.content;

        // Auto-populate YouTube automation fields
        newStory.value.youtube_title = response.data.youtube_title || response.data.title;
        newStory.value.youtube_description = response.data.youtube_description || response.data.content;
        newStory.value.youtube_tags = response.data.youtube_tags || 'ai, story, animation';

        // Open the YouTube settings accordion so user can see the generated metadata
        showYoutubeSettings.value = true;
    } catch (error) {
        console.error('Error generating story:', error);
    } finally {
        generating.value = false;
    }
};

const searchNews = async () => {
    if (!newStory.value.search_query) return;
    searching_news.value = true;
    try {
        const response = await axios.post('/api/ai/search-news', {
            query: newStory.value.search_query,
            style: newStory.value.style
        });
        news_results.value = response.data;
    } catch (error) {
        console.error('Error searching news:', error);
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
        confirmButtonColor: '#4f46e5',
        cancelButtonColor: '#64748b',
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
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
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

const uploadToFacebook = async (story) => {
    if (facebookPages.value.length === 0) {
        toast.error('Please connect a Facebook page first.');
        return;
    }

    const { value: facebookPageId } = await Swal.fire({
        title: 'Select Facebook Page',
        input: 'select',
        inputOptions: facebookPages.value.reduce((acc, page) => {
            acc[page.id] = page.name;
            return acc;
        }, {}),
        inputPlaceholder: 'Choose a page...',
        showCancelButton: true,
        confirmButtonColor: '#4f46e5',
        cancelButtonColor: '#64748b',
        background: isDark.value ? '#0f172a' : '#ffffff',
        color: isDark.value ? '#f8fafc' : '#0f172a'
    });

    if (!facebookPageId) return;

    try {
        await axios.post(`/api/stories/${story.id}/upload-facebook`, {
            facebook_page_id: facebookPageId
        });
        toast.success('Facebook upload queued successfully!');
        fetchStories();
    } catch (error) {
        console.error('Error uploading to Facebook:', error);
        toast.error(error.response?.data?.error || 'Failed to upload to Facebook.');
    }
};

const confirmPublish = async (formData) => {
    try {
        showPublishModal.value = false;
        // First update metadata
        await axios.patch(`/api/stories/${publishingStory.value.id}`, formData);
        // Then trigger upload
        await axios.post(`/api/stories/${publishingStory.value.id}/upload`);
        toast.success('Upload queued successfully!');
        fetchStories();
    } catch (error) {
        console.error('Error publishing story:', error);
        toast.error('Failed to start upload. Please try again.');
    }
};

const handleLogout = () => {
    useForm({}).post('/logout');
};
</script>

<template>
    <Head title="AI Video Storyteller" />

    <div class="min-h-screen bg-[#f8fafc] dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-300">
        <!-- Navigation -->
        <nav class="sticky top-0 z-50 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
            <div class="container mx-auto px-4 max-w-6xl">
                <div class="flex items-center justify-between h-16">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-200/50 dark:shadow-indigo-900/20">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
                        </div>
                        <span class="text-lg font-bold tracking-tight text-slate-800 dark:text-white">Video<span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600">AI</span></span>
                    </div>

                    <div class="flex items-center gap-3">
                        <div v-if="channels.length > 0 || facebookPages.length > 0" class="hidden lg:flex items-center -space-x-2.5 pr-3 border-r border-slate-200 dark:border-slate-700">
                            <div class="flex items-center -space-x-2.5">
                                <img v-for="channel in channels.slice(0, 2)" :key="'yt-'+channel.id" :src="channel.channel_thumbnail" :title="channel.channel_title" class="w-8 h-8 rounded-full border-2 border-white dark:border-slate-800 ring-2 ring-slate-100 dark:ring-slate-700 cursor-pointer transition-all hover:scale-110 hover:z-10 hover:ring-indigo-400">
                                <template v-for="page in facebookPages.slice(0, 2)" :key="'fb-'+page.id">
                                    <img v-if="page.picture_url" :src="page.picture_url" :title="page.name" class="w-8 h-8 rounded-full border-2 border-white dark:border-slate-800 ring-2 ring-slate-100 dark:ring-slate-700 cursor-pointer transition-all hover:scale-110 hover:z-10 hover:ring-blue-400">
                                    <div v-else :title="page.name" class="w-8 h-8 rounded-full border-2 border-white dark:border-slate-800 ring-2 ring-slate-100 dark:ring-slate-700 flex items-center justify-center bg-gradient-to-br from-blue-500 to-blue-600 text-white text-xs font-bold cursor-pointer transition-all hover:scale-110 hover:z-10 hover:ring-blue-400">
                                        {{ page.name.charAt(0) }}
                                    </div>
                                </template>
                                <div v-if="(channels.length + facebookPages.length) > 4" class="w-8 h-8 rounded-full border-2 border-white dark:border-slate-800 ring-2 ring-slate-100 dark:ring-slate-700 flex items-center justify-center bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-bold">
                                    +{{ channels.length + facebookPages.length - 4 }}
                                </div>
                            </div>
                        </div>

                        <div class="flex items-center gap-1.5">
                            <button @click="toggleDarkMode" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-all group relative">
                                <svg v-if="isDark" class="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M16.243 17.243l.707.707M7.757 7.757l.707-.707M12 7a5 5 0 100 10 5 5 0 000-10z"></path></svg>
                                <svg v-else class="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path></svg>
                            </button>
                            
                            <a href="/statistics" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-all group relative" title="Statistics">
                                <svg class="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                            </a>
                            
                            <a href="/schedules" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-all group relative" title="Schedules">
                                <svg class="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            </a>
                            
                            <button v-if="props.auth?.user" @click="handleLogout" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-all group relative" title="Logout">
                                <svg class="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                            </button>

                            <a href="/youtube/auth" class="group flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-900 dark:bg-slate-100 hover:bg-slate-800 dark:hover:bg-white text-white dark:text-slate-900 transition-all duration-200 hover:shadow-lg hover:shadow-slate-200 dark:hover:shadow-none" title="Connect YouTube">
                                <svg class="w-4 h-4 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                                <span class="hidden sm:inline text-xs font-semibold">YouTube</span>
                            </a>

                            <a href="/oauth/facebook/auth" class="group flex items-center gap-2 px-3 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white transition-all duration-200 hover:shadow-lg hover:shadow-blue-200 dark:hover:shadow-none" title="Connect Facebook">
                                <svg class="w-4 h-4 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
                                <span class="hidden sm:inline text-xs font-semibold">Facebook</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </nav>

        <main class="container mx-auto px-4 max-w-6xl pb-20">
            <!-- Hero -->
            <section class="text-center mb-12">
                <h1 class="text-4xl md:text-5xl font-extrabold text-slate-900 dark:text-white mb-4 tracking-tight">
                    Turn your ideas into <span class="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">stunning videos</span>
                </h1>
                <p class="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
                    The fastest way to create animated stories, science explainers, and entertainment news using advanced AI.
                </p>
            </section>

            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <!-- Creator Form -->
                <div class="lg:col-span-8 space-y-8">
                    <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
                        <div class="p-6 md:p-8">
                            <div class="flex items-center justify-between mb-8">
                                <h2 class="text-2xl font-bold text-slate-800 dark:text-white">Create New Story</h2>
                                <span class="text-xs font-semibold px-3 py-1 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-full">AI-Powered</span>
                            </div>

                            <!-- Content Style Grid -->
                            <div class="mb-8">
                                <label class="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-4">Choose your style</label>
                                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div v-for="style in [
                                        { id: 'story', name: 'General Story', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5S19.832 5.477 21 6.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253', color: 'blue' },
                                        { id: 'science_short', name: '60s Lab', icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.691.34a2 2 0 01-1.782 0l-.691-.34a6 6 0 00-3.86-.517l-2.387.477a2 2 0 00-1.022.547V18a2 2 0 002 2h12a2 2 0 002-2v-2.572zM12 11V3.5', color: 'purple' },
                                        { id: 'hollywood_hype', name: 'Hollywood', icon: 'M7 4V20M17 4V20M3 8H7M17 8H21M3 12H21M3 16H7M17 16H21M4 20H20C21.1046 20 22 19.1046 22 18V6C22 4.89543 21.1046 4 20 4H4C2.89543 4 2 4.89543 2 6V18C2 19.1046 2.89543 20 4 20Z', color: 'red' },
                                        { id: 'trade_wave', name: 'TradeWave', icon: 'M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z', color: 'green' }
                                    ]" :key="style.id"
                                    @click="newStory.style = style.id"
                                    :class="['cursor-pointer p-4 rounded-xl border-2 transition-all flex flex-col items-center text-center space-y-3',
                                             newStory.style === style.id ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/20 shadow-sm' : 'border-slate-100 dark:border-slate-800 hover:border-slate-200 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50']">
                                        <div :class="['w-10 h-10 rounded-lg flex items-center justify-center',
                                                     newStory.style === style.id ? 'bg-indigo-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400']">
                                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="style.icon"></path></svg>
                                        </div>
                                        <span class="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">{{ style.name }}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- News Search Context -->
                            <div v-if="newStory.style === 'hollywood_hype' || newStory.style === 'trade_wave'"
                                 class="mb-8 p-6 rounded-2xl animate-in fade-in slide-in-from-top-4 duration-300"
                                 :class="newStory.style === 'hollywood_hype' ? 'bg-red-50/50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30' : 'bg-emerald-50/50 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-900/30'">
                                <div class="flex items-center space-x-2 mb-4">
                                    <div :class="['w-8 h-8 rounded-lg flex items-center justify-center', newStory.style === 'hollywood_hype' ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400' : 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400']">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path></svg>
                                    </div>
                                    <h3 class="font-bold" :class="newStory.style === 'hollywood_hype' ? 'text-red-900 dark:text-red-200' : 'text-emerald-900 dark:text-emerald-200'">
                                        {{ newStory.style === 'hollywood_hype' ? 'Hollywood News' : 'Market Updates' }}
                                    </h3>
                                </div>
                                <div class="flex space-x-2 mb-4">
                                    <input v-model="newStory.search_query" type="text"
                                           class="flex-1 px-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 transition-all shadow-sm dark:text-white"
                                           :class="newStory.style === 'hollywood_hype' ? 'focus:ring-red-500' : 'focus:ring-emerald-500'"
                                           :placeholder="newStory.style === 'hollywood_hype' ? 'e.g. Dakota Johnson latest news...' : 'e.g. Bitcoin price action today...'">
                                    <button @click="searchNews" :disabled="searching_news"
                                            class="px-6 py-3 rounded-xl font-bold text-white transition-all shadow-md disabled:opacity-50"
                                            :class="newStory.style === 'hollywood_hype' ? 'bg-red-600 hover:bg-red-700' : 'bg-emerald-600 hover:bg-emerald-700'">
                                        <div class="flex items-center space-x-2">
                                            <svg v-if="searching_news" class="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                            <span>Search</span>
                                        </div>
                                    </button>
                                </div>
                                <div v-if="news_results.length > 0" class="space-y-3 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
                                    <div v-for="(news, index) in news_results" :key="index" @click="selectNews(news)"
                                         class="p-4 bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-xl cursor-pointer hover:shadow-md transition-all group">
                                        <p class="font-bold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 mb-1">{{ news.title }}</p>
                                        <p class="text-sm text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">{{ news.snippet }}</p>
                                    </div>
                                </div>
                            </div>

                            <!-- Form Fields -->
                            <div class="space-y-6">
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <label class="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-2">Video Format</label>
                                        <div class="flex p-1 bg-slate-100 dark:bg-slate-800 rounded-xl">
                                            <button v-for="ratio in ['16:9', '9:16']" :key="ratio"
                                                    @click="newStory.aspect_ratio = ratio"
                                                    :class="['flex-1 py-2 text-sm font-bold rounded-lg transition-all',
                                                             newStory.aspect_ratio === ratio ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200']">
                                                {{ ratio === '16:9' ? 'Landscape' : 'Shorts' }}
                                            </button>
                                        </div>
                                    </div>
                                    <div>
                                        <label class="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-2">Story Title</label>
                                        <input v-model="newStory.title" type="text"
                                               class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all dark:text-white"
                                               placeholder="A magical journey through...">
                                    </div>
                                </div>

                                <div>
                                    <label class="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-2">The Story</label>
                                    <textarea v-model="newStory.content" rows="5"
                                              class="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all dark:text-white"
                                              placeholder="Tell your story in detail... (minimum 10 characters)"></textarea>
                                </div>

                                <!-- YouTube Settings Accordion -->
                                <div class="border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden bg-slate-50/50 dark:bg-slate-900/50">
                                    <button @click="showYoutubeSettings = !showYoutubeSettings"
                                            class="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                                        <div class="flex items-center space-x-3 text-slate-700 dark:text-slate-200 font-bold">
                                            <svg class="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                                            <span>YouTube Automations</span>
                                        </div>
                                        <svg :class="{'rotate-180': showYoutubeSettings}" class="w-5 h-5 text-slate-400 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                                    </button>

                                    <div v-show="showYoutubeSettings" class="px-6 pb-6 space-y-4">
                                        <div v-if="channels.length > 0">
                                            <label class="block text-slate-500 dark:text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-2">Target Channel</label>
                                            <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                                                <div v-for="channel in channels" :key="channel.id"
                                                     @click="newStory.youtube_token_id = channel.id"
                                                     :class="['flex items-center p-3 border rounded-xl cursor-pointer transition-all',
                                                              newStory.youtube_token_id === channel.id ? 'border-red-500 bg-red-50 dark:bg-red-900/20 ring-2 ring-red-100 dark:ring-red-900/40' : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-red-300 dark:hover:border-red-900/60']">
                                                    <img :src="channel.channel_thumbnail" class="w-8 h-8 rounded-full shadow-sm mr-3">
                                                    <span class="text-xs font-bold truncate text-slate-700 dark:text-slate-200">{{ channel.channel_title }}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <label class="block text-slate-500 dark:text-slate-400 text-[10px] font-bold uppercase mb-1">YouTube Title</label>
                                                <input v-model="newStory.youtube_title" type="text" class="w-full px-3 py-2 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-red-500 outline-none dark:text-white" placeholder="Default: Story Title">
                                            </div>
                                            <div>
                                                <label class="block text-slate-500 dark:text-slate-400 text-[10px] font-bold uppercase mb-1">Tags</label>
                                                <input v-model="newStory.youtube_tags" type="text" class="w-full px-3 py-2 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-red-500 outline-none dark:text-white" placeholder="story, ai, animation">
                                            </div>
                                        </div>
                                        <div>
                                            <label class="block text-slate-500 dark:text-slate-400 text-[10px] font-bold uppercase mb-1">Description</label>
                                            <textarea v-model="newStory.youtube_description" rows="2" class="w-full px-3 py-2 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-red-500 outline-none dark:text-white" placeholder="Default: Story Content"></textarea>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Actions -->
                            <div class="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4 mt-10">
                                <button @click="submitStory" :disabled="loading || generating"
                                        class="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-4 px-8 rounded-2xl transition-all shadow-lg shadow-indigo-200 dark:shadow-none disabled:opacity-50 flex items-center justify-center space-x-2">
                                    <svg v-if="loading" class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                    <span>{{ loading ? 'Processing...' : 'Generate Video' }}</span>
                                </button>
                                <button @click="generateStory" :disabled="loading || generating"
                                        class="flex-1 bg-slate-900 dark:bg-slate-700 hover:bg-slate-800 dark:hover:bg-slate-600 text-white font-bold py-4 px-8 rounded-2xl transition-all shadow-lg shadow-slate-200 dark:shadow-none disabled:opacity-50 flex items-center justify-center space-x-2">
                                    <svg v-if="generating" class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                    <svg v-else class="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                    <span>{{ generating ? 'AI is Writing...' : 'AI: Draft Story' }}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Sidebar / Recent Activity -->
                <div class="lg:col-span-4 space-y-6">
                    <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6">
                        <h3 class="font-bold text-slate-800 dark:text-white mb-4 flex items-center">
                            <svg class="w-5 h-5 mr-2 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            Tips for Success
                        </h3>
                        <ul class="space-y-4">
                            <li class="flex items-start space-x-3 text-sm">
                                <div class="w-5 h-5 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0 font-bold">1</div>
                                <p class="text-slate-600 dark:text-slate-400">Be descriptive in your story content for better AI visualization.</p>
                            </li>
                            <li class="flex items-start space-x-3 text-sm">
                                <div class="w-5 h-5 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0 font-bold">2</div>
                                <p class="text-slate-600 dark:text-slate-400">Use "Shorts" format for TikTok, Reels, and YouTube Shorts.</p>
                            </li>
                            <li class="flex items-start space-x-3 text-sm">
                                <div class="w-5 h-5 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0 font-bold">3</div>
                                <p class="text-slate-600 dark:text-slate-400">Connect your YouTube channel to automate uploads.</p>
                            </li>
                        </ul>
                    </div>

                    <div v-if="channels.length === 0" class="bg-indigo-600 rounded-2xl shadow-lg p-6 text-white">
                        <h3 class="font-bold mb-2">Grow your channel</h3>
                        <p class="text-indigo-100 text-sm mb-4 leading-relaxed">Connect your YouTube account to automatically upload your generated videos with AI-optimized metadata.</p>
                        <a href="/youtube/auth" class="block w-full text-center bg-white text-indigo-600 font-bold py-3 rounded-xl hover:bg-indigo-50 transition-colors">
                            Connect YouTube
                        </a>
                    </div>
                </div>
            </div>

            <!-- Your Stories Grid -->
            <section v-if="stories.length > 0" class="mt-20">
                <div class="flex items-center justify-between mb-8">
                    <div>
                        <h2 class="text-3xl font-bold text-slate-900 dark:text-white">Your Gallery</h2>
                        <p class="text-slate-500 dark:text-slate-400">View and manage your generated videos</p>
                    </div>
                    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400">
                        {{ stories.length }} Total Stories
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                    <StoryCard v-for="story in stories" :key="story.id"
                               :story="story"
                               @regenerate="regenerateVideo"
                               @delete="deleteStory"
                               @upload="openPublishModal"
                               @upload-facebook="uploadToFacebook" />
                </div>

                <!-- Pagination -->
                <div v-if="pagination && pagination.last_page > 1" class="mt-12 flex justify-center items-center space-x-2">
                    <button v-for="link in pagination.links"
                            :key="link.label"
                            @click="link.url ? fetchStories(parseInt(link.url.match(/page=(\d+)/)?.[1] || 1)) : null"
                            :disabled="!link.url || link.active"
                            class="px-4 py-2 rounded-xl text-sm font-bold transition-all border shadow-sm flex items-center justify-center min-w-[40px]"
                            :class="[
                                link.active
                                    ? 'bg-indigo-600 border-indigo-600 text-white'
                                    : link.url
                                        ? 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-indigo-500 hover:text-indigo-600'
                                        : 'bg-slate-50 dark:bg-slate-800 border-slate-100 dark:border-slate-700 text-slate-300 dark:text-slate-600 cursor-not-allowed'
                            ]"
                            v-html="link.label">
                    </button>
                </div>
            </section>
        </main>

        <PublishModal :show="showPublishModal"
                      :story="publishingStory"
                      :channels="channels"
                      @close="showPublishModal = false"
                      @confirm="confirmPublish" />
    </div>
</template>

<style>
.custom-scrollbar::-webkit-scrollbar {
    width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}
.dark .custom-scrollbar::-webkit-scrollbar-track {
    background: #1e293b;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #e2e8f0;
    border-radius: 10px;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb {
    background: #334155;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #cbd5e1;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #475569;
}
</style>
