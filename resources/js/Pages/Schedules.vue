<script setup>
import AppLayout from '@/Layouts/AppLayout.vue';
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { Head } from '@inertiajs/vue3';
import Swal from 'sweetalert2';

const schedules = ref({ data: [] });
const channels = ref([]);
const loading = ref(false);
const creating = ref(false);
const updating = ref(false);
const showEditModal = ref(false);
const editingSchedule = ref(null);
const isDark = ref(false);

const newSchedule = ref({
    topic: '',
    style: 'story',
    talking_style: 'none',
    aspect_ratio: '16:9',
    scheduled_time: '',
    youtube_token_id: null
});

const editForm = ref({
    topic: '',
    style: 'story',
    talking_style: 'none',
    aspect_ratio: '16:9',
    scheduled_time: '',
    youtube_token_id: null
});

const fetchSchedules = async (page = 1) => {
    loading.value = true;
    try {
        const response = await axios.get(`/api/schedules?page=${page}`);
        schedules.value = response.data;
    } catch (error) {
        console.error('Error fetching schedules:', error);
    } finally {
        loading.value = false;
    }
};

const fetchChannels = async () => {
    try {
        const response = await axios.get('/api/youtube/channels');
        channels.value = response.data;
        if (channels.value.length > 0 && !newSchedule.value.youtube_token_id) {
            newSchedule.value.youtube_token_id = channels.value[0].id;
        }
    } catch (error) {
        console.error('Error fetching channels:', error);
    }
};

const createSchedule = async () => {
    creating.value = true;
    try {
        await axios.post('/api/schedules', newSchedule.value);
        newSchedule.value.topic = '';
        newSchedule.value.scheduled_time = '';
        fetchSchedules();
    } catch (error) {
        console.error('Error creating schedule:', error);
        Swal.fire({
            icon: 'error',
            title: 'Oops...',
            text: error.response?.data?.message || 'Failed to create schedule',
            confirmButtonColor: '#0b1021',
            background: isDark.value ? '#0f172a' : '#ffffff',
            color: isDark.value ? '#f8fafc' : '#0f172a'
        });
    } finally {
        creating.value = false;
    }
};

const openEditModal = (schedule) => {
    editingSchedule.value = schedule;
    editForm.value = {
        topic: schedule.topic || '',
        style: schedule.style || 'story',
        talking_style: schedule.talking_style || 'none',
        aspect_ratio: schedule.aspect_ratio || '16:9',
        scheduled_time: schedule.scheduled_time ? schedule.scheduled_time.substring(0, 5) : '',
        youtube_token_id: schedule.youtube_token_id
    };
    showEditModal.value = true;
};

const updateSchedule = async () => {
    if (!editingSchedule.value) return;
    updating.value = true;
    try {
        await axios.patch(`/api/schedules/${editingSchedule.value.id}`, editForm.value);
        showEditModal.value = false;
        fetchSchedules();
    } catch (error) {
        console.error('Error updating schedule:', error);
        Swal.fire({
            icon: 'error',
            title: 'Oops...',
            text: error.response?.data?.message || 'Failed to update schedule',
            confirmButtonColor: '#0b1021',
            background: isDark.value ? '#0f172a' : '#ffffff',
            color: isDark.value ? '#f8fafc' : '#0f172a'
        });
    } finally {
        updating.value = false;
    }
};

const copySchedule = (schedule) => {
    newSchedule.value = {
        topic: `${schedule.topic} (Copy)`,
        style: schedule.style,
        aspect_ratio: schedule.aspect_ratio,
        scheduled_time: schedule.scheduled_time.substring(0, 5),
        youtube_token_id: schedule.youtube_token_id
    };
    window.scrollTo({ top: 0, behavior: 'smooth' });
};

