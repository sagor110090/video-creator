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
    <div class="flex h-screen bg-slate-50 dark:bg-slate-950">
        <!-- Mobile Sidebar Backdrop -->
        <div v-if="isSidebarOpen" @click="isSidebarOpen = false" class="fixed inset-0 z-40 bg-black/50 md:hidden backdrop-blur-sm transition-opacity"></div>

        <!-- Sidebar -->
        <div :class="[
            'w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col z-50 transition-transform duration-300 ease-in-out',
            'fixed inset-y-0 left-0 md:relative md:translate-x-0',
            isSidebarOpen ? 'translate-x-0 shadow-xl' : '-translate-x-full md:shadow-none'
        ]">
            <!-- App Logo / Header -->
            <div class="h-16 flex items-center justify-between px-6 border-b border-slate-200 dark:border-slate-800 drag-region">
                <div class="flex items-center">
                    <div class="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center mr-3">
                        <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                    </div>
                    <span class="text-lg font-bold text-slate-900 dark:text-white">VideoAI</span>
                </div>
                <!-- Close Button (Mobile) -->
                <button @click="isSidebarOpen = false" class="md:hidden text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-white no-drag focus:outline-none">
                    <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Navigation -->
            <nav class="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
                <Link
                    v-for="item in navigation"
                    :key="item.name"
                    :href="item.href"
                    class="group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-150"
                    :class="[
                        url === item.href
                            ? 'bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400'
                            : 'text-slate-700 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white'
                    ]"
                    @click="isSidebarOpen = false"
                >
                    <!-- Icons -->
                    <svg v-if="item.icon === 'HomeIcon'" class="mr-3 h-5 w-5 flex-shrink-0" :class="url === item.href ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400 group-hover:text-slate-500 dark:group-hover:text-slate-300'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>

                    <svg v-else-if="item.icon === 'ChartBarIcon'" class="mr-3 h-5 w-5 flex-shrink-0" :class="url === item.href ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400 group-hover:text-slate-500 dark:group-hover:text-slate-300'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
                    </svg>
                    <svg v-else-if="item.icon === 'VideoCameraIcon'" class="mr-3 h-5 w-5 flex-shrink-0" :class="url === item.href ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400 group-hover:text-slate-500 dark:group-hover:text-slate-300'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <svg v-else-if="item.icon === 'ClockIcon'" class="mr-3 h-5 w-5 flex-shrink-0" :class="url === item.href ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400 group-hover:text-slate-500 dark:group-hover:text-slate-300'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {{ item.name }}
                </Link>
            </nav>


        </div>

        <!-- Main Content Area -->
        <div class="flex-1 flex flex-col overflow-hidden w-full">
            <!-- Top Bar -->
            <header class="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 sm:px-6 drag-region">
                <div class="flex items-center">
                    <!-- Hamburger Button -->
                    <button @click="isSidebarOpen = true" class="mr-4 md:hidden text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-white no-drag focus:outline-none">
                        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
                    <h1 class="text-xl font-bold text-slate-900 dark:text-white truncate">
                        <slot name="header"></slot>
                    </h1>
                </div>
                <div class="flex items-center space-x-4 no-drag">
                    <slot name="actions"></slot>
                </div>
            </header>

            <!-- Page Content -->
            <main class="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-950 p-4 sm:p-6">
                <slot></slot>
            </main>
        </div>
    </div>
</template>

<style scoped>
.drag-region {
    -webkit-app-region: drag;
}
.no-drag {
    -webkit-app-region: no-drag;
}
</style>
