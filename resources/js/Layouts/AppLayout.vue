<script setup>
import { Link, usePage } from '@inertiajs/vue3';
import { computed, ref } from 'vue';

const page = usePage();
const url = computed(() => page.url);
const isSidebarOpen = ref(false);

const navigation = [
    { name: 'Dashboard', href: '/', icon: 'HomeIcon' },
    { name: 'Schedules', href: '/schedules', icon: 'ClockIcon' },
    { name: 'YouTube Channels', href: '/youtube/channels', icon: 'VideoCameraIcon' },
    { name: 'Statistics', href: '/statistics', icon: 'ChartBarIcon' },
];
</script>

<template>
    <div class="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans selection:bg-slate-900/10 dark:selection:bg-white/10">
        <!-- Mobile Sidebar Backdrop -->
        <div v-if="isSidebarOpen" @click="isSidebarOpen = false" class="fixed inset-0 z-40 bg-slate-950/50 md:hidden transition-opacity duration-300"></div>

        <!-- Sidebar -->
        <aside :class="[
            'w-72 bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 flex flex-col z-50 transition-all duration-500 ease-in-out',
            'fixed inset-y-0 left-0 md:relative md:translate-x-0',
            isSidebarOpen ? 'translate-x-0 shadow-2xl shadow-slate-900/10 dark:shadow-black/30' : '-translate-x-full md:shadow-none'
        ]">
            <!-- App Logo / Header -->
            <div class="h-20 flex items-center justify-between px-8 drag-region">
                <div class="flex items-center group cursor-pointer">
                    <div class="relative">
                        <div class="relative w-10 h-10 bg-slate-900 dark:bg-white rounded-xl flex items-center justify-center transform group-hover:scale-105 transition-transform duration-300 shadow-sm">
                            <svg class="w-6 h-6 text-white dark:text-slate-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                        </div>
                    </div>
                    <div class="ml-4">
                        <span class="text-xl font-black tracking-tight text-slate-900 dark:text-white">VideoAI</span>
                        <div class="h-0.5 w-0 group-hover:w-full bg-slate-900 dark:bg-white transition-all duration-300"></div>
                    </div>
                </div>
                <!-- Close Button (Mobile) -->
                <button @click="isSidebarOpen = false" class="md:hidden p-2 rounded-lg text-slate-400 hover:text-slate-900 hover:bg-slate-100 dark:hover:bg-slate-900 transition-colors no-drag focus:outline-none">
                    <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Navigation -->
            <nav class="flex-1 px-4 py-8 space-y-2 overflow-y-auto custom-scrollbar">
                <div class="px-4 mb-4">
                    <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">Main Menu</p>
                </div>
                <Link
                    v-for="item in navigation"
                    :key="item.name"
                    :href="item.href"
                    class="group relative flex items-center px-4 py-3 text-sm font-semibold rounded-xl transition-all duration-300 overflow-hidden"
                    :class="[
                        url === item.href
                            ? 'text-slate-900 dark:text-white'
                            : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                    ]"
                    @click="isSidebarOpen = false"
                >
                    <!-- Active Background Indicator -->
                    <div v-if="url === item.href" class="absolute inset-0 bg-slate-100 dark:bg-slate-900"></div>
                    <div v-if="url === item.href" class="absolute left-0 top-3 bottom-3 w-0.5 bg-slate-900 dark:bg-white rounded-r-full"></div>

                    <!-- Icons -->
                    <div class="relative flex items-center justify-center w-8 h-8 mr-3 rounded-lg transition-all duration-300"
                        :class="[
                            url === item.href
                                ? 'bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800'
                                : 'bg-transparent group-hover:bg-slate-100 dark:group-hover:bg-slate-900'
                        ]"
                    >
                        <svg v-if="item.icon === 'HomeIcon'" class="h-5 w-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110" :class="url === item.href ? 'text-slate-900 dark:text-white' : 'text-slate-400 group-hover:text-slate-700 dark:group-hover:text-slate-200'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                        </svg>

                        <svg v-else-if="item.icon === 'ChartBarIcon'" class="h-5 w-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110" :class="url === item.href ? 'text-slate-900 dark:text-white' : 'text-slate-400 group-hover:text-slate-700 dark:group-hover:text-slate-200'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
                        </svg>

                        <svg v-else-if="item.icon === 'VideoCameraIcon'" class="h-5 w-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110" :class="url === item.href ? 'text-slate-900 dark:text-white' : 'text-slate-400 group-hover:text-slate-700 dark:group-hover:text-slate-200'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>

                        <svg v-else-if="item.icon === 'ClockIcon'" class="h-5 w-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110" :class="url === item.href ? 'text-slate-900 dark:text-white' : 'text-slate-400 group-hover:text-slate-700 dark:group-hover:text-slate-200'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>

                    <span class="relative font-bold tracking-tight">{{ item.name }}</span>
                </Link>
            </nav>

            <!-- Bottom Section -->
            <div class="p-6 mt-auto">
                <div class="rounded-2xl p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm">
                    <p class="text-slate-900 dark:text-white font-bold text-sm mb-1">Upgrade Plan</p>
                    <p class="text-slate-500 dark:text-slate-400 text-xs mb-3">Unlock pro AI features</p>
                    <button class="w-full py-2.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl text-xs font-black hover:bg-slate-800 dark:hover:bg-slate-100 transition-colors shadow-sm">
                        Go Premium
                    </button>
                </div>
            </div>
        </aside>

        <!-- Main Content Area -->
            <div class="flex-1 flex flex-col overflow-hidden w-full relative">
            <!-- Top Bar -->
            <header class="h-20 bg-white dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-8 z-30 drag-region">
                <div class="flex items-center">
                    <!-- Hamburger Button -->
                    <button @click="isSidebarOpen = true" class="mr-6 md:hidden p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:hover:bg-slate-900 transition-all no-drag focus:outline-none shadow-sm border border-slate-200 dark:border-slate-800">
                        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
                    <div>
                        <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
                            <slot name="header"></slot>
                        </h1>
                        <p class="text-xs text-slate-400 dark:text-slate-500 font-medium">Welcome back, {{ $page.props.auth?.user?.name || 'Guest' }}</p>
                    </div>
                </div>
                <div class="flex items-center space-x-6 no-drag">
                    <slot name="actions"></slot>

                    <!-- User Profile -->
                    <div class="flex items-center space-x-3 pl-6 border-l border-slate-200 dark:border-slate-800">
                        <div class="hidden sm:block text-right">
                            <p class="text-sm font-bold text-slate-900 dark:text-white leading-none">{{ $page.props.auth?.user?.name || 'Guest' }}</p>
                            <p class="text-[10px] text-slate-400 dark:text-slate-500 font-medium mt-1">Free Tier</p>
                        </div>
                        <div class="w-10 h-10 rounded-2xl bg-slate-900 dark:bg-white flex items-center justify-center text-white dark:text-slate-900 font-black shadow-sm ring-1 ring-slate-200 dark:ring-slate-800">
                            {{ ($page.props.auth?.user?.name || 'G').charAt(0) }}
                        </div>
                    </div>
                </div>
            </header>

            <!-- Page Content -->
            <main class="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-950 p-8 custom-scrollbar relative">
                <div class="max-w-7xl mx-auto">
                    <slot></slot>
                </div>
            </main>
        </div>
    </div>
</template>

<style>
/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #e2e8f0;
    border-radius: 10px;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb {
    background: #1e293b;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #cbd5e1;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #334155;
}

.drag-region {
    -webkit-app-region: drag;
}
.no-drag {
    -webkit-app-region: no-drag;
}
</style>

<style scoped>
.drag-region {
    -webkit-app-region: drag;
}
.no-drag {
    -webkit-app-region: no-drag;
}
</style>