const deleteSchedule = async (id) => {
    const result = await Swal.fire({
        title: 'Delete Schedule?',
        text: "Are you sure you want to delete this schedule?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#b9382a',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Yes, delete it!',
        background: isDark.value ? '#0f172a' : '#ffffff',
        color: isDark.value ? '#f8fafc' : '#0f172a'
    });

    if (!result.isConfirmed) return;

    try {
        await axios.delete(`/api/schedules/${id}`);
        fetchSchedules();
    } catch (error) {
        console.error('Error deleting schedule:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to delete schedule',
            confirmButtonColor: '#0b1021',
            background: isDark.value ? '#0f172a' : '#ffffff',
            color: isDark.value ? '#f8fafc' : '#0f172a'
        });
    }
};

const getStatusColor = (status) => {
    switch (status) {
        case 'pending': return 'bg-[#f2ebe0] text-[#6a5d4d] dark:bg-slate-800 dark:text-slate-300';
        case 'processing': return 'bg-[#e3f5f4] text-[#2f6c73] dark:bg-slate-800 dark:text-slate-200';
        case 'completed': return 'bg-[#e8f4dc] text-[#3d5b2f] dark:bg-slate-800 dark:text-slate-200';
        case 'failed': return 'bg-[#fde7dd] text-[#b9382a] dark:bg-slate-800 dark:text-slate-200';
        default: return 'bg-[#f2ebe0] text-[#6a5d4d] dark:bg-slate-800 dark:text-slate-300';
    }
};

const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
};

const formatTime = (timeString) => {
    if (!timeString) return '--:--';
    // Remove seconds if present
    return timeString.substring(0, 5);
};

onMounted(() => {
    isDark.value = document.documentElement.classList.contains('dark');
    fetchSchedules();
    fetchChannels();
});
</script>

