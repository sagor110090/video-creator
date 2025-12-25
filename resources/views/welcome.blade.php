<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Video Storyteller | Create Animated Stories Instantly</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        body { font-family: 'Inter', sans-serif; }
        .glass { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }
        .gradient-text { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .style-card-active { border-color: #4f46e5; background-color: #f5f3ff; }
        [v-cloak] { display: none; }
    </style>
</head>
<body class="bg-[#f8fafc] text-slate-900 min-h-screen">
    <div id="app" v-cloak>
        <!-- Navigation -->
        <nav class="sticky top-0 z-50 glass border-b border-slate-200 py-4 mb-8">
            <div class="container mx-auto px-4 max-w-6xl flex justify-between items-center">
                <div class="flex items-center space-x-2">
                    <div class="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-200">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
                    </div>
                    <span class="text-xl font-bold tracking-tight text-slate-800">Video<span class="text-indigo-600">AI</span></span>
                </div>
                <div class="flex items-center space-x-4">
                    <div v-if="channels.length > 0" class="hidden md:flex items-center -space-x-2 mr-4">
                        <img v-for="channel in channels" :key="channel.id" :src="channel.channel_thumbnail" :title="channel.channel_title" class="w-8 h-8 rounded-full border-2 border-white ring-1 ring-slate-100 cursor-help transition-transform hover:scale-110 hover:z-10">
                    </div>
                    <a href="{{ route('youtube.auth') }}" class="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                        <span>Add Channel</span>
                    </a>
                </div>
            </div>
        </nav>

        <main class="container mx-auto px-4 max-w-6xl pb-20">
            <!-- Hero -->
            <section class="text-center mb-12">
                <h1 class="text-4xl md:text-5xl font-extrabold text-slate-900 mb-4 tracking-tight">
                    Turn your ideas into <span class="gradient-text">stunning videos</span>
                </h1>
                <p class="text-lg text-slate-600 max-w-2xl mx-auto">
                    The fastest way to create animated stories, science explainers, and entertainment news using advanced AI.
                </p>
            </section>

            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <!-- Creator Form -->
                <div class="lg:col-span-8 space-y-8">
                    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                        <div class="p-6 md:p-8">
                            <div class="flex items-center justify-between mb-8">
                                <h2 class="text-2xl font-bold text-slate-800">Create New Story</h2>
                                <span class="text-xs font-semibold px-3 py-1 bg-indigo-50 text-indigo-600 rounded-full">AI-Powered</span>
                            </div>

                            <!-- Content Style Grid -->
                            <div class="mb-8">
                                <label class="block text-slate-700 text-sm font-semibold mb-4">Choose your style</label>
                                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div v-for="style in [
                                        { id: 'story', name: 'General Story', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5S19.832 5.477 21 6.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253', color: 'blue' },
                                        { id: 'science_short', name: '60s Lab', icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.691.34a2 2 0 01-1.782 0l-.691-.34a6 6 0 00-3.86-.517l-2.387.477a2 2 0 00-1.022.547V18a2 2 0 002 2h12a2 2 0 002-2v-2.572zM12 11V3.5', color: 'purple' },
                                        { id: 'hollywood_hype', name: 'Hollywood', icon: 'M7 4V20M17 4V20M3 8H7M17 8H21M3 12H21M3 16H7M17 16H21M4 20H20C21.1046 20 22 19.1046 22 18V6C22 4.89543 21.1046 4 20 4H4C2.89543 4 2 4.89543 2 6V18C2 19.1046 2.89543 20 4 20Z', color: 'red' },
                                        { id: 'trade_wave', name: 'TradeWave', icon: 'M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z', color: 'green' }
                                    ]" :key="style.id"
                                    @click="newStory.style = style.id"
                                    :class="['cursor-pointer p-4 rounded-xl border-2 transition-all flex flex-col items-center text-center space-y-3',
                                             newStory.style === style.id ? 'border-indigo-600 bg-indigo-50 shadow-sm' : 'border-slate-100 hover:border-slate-200 hover:bg-slate-50']">
                                        <div :class="['w-10 h-10 rounded-lg flex items-center justify-center',
                                                     newStory.style === style.id ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500']">
                                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="style.icon"></path></svg>
                                        </div>
                                        <span class="text-xs font-bold uppercase tracking-wider">[[ style.name ]]</span>
                                    </div>
                                </div>
                            </div>

                            <!-- News Search Context -->
                            <div v-if="newStory.style === 'hollywood_hype' || newStory.style === 'trade_wave'"
                                 class="mb-8 p-6 rounded-2xl animate-in fade-in slide-in-from-top-4 duration-300"
                                 :class="newStory.style === 'hollywood_hype' ? 'bg-red-50/50 border border-red-100' : 'bg-emerald-50/50 border border-emerald-100'">
                                <div class="flex items-center space-x-2 mb-4">
                                    <div :class="['w-8 h-8 rounded-lg flex items-center justify-center', newStory.style === 'hollywood_hype' ? 'bg-red-100 text-red-600' : 'bg-emerald-100 text-emerald-600']">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path></svg>
                                    </div>
                                    <h3 class="font-bold" :class="newStory.style === 'hollywood_hype' ? 'text-red-900' : 'text-emerald-900'">
                                        [[ newStory.style === 'hollywood_hype' ? 'Hollywood News' : 'Market Updates' ]]
                                    </h3>
                                </div>
                                <div class="flex space-x-2 mb-4">
                                    <input v-model="newStory.search_query" type="text"
                                           class="flex-1 px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 transition-all shadow-sm"
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
                                         class="p-4 bg-white border border-slate-100 rounded-xl cursor-pointer hover:shadow-md transition-all group">
                                        <p class="font-bold text-slate-800 group-hover:text-indigo-600 mb-1">[[ news.title ]]</p>
                                        <p class="text-sm text-slate-500 line-clamp-2 leading-relaxed">[[ news.snippet ]]</p>
                                    </div>
                                </div>
                            </div>

                            <!-- Form Fields -->
                            <div class="space-y-6">
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <label class="block text-slate-700 text-sm font-semibold mb-2">Video Format</label>
                                        <div class="flex p-1 bg-slate-100 rounded-xl">
                                            <button v-for="ratio in ['16:9', '9:16']" :key="ratio"
                                                    @click="newStory.aspect_ratio = ratio"
                                                    :class="['flex-1 py-2 text-sm font-bold rounded-lg transition-all',
                                                             newStory.aspect_ratio === ratio ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700']">
                                                [[ ratio === '16:9' ? 'Landscape' : 'Shorts' ]]
                                            </button>
                                        </div>
                                    </div>
                                    <div>
                                        <label class="block text-slate-700 text-sm font-semibold mb-2">Story Title</label>
                                        <input v-model="newStory.title" type="text"
                                               class="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                                               placeholder="A magical journey through...">
                                    </div>
                                </div>

                                <div>
                                    <label class="block text-slate-700 text-sm font-semibold mb-2">The Story</label>
                                    <textarea v-model="newStory.content" rows="5"
                                              class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                                              placeholder="Tell your story in detail... (minimum 10 characters)"></textarea>
                                </div>

                                <!-- YouTube Settings Accordion -->
                                <div class="border border-slate-200 rounded-2xl overflow-hidden bg-slate-50/50">
                                    <button @click="showYoutubeSettings = !showYoutubeSettings"
                                            class="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                                        <div class="flex items-center space-x-3 text-slate-700 font-bold">
                                            <svg class="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                                            <span>YouTube Automations</span>
                                        </div>
                                        <svg :class="{'rotate-180': showYoutubeSettings}" class="w-5 h-5 text-slate-400 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                                    </button>

                                    <div v-show="showYoutubeSettings" class="px-6 pb-6 space-y-4 animate-in slide-in-from-top-2">
                                        <div v-if="channels.length > 0">
                                            <label class="block text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-2">Target Channel</label>
                                            <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                                                <div v-for="channel in channels" :key="channel.id"
                                                     @click="newStory.youtube_token_id = channel.id"
                                                     :class="['flex items-center p-3 border rounded-xl cursor-pointer transition-all',
                                                              newStory.youtube_token_id === channel.id ? 'border-red-500 bg-red-50 ring-2 ring-red-100' : 'bg-white border-slate-200 hover:border-red-300']">
                                                    <img :src="channel.channel_thumbnail" class="w-8 h-8 rounded-full shadow-sm mr-3">
                                                    <span class="text-xs font-bold truncate">[[ channel.channel_title ]]</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <label class="block text-slate-500 text-[10px] font-bold uppercase mb-1">YouTube Title</label>
                                                <input v-model="newStory.youtube_title" type="text" class="w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-red-500 outline-none" placeholder="Default: Story Title">
                                            </div>
                                            <div>
                                                <label class="block text-slate-500 text-[10px] font-bold uppercase mb-1">Tags</label>
                                                <input v-model="newStory.youtube_tags" type="text" class="w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-red-500 outline-none" placeholder="story, ai, animation">
                                            </div>
                                        </div>
                                        <div>
                                            <label class="block text-slate-500 text-[10px] font-bold uppercase mb-1">Description</label>
                                            <textarea v-model="newStory.youtube_description" rows="2" class="w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-red-500 outline-none" placeholder="Default: Story Content"></textarea>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Actions -->
                            <div class="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4 mt-10">
                                <button @click="submitStory" :disabled="loading || generating"
                                        class="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-4 px-8 rounded-2xl transition-all shadow-lg shadow-indigo-200 disabled:opacity-50 flex items-center justify-center space-x-2">
                                    <svg v-if="loading" class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                    <span>[[ loading ? 'Processing...' : 'Generate Video' ]]</span>
                                </button>
                                <button @click="generateStory" :disabled="loading || generating"
                                        class="flex-1 bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 px-8 rounded-2xl transition-all shadow-lg shadow-slate-200 disabled:opacity-50 flex items-center justify-center space-x-2">
                                    <svg v-if="generating" class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                    <svg v-else class="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                    <span>[[ generating ? 'AI is Writing...' : 'AI: Draft Story' ]]</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Sidebar / Recent Activity -->
                <div class="lg:col-span-4 space-y-6">
                    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                        <h3 class="font-bold text-slate-800 mb-4 flex items-center">
                            <svg class="w-5 h-5 mr-2 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            Tips for Success
                        </h3>
                        <ul class="space-y-4">
                            <li class="flex items-start space-x-3 text-sm">
                                <div class="w-5 h-5 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0 font-bold">1</div>
                                <p class="text-slate-600">Be descriptive in your story content for better AI visualization.</p>
                            </li>
                            <li class="flex items-start space-x-3 text-sm">
                                <div class="w-5 h-5 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0 font-bold">2</div>
                                <p class="text-slate-600">Use "Shorts" format for TikTok, Reels, and YouTube Shorts.</p>
                            </li>
                            <li class="flex items-start space-x-3 text-sm">
                                <div class="w-5 h-5 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0 font-bold">3</div>
                                <p class="text-slate-600">Connect your YouTube channel to automate uploads.</p>
                            </li>
                        </ul>
                    </div>

                    <div v-if="channels.length === 0" class="bg-indigo-600 rounded-2xl shadow-lg p-6 text-white">
                        <h3 class="font-bold mb-2">Grow your channel</h3>
                        <p class="text-indigo-100 text-sm mb-4 leading-relaxed">Connect your YouTube account to automatically upload your generated videos with AI-optimized metadata.</p>
                        <a href="{{ route('youtube.auth') }}" class="block w-full text-center bg-white text-indigo-600 font-bold py-3 rounded-xl hover:bg-indigo-50 transition-colors">
                            Connect YouTube
                        </a>
                    </div>
                </div>
            </div>

            <!-- Your Stories Grid -->
            <section v-if="stories.length > 0" class="mt-20">
                <div class="flex items-center justify-between mb-8">
                    <div>
                        <h2 class="text-3xl font-bold text-slate-900">Your Gallery</h2>
                        <p class="text-slate-500">View and manage your generated videos</p>
                    </div>
                    <div class="bg-white border border-slate-200 rounded-lg px-4 py-2 text-sm font-medium text-slate-600">
                        [[ stories.length ]] Total Stories
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                    <div v-for="story in stories" :key="story.id"
                         class="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-xl transition-all duration-300 group flex flex-col h-full">

                        <!-- Video Preview Area -->
                        <div class="relative rounded-t-2xl overflow-hidden bg-slate-900 aspect-video flex items-center justify-center">
                            <video v-if="story.status === 'completed' && story.video_path"
                                   controls class="w-full h-full object-contain"
                                   :class="story.aspect_ratio === '9:16' ? 'max-w-[180px] mx-auto' : ''">
                                <source :src="'/storage/' + story.video_path" type="video/mp4">
                            </video>

                            <!-- Status Overlay for Processing -->
                            <div v-if="story.status === 'processing' || story.status === 'pending'"
                                 class="absolute inset-0 bg-slate-900/80 flex flex-col items-center justify-center p-6 text-center">
                                <div class="relative w-16 h-16 mb-4">
                                    <div class="absolute inset-0 rounded-full border-4 border-indigo-500/20"></div>
                                    <div class="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
                                </div>
                                <h4 class="text-white font-bold mb-1">AI is working...</h4>
                                <p class="text-indigo-300 text-[10px] uppercase tracking-widest">
                                    [[ story.scenes_count > 0 ? 'Parsing Scenes' : 'Initializing' ]]
                                </p>
                            </div>

                            <!-- Failed State Overlay -->
                            <div v-if="story.status === 'failed'" class="absolute inset-0 bg-red-900/20 flex flex-col items-center justify-center">
                                <svg class="w-12 h-12 text-red-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                <span class="text-red-700 font-bold">Generation Failed</span>
                            </div>

                            <!-- Actions Badge -->
                            <div class="absolute top-4 right-4 flex space-x-2">
                                <button v-if="story.status === 'completed' || story.status === 'failed'"
                                        @click="regenerateVideo(story)"
                                        class="p-2 bg-white/10 hover:bg-indigo-500 text-white rounded-lg backdrop-blur-md transition-all group/btn"
                                        title="Regenerate Video">
                                    <svg class="w-4 h-4 group-hover/btn:rotate-180 transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                                </button>
                                <button @click="deleteStory(story)"
                                        class="p-2 bg-white/10 hover:bg-red-500 text-white rounded-lg backdrop-blur-md transition-all"
                                        title="Delete Story">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                </button>
                            </div>
                        </div>

                        <!-- Content Area -->
                        <div class="p-6 flex-1 flex flex-col">
                            <div class="flex justify-between items-start mb-3">
                                <h3 class="font-bold text-slate-900 line-clamp-1 group-hover:text-indigo-600 transition-colors">[[ story.title || 'Untitled Story' ]]</h3>
                                <span :class="statusClass(story.status)" class="text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-wider">
                                    [[ story.status ]]
                                </span>
                            </div>

                            <p class="text-slate-500 text-sm line-clamp-2 mb-6 leading-relaxed">[[ story.content ]]</p>

                            <div class="mt-auto space-y-4">
                                <!-- Progress Steps for Processing -->
                                <div v-if="story.status === 'processing' || story.status === 'pending'" class="grid grid-cols-4 gap-1">
                                    <div v-for="step in 4" :key="step" class="h-1 rounded-full"
                                         :class="story.scenes_count >= step ? 'bg-indigo-500' : 'bg-slate-100'"></div>
                                </div>

                                <!-- Actions for Completed -->
                                <div v-if="story.status === 'completed'" class="space-y-3">
                                    <div class="flex items-center justify-between text-xs text-slate-400">
                                        <span>Created [[ formatDate(story.created_at) ]]</span>
                                        <span class="font-bold text-slate-600 uppercase">[[ story.aspect_ratio ]]</span>
                                    </div>

                                    <div class="grid grid-cols-2 gap-2">
                                        <a :href="'/storage/' + story.video_path" download
                                           class="flex items-center justify-center space-x-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-2 rounded-xl transition-all text-sm">
                                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                                            <span>Save</span>
                                        </a>
                                        <button v-if="!story.youtube_upload_status || story.youtube_upload_status === 'failed'"
                                                @click="uploadToYouTube(story)"
                                                class="flex items-center justify-center space-x-2 bg-red-600 hover:bg-red-700 text-white font-bold py-2 rounded-xl transition-all text-sm">
                                            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                                            <span>Publish</span>
                                        </button>
                                        <div v-else class="col-span-2">
                                            <div v-if="story.youtube_upload_status === 'completed'" class="w-full flex items-center justify-between p-2 bg-blue-50 text-blue-700 rounded-xl border border-blue-100">
                                                <div class="flex items-center">
                                                    <img :src="story.youtube_channel?.channel_thumbnail" class="w-5 h-5 rounded-full mr-2">
                                                    <span class="text-[10px] font-bold">LIVE ON YOUTUBE</span>
                                                </div>
                                                <a :href="'https://youtube.com/watch?v=' + story.youtube_video_id" target="_blank" class="text-[10px] underline font-bold">WATCH</a>
                                            </div>
                                            <div v-else-if="story.youtube_upload_status === 'uploading'" class="w-full flex items-center justify-center p-2 bg-yellow-50 text-yellow-700 rounded-xl border border-yellow-100">
                                                <svg class="animate-spin h-3 w-3 mr-2" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                                <span class="text-[10px] font-bold">UPLOADING...</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </main>

        <!-- Publish Modal -->
        <div v-if="showPublishModal" class="fixed inset-0 z-[100] overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <!-- Background overlay -->
                <div @click="showPublishModal = false" class="fixed inset-0 bg-slate-900/75 backdrop-blur-sm transition-opacity" aria-hidden="true"></div>

                <!-- Modal panel -->
                <div class="inline-block align-bottom bg-white rounded-3xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full animate-in zoom-in-95 duration-200">
                    <div class="bg-white px-6 pt-6 pb-8">
                        <div class="flex items-center justify-between mb-6">
                            <h3 class="text-2xl font-bold text-slate-900" id="modal-title">Publish to YouTube</h3>
                            <button @click="showPublishModal = false" class="text-slate-400 hover:text-slate-600 transition-colors">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                            </button>
                        </div>

                        <div class="space-y-5">
                            <!-- Channel Selection -->
                            <div>
                                <label class="block text-slate-700 text-sm font-semibold mb-2">Select Channel</label>
                                <div class="grid grid-cols-2 gap-3">
                                    <div v-for="channel in channels" :key="channel.id"
                                         @click="publishForm.youtube_token_id = channel.id"
                                         :class="['flex items-center p-3 border rounded-xl cursor-pointer transition-all',
                                                  publishForm.youtube_token_id === channel.id ? 'border-red-500 bg-red-50 ring-2 ring-red-100' : 'bg-white border-slate-200 hover:border-red-300']">
                                        <img :src="channel.channel_thumbnail" class="w-8 h-8 rounded-full shadow-sm mr-3">
                                        <span class="text-xs font-bold truncate">[[ channel.channel_title ]]</span>
                                    </div>
                                </div>
                            </div>

                            <!-- Title -->
                            <div>
                                <label class="block text-slate-700 text-sm font-semibold mb-2">YouTube Title</label>
                                <input v-model="publishForm.youtube_title" type="text"
                                       class="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 transition-all"
                                       placeholder="Enter a catchy title...">
                            </div>

                            <!-- Tags -->
                            <div>
                                <label class="block text-slate-700 text-sm font-semibold mb-2">Tags (comma separated)</label>
                                <input v-model="publishForm.youtube_tags" type="text"
                                       class="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 transition-all"
                                       placeholder="ai, story, animation...">
                            </div>

                            <!-- Description -->
                            <div>
                                <label class="block text-slate-700 text-sm font-semibold mb-2">Description</label>
                                <textarea v-model="publishForm.youtube_description" rows="4"
                                          class="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 transition-all text-sm"
                                          placeholder="Enter video description..."></textarea>
                            </div>
                        </div>
                    </div>

                    <div class="bg-slate-50 px-6 py-4 flex flex-row-reverse space-x-3 space-x-reverse">
                        <button @click="confirmPublish"
                                class="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg shadow-red-100 flex items-center justify-center space-x-2">
                            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                            <span>Start Upload</span>
                        </button>
                        <button @click="showPublishModal = false"
                                class="px-6 py-3 text-slate-600 font-bold hover:bg-slate-100 rounded-xl transition-colors">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const { createApp, ref, onMounted, watch } = Vue;

        createApp({
            delimiters: ['[[', ']]'],
            setup() {
                const stories = ref([]);
                const loading = ref(false);
                const generating = ref(false);
                const searching_news = ref(false);
                const news_results = ref([]);
                const showYoutubeSettings = ref(false);
                const showPublishModal = ref(false);
                const publishingStory = ref(null);
                const publishForm = ref({
                    youtube_title: '',
                    youtube_description: '',
                    youtube_tags: '',
                    youtube_token_id: null
                });
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
                const channels = ref([]);

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

                const fetchStories = async () => {
                    try {
                        const response = await axios.get('/api/stories');
                        stories.value = response.data;
                    } catch (error) {
                        console.error('Error fetching stories:', error);
                    }
                };

                const fetchChannels = async () => {
                    try {
                        const response = await axios.get('/api/youtube/channels');
                        channels.value = response.data;
                        if (channels.value.length > 0 && !newStory.value.youtube_token_id) {
                            newStory.value.youtube_token_id = channels.value[0].id;
                        }
                    } catch (error) {
                        console.error('Error fetching channels:', error);
                    }
                };

                const searchNews = async () => {
                    if (!newStory.value.search_query) return;
                    searching_news.value = true;
                    try {
                        const response = await axios.get(`/api/news/search?q=${encodeURIComponent(newStory.value.search_query)}`);
                        news_results.value = response.data;
                    } catch (error) {
                        console.error('Error searching news:', error);
                    } finally {
                        searching_news.value = false;
                    }
                };

                const selectNews = (news) => {
                    newStory.value.content = `Latest news about ${newStory.value.search_query}:\n\n${news.title}\n\n${news.snippet}`;
                    newStory.value.title = news.title;
                    news_results.value = [];
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
                        const currentStyle = newStory.value.style;
                        const currentToken = newStory.value.youtube_token_id;
                        newStory.value = {
                            title: '',
                            content: '',
                            aspect_ratio: '9:16',
                            style: currentStyle,
                            youtube_title: '',
                            youtube_description: '',
                            youtube_tags: '',
                            youtube_token_id: currentToken,
                            search_query: ''
                        };
                        fetchStories();
                    } catch (error) {
                        console.error('Error submitting story:', error);
                    } finally {
                        loading.value = false;
                    }
                };

                const openPublishModal = (story) => {
                    publishingStory.value = story;
                    publishForm.value = {
                        youtube_title: story.youtube_title || story.title,
                        youtube_description: story.youtube_description || story.content,
                        youtube_tags: story.youtube_tags || '',
                        youtube_token_id: story.youtube_token_id || (channels.value.length > 0 ? channels.value[0].id : null)
                    };
                    showPublishModal.value = true;
                };

                const confirmPublish = async () => {
                    if (!publishingStory.value) return;

                    try {
                        // 1. Update metadata first
                        await axios.patch(`/api/stories/${publishingStory.value.id}`, publishForm.value);

                        // 2. Trigger upload
                        publishingStory.value.youtube_upload_status = 'uploading';
                        await axios.post(`/api/stories/${publishingStory.value.id}/upload`);

                        showPublishModal.value = false;
                        fetchStories();
                    } catch (error) {
                        console.error('Error starting upload:', error);
                        if (publishingStory.value) {
                            publishingStory.value.youtube_upload_status = 'failed';
                        }
                    }
                };

                const uploadToYouTube = async (story) => {
                    openPublishModal(story);
                };

                const regenerateVideo = async (story) => {
                    if (!confirm('Re-run AI generation for this story? Existing video will be replaced.')) return;
                    try {
                        story.status = 'pending';
                        await axios.post(`/api/stories/${story.id}/regenerate`);
                        fetchStories();
                    } catch (error) {
                        console.error('Error regenerating story:', error);
                    }
                };

                const formatDate = (dateString) => {
                    return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                };

                const statusClass = (status) => {
                    switch (status) {
                        case 'completed': return 'bg-emerald-100 text-emerald-700';
                        case 'processing': return 'bg-indigo-100 text-indigo-700';
                        case 'pending': return 'bg-amber-100 text-amber-700';
                        case 'failed': return 'bg-rose-100 text-rose-700';
                        default: return 'bg-slate-100 text-slate-700';
                    }
                };

                const deleteStory = async (story) => {
                    if (!confirm('Delete this story permanently?')) return;
                    try {
                        await axios.delete(`/api/stories/${story.id}`);
                        stories.value = stories.value.filter(s => s.id !== story.id);
                    } catch (error) {
                        console.error('Error deleting story:', error);
                    }
                };

                onMounted(() => {
                    fetchStories();
                    fetchChannels();
                    setInterval(fetchStories, 5000);
                });

                return {
                    stories, newStory, loading, generating, channels, searching_news,
                    news_results, showYoutubeSettings, showPublishModal, publishingStory,
                    publishForm, openPublishModal, confirmPublish, generateStory,
                    submitStory, searchNews, selectNews, uploadToYouTube, regenerateVideo, deleteStory,
                    formatDate, statusClass
                };
            }
        }).mount('#app');
    </script>
</body>
</html>
