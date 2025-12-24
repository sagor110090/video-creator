<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Video Storyteller</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div id="app" class="container mx-auto px-4 py-8 max-w-4xl">
        <header class="text-center mb-12">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">AI Video Storyteller</h1>
            <p class="text-gray-600">Turn your stories into animated videos instantly</p>
        </header>

        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold">Create New Story</h2>
                <a href="{{ route('youtube.auth') }}" class="text-sm bg-red-600 hover:bg-red-700 text-white py-1 px-3 rounded flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                    Auth YouTube
                </a>
            </div>

            <div class="mb-4">
                <label class="block text-gray-700 text-sm font-bold mb-2">Content Style</label>
                <div class="flex space-x-4">
                    <label class="flex items-center cursor-pointer">
                        <input type="radio" v-model="newStory.style" value="story" class="mr-2">
                        <span class="text-gray-700" :class="{'font-bold text-blue-600': newStory.style === 'story'}">General Story</span>
                    </label>
                    <label class="flex items-center cursor-pointer">
                        <input type="radio" v-model="newStory.style" value="science_short" class="mr-2">
                        <span class="text-gray-700" :class="{'font-bold text-purple-600': newStory.style === 'science_short'}">The 60s Lab (Science)</span>
                    </label>
                </div>
            </div>

            <div class="mb-4">
                <label class="block text-gray-700 text-sm font-bold mb-2">Video Format</label>
                <div class="flex space-x-4">
                    <label class="flex items-center cursor-pointer">
                        <input type="radio" v-model="newStory.aspect_ratio" value="16:9" class="mr-2">
                        <span class="text-gray-700" :class="{'font-bold text-blue-600': newStory.aspect_ratio === '16:9'}">Landscape (16:9)</span>
                    </label>
                    <label class="flex items-center cursor-pointer">
                        <input type="radio" v-model="newStory.aspect_ratio" value="9:16" class="mr-2">
                        <span class="text-gray-700" :class="{'font-bold text-blue-600': newStory.aspect_ratio === '9:16'}">Shorts (9:16)</span>
                    </label>
                </div>
            </div>

            <div class="mb-4">
                <label class="block text-gray-700 text-sm font-bold mb-2">Title (Optional)</label>
                <input v-model="newStory.title" type="text" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="A Day at the Beach">
            </div>

            <div class="mb-4">
                <label class="block text-gray-700 text-sm font-bold mb-2">Your Story</label>
                <textarea v-model="newStory.content" rows="4" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter your story here... (at least 10 characters)"></textarea>
            </div>

            <div class="border-t pt-4 mt-4">
                <h3 class="text-md font-bold text-gray-700 mb-3 flex items-center">
                    <svg class="w-5 h-5 mr-2 text-red-600" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                    YouTube Upload Settings
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="mb-2">
                        <label class="block text-gray-600 text-xs font-bold mb-1">YouTube Title</label>
                        <input v-model="newStory.youtube_title" type="text" class="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Leave empty to use Story Title">
                    </div>
                    <div class="mb-2">
                        <label class="block text-gray-600 text-xs font-bold mb-1">YouTube Tags (comma separated)</label>
                        <input v-model="newStory.youtube_tags" type="text" class="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="story, ai, animation">
                    </div>
                </div>
                <div class="mb-2">
                    <label class="block text-gray-600 text-xs font-bold mb-1">YouTube Description</label>
                    <textarea v-model="newStory.youtube_description" rows="2" class="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Leave empty to use Story Content"></textarea>
                </div>
            </div>

            <div class="flex space-x-4 mt-6">
                <button @click="submitStory" :disabled="loading || generating" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg transition duration-200 disabled:opacity-50">
                    <span v-if="loading">Processing...</span>
                    <span v-else>Generate Video</span>
                </button>
                <button @click="generateStory" :disabled="loading || generating" class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-6 rounded-lg transition duration-200 disabled:opacity-50 flex items-center">
                    <svg v-if="generating" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span v-if="generating">AI is Writing...</span>
                    <span v-else>AI: Generate Story</span>
                </button>
            </div>
        </div>

        <div v-if="stories.length > 0">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">Your Stories</h2>
            <div class="grid gap-6">
                <div v-for="story in stories" :key="story.id" class="bg-white rounded-lg shadow-md p-6">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <h3 class="text-xl font-bold text-gray-800">[[ story.title ]]</h3>
                            <p class="text-sm text-gray-500">Created [[ formatDate(story.created_at) ]]</p>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span :class="statusClass(story.status)" class="px-3 py-1 rounded-full text-xs font-semibold uppercase">
                                [[ story.status ]]
                            </span>
                            <button v-if="story.status === 'failed' || story.status === 'completed'" @click="regenerateVideo(story)" class="text-blue-500 hover:text-blue-700 p-1 transition" title="Regenerate Video">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                            </button>
                            <button @click="deleteStory(story)" class="text-red-500 hover:text-red-700 p-1 transition" title="Delete Story">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                            </button>
                        </div>
                    </div>

                    <p class="text-gray-700 mb-4 italic">"[[ truncate(story.content) ]]"</p>

                    <div v-if="story.status === 'completed' && story.video_path" class="mt-4">
                        <video controls :class="story.aspect_ratio === '9:16' ? 'max-w-xs mx-auto aspect-[9/16]' : 'w-full aspect-video'" class="rounded-lg shadow-inner bg-black">
                            <source :src="'/storage/' + story.video_path" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>

                        <div class="mt-4 flex flex-wrap gap-2 items-center">
                            <a :href="'/storage/' + story.video_path" download class="inline-block bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded transition duration-200">
                                Download Video
                            </a>

                            <!-- YouTube Upload Section -->
                            <div v-if="story.status === 'completed'" class="flex flex-wrap gap-2 items-center">
                                <button v-if="!story.youtube_upload_status || story.youtube_upload_status === 'failed'"
                                        @click="uploadToYouTube(story)"
                                        class="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded transition duration-200 flex items-center">
                                    <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                                    Upload to YouTube
                                </button>

                                <span v-if="story.youtube_upload_status === 'completed'" class="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium flex items-center">
                                    <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                                    Uploaded
                                    <a :href="'https://youtube.com/watch?v=' + story.youtube_video_id" target="_blank" class="ml-2 underline">View</a>
                                </span>
                                <span v-else-if="story.youtube_upload_status === 'uploading'" class="bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full text-sm font-medium flex items-center">
                                    <svg class="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                    Uploading...
                                </span>
                            </div>
                        </div>

                        <!-- Metadata Editor for Completed Stories -->
                        <div v-if="story.status === 'completed'" class="mt-4 p-4 bg-gray-50 rounded-lg border">
                            <h4 class="text-sm font-bold text-gray-700 mb-2 flex items-center">
                                <svg class="w-4 h-4 mr-1 text-red-600" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                                YouTube Settings
                            </h4>
                            <div class="space-y-3">
                                <div>
                                    <label class="block text-xs font-bold text-gray-500 uppercase">Title</label>
                                    <input v-model="story.youtube_title" type="text" class="w-full px-2 py-1 text-sm border rounded focus:ring-1 focus:ring-blue-500 outline-none">
                                </div>
                                <div>
                                    <label class="block text-xs font-bold text-gray-500 uppercase">Tags</label>
                                    <input v-model="story.youtube_tags" type="text" class="w-full px-2 py-1 text-sm border rounded focus:ring-1 focus:ring-blue-500 outline-none">
                                </div>
                                <div>
                                    <label class="block text-xs font-bold text-gray-500 uppercase">Description</label>
                                    <textarea v-model="story.youtube_description" rows="2" class="w-full px-2 py-1 text-sm border rounded focus:ring-1 focus:ring-blue-500 outline-none"></textarea>
                                </div>
                                <div class="flex justify-between items-center">
                                    <button @click="updateMetadata(story)" class="text-xs bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded font-semibold transition">
                                        Save YouTube Info
                                    </button>
                                    <button @click="regenerateMetadata(story)" :disabled="story.regenerating" class="text-xs text-purple-600 hover:text-purple-800 font-semibold flex items-center">
                                        <svg v-if="story.regenerating" class="animate-spin -ml-1 mr-1 h-3 w-3 text-purple-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        AI: Regenerate Info
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div v-if="story.status === 'processing' || story.status === 'pending'" class="mt-4">
                        <div class="flex items-center space-x-2 text-blue-600 mb-2">
                            <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span class="font-medium">AI Workflow in Progress...</span>
                        </div>
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                            <div class="p-2 border rounded" :class="story.scenes_count > 0 ? 'bg-green-50 border-green-200 text-green-700' : 'bg-gray-50 border-gray-200 text-gray-500'">
                                1. Story Parser
                            </div>
                            <div class="p-2 border rounded bg-gray-50 border-gray-200 text-gray-500">
                                2. Voice Gen
                            </div>
                            <div class="p-2 border rounded bg-gray-50 border-gray-200 text-gray-500">
                                3. Video Gen
                            </div>
                            <div class="p-2 border rounded bg-gray-50 border-gray-200 text-gray-500">
                                4. Assembly
                            </div>
                        </div>
                    </div>

                    <div v-if="story.status === 'failed'" class="mt-4 p-4 bg-red-50 text-red-700 rounded-lg">
                        Failed to generate video. Please try again.
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const { createApp, ref, onMounted } = Vue;

        createApp({
            delimiters: ['[[', ']]'],
            setup() {
                const stories = ref([]);
                const loading = ref(false);
                const generating = ref(false);
                const newStory = ref({
                    title: '',
                    content: '',
                    aspect_ratio: '9:16',
                    style: 'science_short',
                    youtube_title: '',
                    youtube_description: '',
                    youtube_tags: ''
                });

                const fetchStories = async () => {
                    try {
                        const response = await axios.get('/api/stories');
                        stories.value = response.data;
                    } catch (error) {
                        console.error('Error fetching stories:', error);
                    }
                };

                const generateStory = async () => {
                    generating.value = true;
                    try {
                        const response = await axios.post('/api/stories/generate', {
                            topic: newStory.value.title,
                            style: newStory.value.style
                        });
                        newStory.value.title = response.data.title;
                        newStory.value.content = response.data.content;
                        newStory.value.youtube_title = response.data.youtube_title;
                        newStory.value.youtube_description = response.data.youtube_description;
                        newStory.value.youtube_tags = response.data.youtube_tags;
                    } catch (error) {
                        console.error('Error generating story:', error);
                        alert('Failed to generate story with AI');
                    } finally {
                        generating.value = false;
                    }
                };

                const submitStory = async () => {
                    if (newStory.value.content.length < 10) {
                        alert('Story content must be at least 10 characters');
                        return;
                    }

                    loading.value = true;
                    try {
                        await axios.post('/api/stories', newStory.value);
                        newStory.value = {
                            title: '',
                            content: '',
                            aspect_ratio: '9:16',
                            style: 'science_short',
                            youtube_title: '',
                            youtube_description: '',
                            youtube_tags: ''
                        };
                        fetchStories();
                        // Poll for updates every 5 seconds
                        const poll = setInterval(async () => {
                            await fetchStories();
                            const processing = stories.value.some(s => s.status === 'processing' || s.status === 'pending');
                            if (!processing) clearInterval(poll);
                        }, 5000);
                    } catch (error) {
                        console.error('Error submitting story:', error);
                        alert('Failed to submit story');
                    } finally {
                        loading.value = false;
                    }
                };

                const updateMetadata = async (story) => {
                    try {
                        await axios.patch(`/api/stories/${story.id}`, {
                            youtube_title: story.youtube_title,
                            youtube_description: story.youtube_description,
                            youtube_tags: story.youtube_tags
                        });
                        alert('YouTube settings saved!');
                    } catch (error) {
                        console.error('Error updating metadata:', error);
                        alert('Failed to save settings');
                    }
                };

                const uploadToYouTube = async (story) => {
                    try {
                        const response = await axios.post(`/api/stories/${story.id}/upload`);
                        story.youtube_upload_status = 'uploading';
                        alert(response.data.message);
                        // Start polling to check upload status
                        const poll = setInterval(async () => {
                            const res = await axios.get(`/api/stories/${story.id}`);
                            story.youtube_upload_status = res.data.youtube_upload_status;
                            story.youtube_video_id = res.data.youtube_video_id;
                            if (story.youtube_upload_status === 'completed' || story.youtube_upload_status === 'failed') {
                                clearInterval(poll);
                            }
                        }, 10000);
                    } catch (error) {
                        console.error('Error uploading to YouTube:', error);
                        alert(error.response?.data?.error || 'Failed to trigger upload');
                    }
                };

                const regenerateMetadata = async (story) => {
                    story.regenerating = true;
                    try {
                        const response = await axios.post(`/api/stories/${story.id}/generate-metadata`);
                        story.youtube_title = response.data.youtube_title;
                        story.youtube_description = response.data.youtube_description;
                        story.youtube_tags = response.data.youtube_tags;
                    } catch (error) {
                        console.error('Error regenerating metadata:', error);
                        alert('Failed to regenerate metadata');
                    } finally {
                        story.regenerating = false;
                    }
                };

                const formatDate = (dateString) => {
                    return new Date(dateString).toLocaleString();
                };

                const statusClass = (status) => {
                    switch (status) {
                        case 'completed': return 'bg-green-100 text-green-800';
                        case 'processing': return 'bg-blue-100 text-blue-800';
                        case 'pending': return 'bg-yellow-100 text-yellow-800';
                        case 'failed': return 'bg-red-100 text-red-800';
                        default: return 'bg-gray-100 text-gray-800';
                    }
                };

                const truncate = (text) => {
                    return text.length > 150 ? text.substring(0, 150) + '...' : text;
                };

                const deleteStory = async (story) => {
                    if (!confirm('Are you sure you want to delete this story?')) return;
                    try {
                        await axios.delete(`/api/stories/${story.id}`);
                        stories.value = stories.value.filter(s => s.id !== story.id);
                    } catch (error) {
                        console.error('Error deleting story:', error);
                        alert('Failed to delete story');
                    }
                };

                const regenerateVideo = async (story) => {
                    if (!confirm('Are you sure you want to regenerate the video? This will restart the processing flow.')) return;
                    try {
                        await axios.post(`/api/stories/${story.id}/regenerate`);
                        story.status = 'pending';
                        // Start polling if not already
                        fetchStories();
                    } catch (error) {
                        console.error('Error regenerating video:', error);
                        alert('Failed to trigger regeneration');
                    }
                };

                onMounted(fetchStories);

                return {
                    stories,
                    newStory,
                    loading,
                    generating,
                    generateStory,
                    submitStory,
                    updateMetadata,
                    regenerateMetadata,
                    uploadToYouTube,
                      deleteStory,
                      regenerateVideo,
                      formatDate,
                    statusClass,
                    truncate
                };
            }
        }).mount('#app');
    </script>
</body>
</html>