<template>
    <Head title="Video Schedules" />

    <AppLayout>
        <template #header>Video Schedules</template>

        <div class="space-y-8">
            <div class="relative overflow-hidden rounded-[32px] border border-[#e6dccf] dark:border-slate-800 bg-[#f7f2e8] dark:bg-slate-900/70 px-8 py-10 shadow-[0_30px_60px_-40px_rgba(15,23,42,0.4)]">
                <div class="absolute inset-0 bg-gradient-to-br from-[#fff7ee] via-transparent to-transparent dark:from-slate-900/60"></div>
                <div class="relative flex flex-col gap-4">
                    <p class="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#6a5d4d] dark:text-slate-400">Schedule Studio</p>
                    <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
                        <div>
                            <h2 class="text-3xl font-black text-[#15131a] dark:text-white">Video Schedules</h2>
                            <p class="text-sm text-[#6a5d4d] dark:text-slate-400 mt-2 max-w-2xl">Orchestrate daily publishing with precision, clarity, and a touch of ritual.</p>
                        </div>
                        <div class="flex flex-wrap gap-3">
                            <div class="rounded-full border border-[#e6dccf] dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 px-4 py-2 text-xs font-semibold text-[#6a5d4d] dark:text-slate-300">
                                {{ schedules.data.length }} Active
                            </div>
                            <div class="rounded-full border border-[#e6dccf] dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 px-4 py-2 text-xs font-semibold text-[#6a5d4d] dark:text-slate-300">
                                {{ channels.length }} Channels
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white dark:bg-slate-900 rounded-[28px] shadow-[0_30px_60px_-40px_rgba(15,23,42,0.35)] border border-[#e6dccf] dark:border-slate-800 p-8">
                <h3 class="text-lg font-black text-[#15131a] dark:text-white mb-6">Create New Schedule</h3>
                <form @submit.prevent="createSchedule" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    <div class="space-y-2">
                        <label class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400">Topic</label>
                        <input
                            v-model="newSchedule.topic"
                            type="text"
                            placeholder="e.g. History of Rome"
                            required
                            class="w-full px-4 py-3 bg-[#fbf7f1] dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 rounded-2xl focus:ring-2 focus:ring-[#c7a36c]/40 focus:border-[#c7a36c] outline-none transition-all dark:text-white"
                        />
                    </div>

                    <div class="space-y-2">
                        <label class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400">Daily Time</label>
                        <input
                            v-model="newSchedule.scheduled_time"
                            type="time"
                            required
                            class="w-full px-4 py-3 bg-[#fbf7f1] dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 rounded-2xl focus:ring-2 focus:ring-[#c7a36c]/40 focus:border-[#c7a36c] outline-none transition-all dark:text-white"
                        />
                    </div>

                    <div class="space-y-2">
                        <label class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400">YouTube Channel</label>
                        <select
                            v-model="newSchedule.youtube_token_id"
                            class="w-full px-4 py-3 bg-[#fbf7f1] dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 rounded-2xl focus:ring-2 focus:ring-[#c7a36c]/40 focus:border-[#c7a36c] outline-none transition-all dark:text-white"
                        >
                            <option v-for="channel in channels" :key="channel.id" :value="channel.id">
                                {{ channel.channel_title }}
                            </option>
                        </select>
                    </div>

                    <div class="space-y-2">
                        <label class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400">Content Style</label>
                        <select
                            v-model="newSchedule.style"
                            class="w-full px-4 py-3 bg-[#fbf7f1] dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 rounded-2xl focus:ring-2 focus:ring-[#c7a36c]/40 focus:border-[#c7a36c] outline-none transition-all dark:text-white"
                        >
                            <option value="story">Story</option>
                            <option value="science_short">Science Short</option>
                            <option value="hollywood_hype">Hollywood Hype</option>
                            <option value="bollywood_masala">Bollywood Masala</option>
                            <option value="trade_wave">Trade Wave</option>
                        </select>
                    </div>

                    <div class="space-y-2">
                        <label class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400">Talking Style</label>
                        <select
                            v-model="newSchedule.talking_style"
                            class="w-full px-4 py-3 bg-[#fbf7f1] dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 rounded-2xl focus:ring-2 focus:ring-[#c7a36c]/40 focus:border-[#c7a36c] outline-none transition-all dark:text-white"
                        >
                            <option value="none">None (Default)</option>
                            <option value="opinion">Opinion</option>
                            <option value="storytime">Storytime</option>
                            <option value="educational">Educational</option>
                            <option value="reaction">Reaction</option>
                            <option value="vlog">Vlog</option>
                        </select>
                    </div>

                    <div class="space-y-2">
                        <label class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400">Aspect Ratio</label>
                        <select
                            v-model="newSchedule.aspect_ratio"
                            class="w-full px-4 py-3 bg-[#fbf7f1] dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 rounded-2xl focus:ring-2 focus:ring-[#c7a36c]/40 focus:border-[#c7a36c] outline-none transition-all dark:text-white"
                        >
                            <option value="16:9">Widescreen (16:9)</option>
                            <option value="9:16">Shorts/Reels (9:16)</option>
                        </select>
                    </div>

                    <div class="flex items-end">
                        <button
                            type="submit"
                            :disabled="creating"
                            class="w-full px-6 py-3 bg-[#0b1021] hover:bg-[#141a2f] disabled:bg-[#2e3346] text-[#f7f2e8] font-semibold rounded-full transition-all duration-300 flex items-center justify-center active:scale-95"
                        >
                            <svg v-if="creating" class="animate-spin -ml-1 mr-3 h-5 w-5 text-[#f7f2e8]" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            {{ creating ? 'Creating...' : 'Add Schedule' }}
                        </button>
                    </div>
                </form>
            </div>

            <div class="bg-white dark:bg-slate-900 rounded-[28px] shadow-[0_30px_60px_-40px_rgba(15,23,42,0.35)] border border-[#e6dccf] dark:border-slate-800 overflow-hidden">
                <div class="px-8 py-6 border-b border-[#e6dccf] dark:border-slate-800 flex items-center justify-between bg-[#f7f2e8] dark:bg-slate-900/80">
                    <div>
                        <p class="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#6a5d4d] dark:text-slate-400">Queue</p>
                        <h3 class="font-black text-[#15131a] dark:text-white">Active Schedules</h3>
                    </div>
                    <button @click="fetchSchedules()" class="p-2 rounded-full border border-[#e6dccf] dark:border-slate-700 bg-white dark:bg-slate-800 text-[#6a5d4d] dark:text-slate-300 hover:text-[#0b1021] dark:hover:text-white transition-all duration-300">
                        <svg class="w-5 h-5" :class="{'animate-spin': loading}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                    </button>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left">
                        <thead>
                            <tr class="bg-[#fbf7f1] dark:bg-slate-900/70 text-[#6a5d4d] dark:text-slate-400 text-[11px] uppercase tracking-[0.2em]">
                                <th class="px-6 py-4 font-semibold">Topic</th>
                                <th class="px-6 py-4 font-semibold">Channel</th>
                                <th class="px-6 py-4 font-semibold">Daily Time</th>
                                <th class="px-6 py-4 font-semibold">Last Run</th>
                                <th class="px-6 py-4 font-semibold">Status</th>
                                <th class="px-6 py-4 font-semibold text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-[#efe6d8] dark:divide-slate-800">
                            <tr v-if="schedules.data.length === 0" class="text-center">
                                <td colspan="6" class="px-6 py-10 text-[#6a5d4d] dark:text-slate-400">
                                    No schedules found. Create one above!
                                </td>
                            </tr>
                            <tr v-for="schedule in schedules.data" :key="schedule.id" class="transition-all duration-300 hover:bg-[#fbf7f1] dark:hover:bg-slate-900/60">
                                <td class="px-6 py-5">
                                    <div class="text-sm font-semibold text-[#15131a] dark:text-white">{{ schedule.topic }}</div>
                                    <div class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400">{{ schedule.style }} • {{ schedule.aspect_ratio }}</div>
                                </td>
                                <td class="px-6 py-5">
                                    <div v-if="schedule.youtube_token" class="flex items-center">
                                        <img :src="schedule.youtube_token.channel_thumbnail" class="w-7 h-7 rounded-full mr-3 ring-2 ring-[#f0e6d8] dark:ring-slate-700" />
                                        <span class="text-sm text-[#4b3f2f] dark:text-slate-300">{{ schedule.youtube_token.channel_title }}</span>
                                    </div>
                                    <span v-else class="text-xs text-[#b3a799] dark:text-slate-500">No channel</span>
                                </td>
                                <td class="px-6 py-5 text-sm font-semibold text-[#0b1021] dark:text-white">
                                    {{ formatTime(schedule.scheduled_time) }}
                                </td>
                                <td class="px-6 py-5 text-sm text-[#6a5d4d] dark:text-slate-300">
                                    {{ formatDate(schedule.last_run_at) }}
                                </td>
                                <td class="px-6 py-5">
                                    <span :class="['px-3 py-1 rounded-full text-[11px] font-semibold uppercase tracking-[0.2em]', getStatusColor(schedule.status)]">
                                        {{ schedule.status }}
                                    </span>
                                    <div v-if="schedule.last_error" class="text-[10px] text-[#b9382a] mt-2 max-w-[180px] truncate" :title="schedule.last_error">
                                        {{ schedule.last_error }}
                                    </div>
                                </td>
                                <td class="px-6 py-5 text-right">
                                    <div class="flex items-center justify-end gap-2">
                                        <button
                                            @click="copySchedule(schedule)"
                                            class="p-2 rounded-full border border-[#efe6d8] dark:border-slate-700 bg-white dark:bg-slate-800 text-[#6a5d4d] hover:text-[#0b1021] transition-all duration-300 active:scale-95"
                                            title="Copy Schedule"
                                        >
                                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                                            </svg>
                                        </button>
                                        <button
                                            @click="openEditModal(schedule)"
                                            class="p-2 rounded-full border border-[#efe6d8] dark:border-slate-700 bg-white dark:bg-slate-800 text-[#6a5d4d] hover:text-[#2f6c73] transition-all duration-300 active:scale-95"
                                            title="Edit Schedule"
                                        >
                                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                            </svg>
                                        </button>
                                        <button
                                            @click="deleteSchedule(schedule.id)"
                                            class="p-2 rounded-full border border-[#efe6d8] dark:border-slate-700 bg-white dark:bg-slate-800 text-[#6a5d4d] hover:text-[#b9382a] transition-all duration-300 active:scale-95"
                                            title="Delete Schedule"
                                        >
                                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                            </svg>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Pagination -->
                <div v-if="schedules.links && schedules.links.length > 3" class="px-6 py-5 bg-[#fbf7f1] dark:bg-slate-900/70 border-t border-[#e6dccf] dark:border-slate-800 flex justify-center">
                    <nav class="flex flex-wrap gap-2">
                        <button
                            v-for="link in schedules.links"
                            :key="link.label"
                            @click="fetchSchedules(link.url ? new URL(link.url).searchParams.get('page') : 1)"
                            :disabled="!link.url"
                            v-html="link.label"
                            :class="[
                                'px-4 py-2 rounded-full text-xs font-semibold transition-all duration-300 border',
                                link.active ? 'bg-[#0b1021] text-[#f7f2e8] border-[#0b1021]' : 'bg-white dark:bg-slate-800 border-[#efe6d8] dark:border-slate-700 text-[#6a5d4d] dark:text-slate-300 hover:border-[#c7a36c]'
                            ]"
                        ></button>
                    </nav>
                </div>
            </div>
        </div>

        <!-- Edit Modal -->
        <Teleport to="body">
            <div v-if="showEditModal" class="fixed inset-0 z-[9999] overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
                    <div class="fixed inset-0 bg-[#0b1021]/70 backdrop-blur-md transition-opacity" aria-hidden="true" @click="showEditModal = false"></div>

                    <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                    <div class="relative inline-block align-bottom bg-white dark:bg-slate-900 rounded-[32px] text-left overflow-hidden shadow-[0_30px_80px_-20px_rgba(11,16,33,0.6)] transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full border border-[#e6dccf] dark:border-slate-800 z-50">
                        <div class="bg-white dark:bg-slate-900 px-6 pt-6 pb-6">
                            <div class="sm:flex sm:items-start">
                                <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                                    <div class="flex items-center justify-between mb-8">
                                        <h3 class="text-2xl font-black text-[#15131a] dark:text-white tracking-tight" id="modal-title">
                                            Edit Schedule
                                        </h3>
                                        <button @click="showEditModal = false" class="p-2 -mr-2 text-[#b3a799] hover:text-[#0b1021] dark:text-slate-500 dark:hover:text-slate-300 transition-all rounded-full hover:bg-[#f2ebe0] dark:hover:bg-slate-800">
                                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
                                            </svg>
                                        </button>
                                    </div>

                                    <div class="space-y-6">
                                        <div class="space-y-2">
                                            <label class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400 ml-1">Topic</label>
                                            <input v-model="editForm.topic" type="text" class="w-full px-5 py-3.5 bg-[#fbf7f1] dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 rounded-2xl focus:ring-2 focus:ring-[#c7a36c]/40 focus:border-[#c7a36c] outline-none transition-all dark:text-white font-medium" placeholder="What's this schedule about?" />
                                        </div>

                                        <div class="space-y-2">
                                            <label class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400 ml-1">Daily Time</label>
                                            <input v-model="editForm.scheduled_time" type="time" class="w-full px-5 py-3.5 bg-[#fbf7f1] dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 rounded-2xl focus:ring-2 focus:ring-[#c7a36c]/40 focus:border-[#c7a36c] outline-none transition-all dark:text-white font-medium" />
                                        </div>

                                        <div class="space-y-2">
                                            <label class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400 ml-1">YouTube Channel</label>
                                            <select v-model="editForm.youtube_token_id" class="w-full px-5 py-3.5 bg-[#fbf7f1] dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 rounded-2xl focus:ring-2 focus:ring-[#c7a36c]/40 focus:border-[#c7a36c] outline-none transition-all dark:text-white font-medium appearance-none">
                                                <option v-for="channel in channels" :key="channel.id" :value="channel.id">{{ channel.channel_title }}</option>
                                            </select>
                                        </div>

                                        <div class="grid grid-cols-2 gap-5">
                                            <div class="space-y-2">
                                                <label class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400 ml-1">Content Style</label>
                                                <select v-model="editForm.style" class="w-full px-5 py-3.5 bg-[#fbf7f1] dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 rounded-2xl focus:ring-2 focus:ring-[#c7a36c]/40 focus:border-[#c7a36c] outline-none transition-all dark:text-white font-medium">
                                                    <option value="story">Story</option>
                                                    <option value="science_short">Science Short</option>
                                                    <option value="hollywood_hype">Hollywood Hype</option>
                                                    <option value="bollywood_masala">Bollywood Masala</option>
                                                    <option value="trade_wave">Trade Wave</option>
                                                </select>
                                            </div>
                                            <div class="space-y-2">
                                                <label class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400 ml-1">Talking Style</label>
                                                <select v-model="editForm.talking_style" class="w-full px-5 py-3.5 bg-[#fbf7f1] dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 rounded-2xl focus:ring-2 focus:ring-[#c7a36c]/40 focus:border-[#c7a36c] outline-none transition-all dark:text-white font-medium">
                                                    <option value="none">None</option>
                                                    <option value="opinion">Opinion</option>
                                                    <option value="storytime">Storytime</option>
                                                    <option value="educational">Educational</option>
                                                    <option value="reaction">Reaction</option>
                                                    <option value="vlog">Vlog</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div class="space-y-2">
                                            <label class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#6a5d4d] dark:text-slate-400 ml-1">Aspect Ratio</label>
                                            <select v-model="editForm.aspect_ratio" class="w-full px-5 py-3.5 bg-[#fbf7f1] dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 rounded-2xl focus:ring-2 focus:ring-[#c7a36c]/40 focus:border-[#c7a36c] outline-none transition-all dark:text-white font-medium">
                                                <option value="16:9">Widescreen (16:9)</option>
                                                <option value="9:16">Shorts/Reels (9:16)</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="bg-[#f7f2e8] dark:bg-slate-900/80 px-8 py-6 flex flex-col sm:flex-row-reverse gap-4 border-t border-[#e6dccf] dark:border-slate-800">
                            <button type="button" @click="updateSchedule" :disabled="updating" class="w-full sm:w-auto inline-flex justify-center items-center rounded-full px-8 py-3.5 bg-[#0b1021] hover:bg-[#141a2f] text-[#f7f2e8] font-semibold transition-all disabled:opacity-50 shadow-[0_20px_40px_-25px_rgba(11,16,33,0.7)] active:scale-95">
                                <svg v-if="updating" class="animate-spin -ml-1 mr-2 h-5 w-5 text-[#f7f2e8]" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                {{ updating ? 'Saving Changes...' : 'Save Changes' }}
                            </button>
                            <button type="button" @click="showEditModal = false" class="w-full sm:w-auto inline-flex justify-center items-center rounded-full px-8 py-3.5 bg-white dark:bg-slate-800 border border-[#efe6d8] dark:border-slate-700 text-[#6a5d4d] dark:text-slate-300 font-semibold hover:border-[#c7a36c] transition-all active:scale-95">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>
    </AppLayout>
</template>
