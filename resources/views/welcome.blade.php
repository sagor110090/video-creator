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
            <h2 class="text-xl font-semibold mb-4">Create New Story</h2>
            <div class="mb-4">
                <label class="block text-gray-700 text-sm font-bold mb-2">Title (Optional)</label>
                <input v-model="newStory.title" type="text" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="A Day at the Beach">
            </div>
            <div class="mb-4">
                <label class="block text-gray-700 text-sm font-bold mb-2">Your Story</label>
                <textarea v-model="newStory.content" rows="4" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter your story here... (at least 10 characters)"></textarea>
            </div>
            <div class="flex space-x-4">
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
                        <span :class="statusClass(story.status)" class="px-3 py-1 rounded-full text-xs font-semibold uppercase">
                            [[ story.status ]]
                        </span>
                    </div>

                    <p class="text-gray-700 mb-4 italic">"[[ truncate(story.content) ]]"</p>

                    <div v-if="story.status === 'completed' && story.video_path" class="mt-4">
                        <video controls class="w-full rounded-lg shadow-inner bg-black aspect-video">
                            <source :src="'/storage/' + story.video_path" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                        <div class="mt-4">
                            <a :href="'/storage/' + story.video_path" download class="inline-block bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded transition duration-200">
                                Download Video
                            </a>
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
                    content: ''
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
                            topic: newStory.value.title
                        });
                        newStory.value.title = response.data.title;
                        newStory.value.content = response.data.content;
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
                        newStory.value = { title: '', content: '' };
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

                onMounted(fetchStories);

                return {
                    stories,
                    newStory,
                    loading,
                    generating,
                    generateStory,
                    submitStory,
                    formatDate,
                    statusClass,
                    truncate
                };
            }
        }).mount('#app');
    </script>
</body>
</html>
