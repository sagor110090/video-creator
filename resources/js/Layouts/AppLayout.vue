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
    <div class="flex h-screen bg-[#0a0a0a] text-white font-sans selection:bg-[#00f0ff]/20 cyber-grid scanlines">
        <!-- Mobile Sidebar Backdrop -->
        <div v-if="isSidebarOpen" @click="isSidebarOpen = false" class="fixed inset-0 z-40 bg-[#0a0a0a]/90 md:hidden transition-opacity duration-300"></div>

        <!-- Sidebar -->
        <aside :class="[
            'w-72 bg-[#111111] border-r border-[#222222] flex flex-col z-50 transition-all duration-500 ease-in-out circuit-pattern',
            'fixed inset-y-0 left-0 md:relative md:translate-x-0',
            isSidebarOpen ? 'translate-x-0 neon-glow-cyan' : '-translate-x-full md:shadow-none'
        ]">
            <!-- App Logo / Header -->
            <div class="h-20 flex items-center justify-between px-6 drag-region border-b border-[#222222]">
                <div class="flex items-center group cursor-pointer">
                    <div class="relative">
                        <div class="relative w-10 h-10 bg-[#1a1a1a] border border-[#00f0ff]/30 rounded-sm flex items-center justify-center transform group-hover:scale-105 transition-transform duration-300 neon-glow-cyan">
                            <svg class="w-6 h-6 text-[#00f0ff]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                        </div>
                    </div>
                    <div class="ml-3">
                        <span class="text-xl font-black tracking-tight text-white font-cyber glitch-effect">VideoAI</span>
                        <div class="h-0.5 w-0 group-hover:w-full bg-[#00f0ff] transition-all duration-300 neon-glow-cyan"></div>
                    </div>
                </div>
                <!-- Close Button (Mobile) -->
                <button @click="isSidebarOpen = false" class="md:hidden p-2 text-[#666666] hover:text-[#00f0ff] hover:bg-[#1a1a1a] transition-colors no-drag focus:outline-none border border-[#222222]">
                    <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Navigation -->
            <nav class="flex-1 px-3 py-6 space-y-1 overflow-y-auto custom-scrollbar">
                <div class="px-3 mb-4">
                    <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-[#666666] font-terminal">System Menu</p>
                </div>
                <Link
                    v-for="item in navigation"
                    :key="item.name"
                    :href="item.href"
                    class="group relative flex items-center px-3 py-2.5 text-sm font-semibold rounded-sm transition-all duration-300 overflow-hidden"
                    :class="[
                        url === item.href
                            ? 'text-white bg-[#1a1a1a] border border-[#00f0ff]/50'
                            : 'text-[#666666] hover:text-[#00f0ff] hover:bg-[#1a1a1a]/50 border border-transparent hover:border-[#00f0ff]/30'
                    ]"
                    @click="isSidebarOpen = false"
                >
                    <!-- Active Background Glow -->
                    <div v-if="url === item.href" class="absolute inset-0 bg-[#00f0ff]/5"></div>
                    <div v-if="url === item.href" class="absolute left-0 top-2 bottom-2 w-0.5 bg-[#00f0ff] neon-glow-cyan"></div>

                    <!-- Icons -->
                    <div class="relative flex items-center justify-center w-8 h-8 mr-3 transition-all duration-300"
                        :class="[
                            url === item.href
                                ? 'text-[#00f0ff]'
                                : 'text-[#666666] group-hover:text-[#00f0ff]'
                        ]"
                    >
                        <svg v-if="item.icon === 'HomeIcon'" class="h-5 w-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                        </svg>

                        <svg v-else-if="item.icon === 'ChartBarIcon'" class="h-5 w-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
                        </svg>

                        <svg v-else-if="item.icon === 'VideoCameraIcon'" class="h-5 w-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>

                        <svg v-else-if="item.icon === 'ClockIcon'" class="h-5 w-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>

                    <span class="relative font-bold tracking-tight font-cyber">{{ item.name }}</span>
                </Link>
            </nav>

            <!-- Bottom Section -->
            <div class="p-4 border-t border-[#222222]">
                <div class="holographic rounded-sm p-3">
                    <div class="flex items-center gap-2 mb-2">
                        <div class="w-2 h-2 bg-[#00f0ff] rounded-full neon-glow-cyan animate-pulse"></div>
                        <span class="text-[10px] font-bold uppercase tracking-wider text-[#00f0ff] font-terminal">System Online</span>
                    </div>
                    <p class="text-[10px] text-[#666666] font-terminal">v2.0.77 // Cyberpunk Edition</p>
                </div>
            </div>
        </aside>

        <!-- Main Content Area -->
        <div class="flex-1 flex flex-col overflow-hidden w-full relative">
            <!-- Top Bar -->
            <header class="h-20 bg-[#111111] border-b border-[#222222] flex items-center justify-between px-8 z-30 drag-region circuit-pattern">
                <div class="flex items-center">
                    <!-- Hamburger Button -->
                    <button @click="isSidebarOpen = true" class="mr-6 md:hidden p-2 text-[#666666] hover:text-[#00f0ff] hover:bg-[#1a1a1a] transition-all no-drag focus:outline-none border border-[#222222] rounded-sm">
                        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
                    <div>
                        <h1 class="text-2xl font-black text-white tracking-tight font-cyber">
                            <slot name="header"></slot>
                        </h1>
                    </div>
                </div>
                <div class="flex items-center space-x-6 no-drag">
                    <slot name="actions"></slot>
                </div>
            </header>

            <!-- Page Content -->
            <main class="flex-1 overflow-y-auto bg-[#0a0a0a] p-8 custom-scrollbar relative cyber-mesh">
                <div class="max-w-7xl mx-auto">
                    <slot></slot>
                </div>
            </main>
        </div>
    </div>
</template>

<style>
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
