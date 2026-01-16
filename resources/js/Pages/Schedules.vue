<script setup>
import AppLayout from '@/Layouts/AppLayout.vue';
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { Head } from '@inertiajs/vue3';

const schedules = ref({ data: [] });
const channels = ref([]);
const loading = ref(false);
const creating = ref(false);
const updating = ref(false);
const showEditModal = ref(false);
const editingSchedule = ref(null);

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
        alert(error.response?.data?.message || 'Failed to create schedule');
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
        alert(error.response?.data?.message || 'Failed to update schedule');
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
    if (!confirm('Are you sure you want to delete this schedule?')) return;
    try {
        await axios.delete(`/api/schedules/${id}`);
        fetchSchedules();
    } catch (error) {
        console.error('Error deleting schedule:', error);
    }
};

const getStatusColor = (status) => {
    switch (status) {
        case 'pending': return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
        case 'processing': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
        case 'completed': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
        case 'failed': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
        default: return 'bg-slate-100 text-slate-700';
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
    fetchSchedules();
    fetchChannels();
});
</script>

<template>
    <Head title="Video Schedules" />

    <AppLayout>
        <template #header>Video Schedules</template>

        <div class="max-w-7xl mx-auto space-y-6">
            <!-- Create Schedule Form -->
            <div class="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-6">
                <h3 class="text-lg font-bold text-slate-900 dark:text-white mb-4">Create New Schedule</h3>
                <form @submit.prevent="createSchedule" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div class="space-y-1">
                        <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Topic</label>
                        <input
                            v-model="newSchedule.topic"
                            type="text"
                            placeholder="e.g. History of Rome"
                            required
                            class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition-all dark:text-white"
                        />
                    </div>

                    <div class="space-y-1">
                        <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Daily Time</label>
                        <input
                            v-model="newSchedule.scheduled_time"
                            type="time"
                            required
                            class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition-all dark:text-white"
                        />
                    </div>

                    <div class="space-y-1">
                        <label class="text-sm font-medium text-slate-700 dark:text-slate-300">YouTube Channel</label>
                        <select
                            v-model="newSchedule.youtube_token_id"
                            class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition-all dark:text-white"
                        >
                            <option v-for="channel in channels" :key="channel.id" :value="channel.id">
                                {{ channel.channel_title }}
                            </option>
                        </select>
                    </div>

                    <div class="space-y-1">
                        <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Content Style</label>
                        <select
                            v-model="newSchedule.style"
                            class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition-all dark:text-white"
                        >
                            <option value="story">Story</option>
                            <option value="science_short">Science Short</option>
                            <option value="hollywood_hype">Hollywood Hype</option>
                            <option value="bollywood_masala">Bollywood Masala</option>
                            <option value="trade_wave">Trade Wave</option>
                        </select>
                    </div>

                    <div class="space-y-1">
                        <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Talking Style</label>
                        <select
                            v-model="newSchedule.talking_style"
                            class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition-all dark:text-white"
                        >
                            <option value="none">None (Default)</option>
                            <option value="opinion">Opinion</option>
                            <option value="storytime">Storytime</option>
                            <option value="educational">Educational</option>
                            <option value="reaction">Reaction</option>
                            <option value="vlog">Vlog</option>
                        </select>
                    </div>

                    <div class="space-y-1">
                        <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Aspect Ratio</label>
                        <select
                            v-model="newSchedule.aspect_ratio"
                            class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition-all dark:text-white"
                        >
                            <option value="16:9">Widescreen (16:9)</option>
                            <option value="9:16">Shorts/Reels (9:16)</option>
                        </select>
                    </div>

                    <div class="flex items-end">
                        <button
                            type="submit"
                            :disabled="creating"
                            class="w-full px-6 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-bold rounded-lg transition-all flex items-center justify-center"
                        >
                            <svg v-if="creating" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            {{ creating ? 'Creating...' : 'Add Schedule' }}
                        </button>
                    </div>
                </form>
            </div>

            <!-- Schedules List -->
            <div class="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
                <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                    <h3 class="font-bold text-slate-900 dark:text-white">Active Schedules</h3>
                    <button @click="fetchSchedules()" class="p-2 text-slate-500 hover:text-indigo-600 transition-colors">
                        <svg class="w-5 h-5" :class="{'animate-spin': loading}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                    </button>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left">
                        <thead>
                            <tr class="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider">
                                <th class="px-6 py-3 font-medium">Topic</th>
                                <th class="px-6 py-3 font-medium">Channel</th>
                                <th class="px-6 py-3 font-medium">Daily Time</th>
                                <th class="px-6 py-3 font-medium">Last Run</th>
                                <th class="px-6 py-3 font-medium">Status</th>
                                <th class="px-6 py-3 font-medium text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-200 dark:divide-slate-800">
                            <tr v-if="schedules.data.length === 0" class="text-center py-10">
                                <td colspan="5" class="px-6 py-10 text-slate-500 dark:text-slate-400">
                                    No schedules found. Create one above!
                                </td>
                            </tr>
                            <tr v-for="schedule in schedules.data" :key="schedule.id" class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                <td class="px-6 py-4">
                                    <div class="text-sm font-medium text-slate-900 dark:text-white">{{ schedule.topic }}</div>
                                    <div class="text-xs text-slate-500">{{ schedule.style }} • {{ schedule.aspect_ratio }}</div>
                                </td>
                                <td class="px-6 py-4">
                                    <div v-if="schedule.youtube_token" class="flex items-center">
                                        <img :src="schedule.youtube_token.channel_thumbnail" class="w-6 h-6 rounded-full mr-2" />
                                        <span class="text-sm text-slate-600 dark:text-slate-300">{{ schedule.youtube_token.channel_title }}</span>
                                    </div>
                                    <span v-else class="text-xs text-slate-400">No channel</span>
                                </td>
                                <td class="px-6 py-4 text-sm font-bold text-indigo-600 dark:text-indigo-400">
                                    {{ formatTime(schedule.scheduled_time) }}
                                </td>
                                <td class="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                                    {{ formatDate(schedule.last_run_at) }}
                                </td>
                                <td class="px-6 py-4">
                                    <span :class="['px-2.5 py-0.5 rounded-full text-xs font-medium', getStatusColor(schedule.status)]">
                                        {{ schedule.status }}
                                    </span>
                                    <div v-if="schedule.last_error" class="text-[10px] text-red-500 mt-1 max-w-[150px] truncate" :title="schedule.last_error">
                                        {{ schedule.last_error }}
                                    </div>
                                </td>
                                <td class="px-6 py-4 text-right">
                                    <div class="flex items-center justify-end space-x-2">
                                        <button
                                            @click="copySchedule(schedule)"
                                            class="p-2 text-slate-400 hover:text-indigo-600 transition-colors"
                                            title="Copy Schedule"
                                        >
                                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                                            </svg>
                                        </button>
                                        <button
                                            @click="openEditModal(schedule)"
                                            class="p-2 text-slate-400 hover:text-blue-600 transition-colors"
                                            title="Edit Schedule"
                                        >
                                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                            </svg>
                                        </button>
                                        <button
                                            @click="deleteSchedule(schedule.id)"
                                            class="p-2 text-slate-400 hover:text-red-600 transition-colors"
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
                <div v-if="schedules.links && schedules.links.length > 3" class="px-6 py-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-800 flex justify-center">
                    <nav class="flex space-x-1">
                        <button
                            v-for="link in schedules.links"
                            :key="link.label"
                            @click="fetchSchedules(link.url ? new URL(link.url).searchParams.get('page') : 1)"
                            :disabled="!link.url"
                            v-html="link.label"
                            :class="[
                                'px-3 py-1 rounded text-sm transition-colors',
                                link.active ? 'bg-indigo-600 text-white' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
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
                    <!-- Backdrop -->
                    <div class="fixed inset-0 bg-slate-900/70 backdrop-blur-md transition-opacity" aria-hidden="true" @click="showEditModal = false"></div>

                    <!-- Centering trick -->
                    <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                    <!-- Modal Content -->
                    <div class="relative inline-block align-bottom bg-white dark:bg-slate-900 rounded-3xl text-left overflow-hidden shadow-[0_20px_70px_-10px_rgba(0,0,0,0.5)] transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full border border-slate-200/50 dark:border-slate-800/50 z-50">
                        <div class="bg-white dark:bg-slate-900 px-6 pt-6 pb-6">
                            <div class="sm:flex sm:items-start">
                                <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                                    <div class="flex items-center justify-between mb-8">
                                        <h3 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight" id="modal-title">
                                            Edit Schedule
                                        </h3>
                                        <button @click="showEditModal = false" class="p-2 -mr-2 text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 transition-all rounded-full hover:bg-slate-100 dark:hover:bg-slate-800">
                                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
                                            </svg>
                                        </button>
                                    </div>

                                    <div class="space-y-6">
                                        <div class="space-y-2">
                                            <label class="text-sm font-bold text-slate-700 dark:text-slate-300 ml-1">Topic</label>
                                            <input v-model="editForm.topic" type="text" class="w-full px-5 py-3.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white font-medium" placeholder="What's this schedule about?" />
                                        </div>

                                        <div class="space-y-2">
                                            <label class="text-sm font-bold text-slate-700 dark:text-slate-300 ml-1">Daily Time</label>
                                            <input v-model="editForm.scheduled_time" type="time" class="w-full px-5 py-3.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white font-medium" />
                                        </div>

                                        <div class="space-y-2">
                                            <label class="text-sm font-bold text-slate-700 dark:text-slate-300 ml-1">YouTube Channel</label>
                                            <select v-model="editForm.youtube_token_id" class="w-full px-5 py-3.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white font-medium appearance-none">
                                                <option v-for="channel in channels" :key="channel.id" :value="channel.id">{{ channel.channel_title }}</option>
                                            </select>
                                        </div>

                                        <div class="grid grid-cols-2 gap-5">
                                            <div class="space-y-2">
                                                <label class="text-sm font-bold text-slate-700 dark:text-slate-300 ml-1">Content Style</label>
                                                <select v-model="editForm.style" class="w-full px-5 py-3.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white font-medium">
                                                    <option value="story">Story</option>
                                                    <option value="science_short">Science Short</option>
                                                    <option value="hollywood_hype">Hollywood Hype</option>
                                                    <option value="bollywood_masala">Bollywood Masala</option>
                                                    <option value="trade_wave">Trade Wave</option>
                                                </select>
                                            </div>
                                            <div class="space-y-2">
                                                <label class="text-sm font-bold text-slate-700 dark:text-slate-300 ml-1">Talking Style</label>
                                                <select v-model="editForm.talking_style" class="w-full px-5 py-3.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white font-medium">
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
                                            <label class="text-sm font-bold text-slate-700 dark:text-slate-300 ml-1">Aspect Ratio</label>
                                            <select v-model="editForm.aspect_ratio" class="w-full px-5 py-3.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white font-medium">
                                                <option value="16:9">Widescreen (16:9)</option>
                                                <option value="9:16">Shorts/Reels (9:16)</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="bg-slate-50/50 dark:bg-slate-800/30 px-8 py-6 flex flex-col sm:flex-row-reverse gap-4 border-t border-slate-100 dark:border-slate-800/50">
                            <button type="button" @click="updateSchedule" :disabled="updating" class="w-full sm:w-auto inline-flex justify-center items-center rounded-2xl px-8 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-black transition-all disabled:opacity-50 shadow-xl shadow-indigo-500/20 active:scale-95">
                                <svg v-if="updating" class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                {{ updating ? 'Saving Changes...' : 'Save Changes' }}
                            </button>
                            <button type="button" @click="showEditModal = false" class="w-full sm:w-auto inline-flex justify-center items-center rounded-2xl px-8 py-3.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-bold hover:bg-slate-100 dark:hover:bg-slate-700 transition-all active:scale-95">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>
    </AppLayout>
</template>
