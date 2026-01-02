<script setup>
import { ref, onMounted } from 'vue';
import { Head } from '@inertiajs/vue3';
import AppLayout from '@/Layouts/AppLayout.vue';
import axios from 'axios';
import { useToast } from 'vue-toast-notification';
import Swal from 'sweetalert2';

const toast = useToast();
const schedules = ref([]);
const channels = ref([]);
const loading = ref(false);
const showModal = ref(false);
const editingSchedule = ref(null);
const showTimePicker = ref(false);
const newTime = ref('');
// Using a computed or simple ref for dark mode check for Swal
const isDark = ref(document.documentElement.classList.contains('dark'));

const formData = ref({
    name: '',
    style: 'science_short',
    aspect_ratio: '9:16',
    videos_per_day: 5,
    timezone: 'UTC',
    upload_times: ['02:00'],
    youtube_token_id: null,
    prompt_template: '',
    is_active: true,
});

const timezones = [
    'UTC',
    'Asia/Dhaka',
    'America/New_York',
    'America/Los_Angeles',
    'America/Chicago',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Asia/Tokyo',
    'Asia/Dubai',
    'Asia/Kolkata',
    'Asia/Singapore',
    'Asia/Hong_Kong',
    'Australia/Sydney'
];

const styles = [
    { id: 'story', name: 'General Story', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
    { id: 'science_short', name: '60s Lab', icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.691.34a2 2 0 01-1.782 0l-.691-.34a6 6 0 00-3.86-.517l-2.387.477a2 2 0 00-1.022.547V18a2 2 0 002 2h12a2 2 0 002-2v-2.572zM12 11V3.5' },
    { id: 'hollywood_hype', name: 'Hollywood', icon: 'M7 4V20M17 4V20M3 8H7M17 8H21M3 12H21M3 16H7M17 16H21M4 20H20' },
    { id: 'trade_wave', name: 'TradeWave', icon: 'M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z' },
];

const fetchSchedules = async () => {
    try {
        const response = await axios.get('/api/schedules');
        schedules.value = response.data;
    } catch (error) {
        console.error('Error fetching schedules:', error);
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

const openModal = (schedule = null) => {
    if (schedule && schedule.id) {
        editingSchedule.value = schedule;
        formData.value = {
            ...schedule,
            upload_times: schedule.upload_times || []
        };
    } else {
        editingSchedule.value = null;
        formData.value = {
            name: '',
            style: 'science_short',
            aspect_ratio: '9:16',
            videos_per_day: 5,
            timezone: 'UTC',
            upload_times: ['02:00'],
            youtube_token_id: null,
            prompt_template: '',
            is_active: true,
        };
    }
    showModal.value = true;
};

const closeModal = () => {
    showModal.value = false;
    editingSchedule.value = null;
};

const addUploadTime = () => {
    showTimePicker.value = true;
};

const confirmAddTime = () => {
    if (newTime.value && /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/.test(newTime.value)) {
        formData.value.upload_times.push(newTime.value);
        formData.value.upload_times.sort();
        newTime.value = '';
        showTimePicker.value = false;
        toast.success('Upload time added');
    } else {
        toast.error('Invalid time format. Use HH:MM (e.g., 02:00)');
    }
};

const quickAddTime = (hour) => {
    const time = `${hour.toString().padStart(2, '0')}:00`;
    if (!formData.value.upload_times.includes(time)) {
        formData.value.upload_times.push(time);
        formData.value.upload_times.sort();
        toast.success(`Added ${time}`);
    } else {
        toast.info(`${time} already added`);
    }
};

const suggestedTimes = [
    { label: 'Early Morning (6 AM)', time: '06:00' },
    { label: 'Morning (9 AM)', time: '09:00' },
    { label: 'Noon (12 PM)', time: '12:00' },
    { label: 'Afternoon (3 PM)', time: '15:00' },
    { label: 'Evening (6 PM)', time: '18:00' },
    { label: 'Night (9 PM)', time: '21:00' },
    { label: 'Late Night (12 AM)', time: '00:00' },
    { label: '2 AM', time: '02:00' },
];

const removeUploadTime = (index) => {
    formData.value.upload_times.splice(index, 1);
};

const saveSchedule = async () => {
    if (!formData.value.name) {
        toast.error('Please enter a schedule name');
        return;
    }
    if (formData.value.upload_times.length === 0) {
        toast.error('Please add at least one upload time');
        return;
    }

    loading.value = true;
    try {
        if (editingSchedule.value) {
            await axios.put(`/api/schedules/${editingSchedule.value.id}`, formData.value);
            toast.success('Schedule updated successfully!');
        } else {
            await axios.post('/api/schedules', formData.value);
            toast.success('Schedule created successfully!');
        }
        closeModal();
        fetchSchedules();
    } catch (error) {
        console.error('Error saving schedule:', error);

        if (error.response?.data?.errors) {
            const errors = error.response.data.errors;
            const firstError = Object.values(errors)[0][0];
            toast.error(firstError || 'Failed to save schedule');
        } else if (error.response?.data?.message) {
            toast.error(error.response.data.message);
        } else {
            toast.error('Failed to save schedule. Please try again.');
        }
    } finally {
        loading.value = false;
    }
};

const deleteSchedule = async (schedule) => {
    const result = await Swal.fire({
        title: 'Are you sure?',
        text: 'This will stop the automatic video generation for this schedule.',
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
        await axios.delete(`/api/schedules/${schedule.id}`);
        toast.success('Schedule deleted');
        fetchSchedules();
    } catch (error) {
        console.error('Error deleting schedule:', error);

        if (error.response?.status === 404) {
            toast.error('Schedule not found. It may have been deleted already.');
            fetchSchedules();
        } else if (error.response?.data?.message) {
            toast.error(error.response.data.message);
        } else {
            toast.error('Failed to delete schedule');
        }
    }
};

const toggleSchedule = async (schedule) => {
    try {
        await axios.patch(`/api/schedules/${schedule.id}`, {
            is_active: !schedule.is_active
        });
        schedule.is_active = !schedule.is_active;
        toast.success(schedule.is_active ? 'Schedule activated' : 'Schedule deactivated');
    } catch (error) {
        console.error('Error toggling schedule:', error);
        toast.error('Failed to update schedule');
    }
};

const generateNow = async (schedule) => {
    try {
        await axios.post(`/api/schedules/${schedule.id}/generate`);
        toast.success('Video generation started!');
    } catch (error) {
        console.error('Error generating video:', error);
        toast.error('Failed to generate video');
    }
};

onMounted(() => {
    fetchSchedules();
    fetchChannels();
});
</script>

<template>
    <AppLayout>
        <Head title="Schedules" />

        <template #header>
            Schedules
        </template>

        <template #actions>
            <button @click="openModal" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg transition-all shadow-sm flex items-center gap-2 text-sm">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                New Schedule
            </button>
        </template>

        <div class="mb-8">
            <h1 class="text-3xl font-bold text-slate-900 dark:text-white mb-2">Auto-Upload Scheduler</h1>
            <p class="text-slate-600 dark:text-slate-400">Set up automatic video generation and upload schedules for your channels</p>
        </div>

        <div v-if="schedules.length === 0" class="text-center py-20 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
            <svg class="w-16 h-16 mx-auto text-slate-300 dark:text-slate-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <h3 class="text-lg font-bold text-slate-700 dark:text-slate-300 mb-2">No schedules yet</h3>
            <p class="text-slate-500 dark:text-slate-400 mb-4">Create your first automated video schedule</p>
            <button @click="openModal" class="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg">Create Schedule</button>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div v-for="schedule in schedules" :key="schedule.id"
                    class="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden"
                    :class="{'opacity-75': !schedule.is_active}">
                <div class="p-6">
                    <div class="flex items-start justify-between mb-4">
                        <div class="flex-1">
                            <h3 class="text-lg font-bold text-slate-900 dark:text-white">{{ schedule.name }}</h3>
                            <p class="text-sm text-slate-500 dark:text-slate-400 capitalize">{{ schedule.style.replace('_', ' ') }}</p>
                        </div>
                        <div class="flex items-center space-x-2">
                            <button @click="generateNow(schedule)" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400" title="Generate Now">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            </button>
                            <button @click="toggleSchedule(schedule)" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" :class="schedule.is_active ? 'text-green-600' : 'text-slate-400'" title="Toggle">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                            </button>
                            <button @click="openModal(schedule)" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400" title="Edit">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                            </button>
                            <button @click="deleteSchedule(schedule)" class="p-2 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600" title="Delete">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                            </button>
                        </div>
                    </div>

                    <div class="space-y-3">
                        <div class="flex items-center justify-between text-sm">
                            <span class="text-slate-600 dark:text-slate-400">Videos per day</span>
                            <span class="font-bold text-slate-900 dark:text-white">{{ schedule.videos_per_day }}</span>
                        </div>
                        <div class="flex items-center justify-between text-sm">
                            <span class="text-slate-600 dark:text-slate-400">Format</span>
                            <span class="font-bold text-slate-900 dark:text-white">{{ schedule.aspect_ratio === '16:9' ? 'Landscape' : 'Shorts' }}</span>
                        </div>
                        <div class="flex items-center justify-between text-sm">
                            <span class="text-slate-600 dark:text-slate-400">Timezone</span>
                            <span class="font-bold text-slate-900 dark:text-white">{{ schedule.timezone }}</span>
                        </div>
                        <div class="text-sm">
                            <span class="text-slate-600 dark:text-slate-400">Upload times</span>
                            <div class="flex flex-wrap gap-2 mt-2">
                                <span v-for="time in (schedule.upload_times || [])" :key="time" class="px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded text-xs font-mono font-bold">{{ time }}</span>
                            </div>
                        </div>
                        <div v-if="schedule.youtube_channel" class="flex items-center gap-2 text-sm">
                            <img :src="schedule.youtube_channel.channel_thumbnail" class="w-6 h-6 rounded-full">
                            <span class="text-slate-700 dark:text-slate-300">{{ schedule.youtube_channel.channel_title }}</span>
                        </div>
                    </div>
                </div>
                <div class="px-6 py-3 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-800">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-semibold" :class="schedule.is_active ? 'text-green-600' : 'text-slate-500'">
                            {{ schedule.is_active ? '● Active' : '○ Paused' }}
                        </span>
                        <span class="text-xs text-slate-500">
                            {{ Math.ceil(schedule.videos_per_day / (schedule.upload_times?.length || 1)) }} videos × {{ schedule.upload_times?.length || 0 }} times
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="closeModal">
            <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                <div class="p-6 border-b border-slate-200 dark:border-slate-800">
                    <h2 class="text-xl font-bold text-slate-900 dark:text-white">{{ editingSchedule ? 'Edit Schedule' : 'Create New Schedule' }}</h2>
                </div>
                <div class="p-6 space-y-6">
                    <div>
                        <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Schedule Name</label>
                        <input v-model="formData.name" type="text" class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white" placeholder="e.g., Daily Science Shorts">
                    </div>

                    <div>
                        <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Content Style</label>
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                            <div v-for="style in styles" :key="style.id"
                                 @click="formData.style = style.id"
                                 :class="['cursor-pointer p-3 rounded-xl border-2 text-center',
                                          formData.style === style.id ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/20' : 'border-slate-200 dark:border-slate-700 hover:border-slate-300']">
                                <div class="text-xs font-bold uppercase text-slate-700 dark:text-slate-300">{{ style.name }}</div>
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Format</label>
                            <div class="flex p-1 bg-slate-100 dark:bg-slate-800 rounded-xl">
                                <button v-for="ratio in ['16:9', '9:16']" :key="ratio"
                                        @click="formData.aspect_ratio = ratio"
                                        :class="['flex-1 py-2 text-sm font-bold rounded-lg',
                                                 formData.aspect_ratio === ratio ? 'bg-white dark:bg-slate-700 text-indigo-600' : 'text-slate-500']">
                                    {{ ratio === '16:9' ? 'Landscape' : 'Shorts' }}
                                </button>
                            </div>
                        </div>
                        <div>
                            <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Videos per Day</label>
                            <input v-model.number="formData.videos_per_day" type="number" min="1" max="50" class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white">
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Timezone</label>
                        <select v-model="formData.timezone" class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white">
                            <option v-for="tz in timezones" :key="tz" :value="tz">{{ tz }}</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Upload Times</label>

                        <div class="flex flex-wrap gap-2 mb-3">
                            <span v-for="(time, index) in formData.upload_times" :key="index" class="px-3 py-2 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-lg flex items-center space-x-2">
                                <span class="font-mono font-bold">{{ time }}</span>
                                <button @click="removeUploadTime(index)" class="text-indigo-800 dark:text-indigo-300 hover:text-red-600 font-bold">&times;</button>
                            </span>
                        </div>

                        <div class="space-y-3">
                            <div class="p-4 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                                <label class="text-xs font-bold text-slate-600 dark:text-slate-400 uppercase mb-2 block">Quick Add Common Times</label>
                                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                                    <button v-for="suggested in suggestedTimes" :key="suggested.time"
                                            @click="quickAddTime(parseInt(suggested.time.split(':')[0]))"
                                            :disabled="formData.upload_times.includes(suggested.time)"
                                            class="px-3 py-2 text-xs font-semibold rounded-lg transition-all border disabled:opacity-50 disabled:cursor-not-allowed"
                                            :class="formData.upload_times.includes(suggested.time)
                                                ? 'bg-indigo-100 dark:bg-indigo-900/30 border-indigo-300 dark:border-indigo-700 text-indigo-600 dark:text-indigo-400'
                                                : 'bg-white dark:bg-slate-700 border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:border-indigo-500 hover:text-indigo-600'">
                                        {{ suggested.time }}
                                    </button>
                                </div>
                            </div>

                            <div class="p-4 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                                <label class="text-xs font-bold text-slate-600 dark:text-slate-400 uppercase mb-2 block">Custom Time</label>
                                <div class="flex gap-2">
                                    <input v-model="newTime" type="time" class="flex-1 px-3 py-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white text-sm">
                                    <button @click="confirmAddTime" :disabled="!newTime || formData.upload_times.includes(newTime)"
                                            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                                        Add
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Upload Destination</label>
                        <div class="space-y-3">
                            <div v-if="channels.length > 0">
                                <label class="text-xs text-slate-500 font-bold uppercase">YouTube Channel</label>
                                <div class="grid grid-cols-2 gap-2">
                                    <div v-for="channel in channels" :key="channel.id"
                                         @click="formData.youtube_token_id = channel.id"
                                         :class="['flex items-center p-3 border rounded-xl cursor-pointer',
                                                  formData.youtube_token_id === channel.id ? 'border-red-500 bg-red-50 dark:bg-red-900/20' : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700']">
                                        <img :src="channel.channel_thumbnail" class="w-8 h-8 rounded-full mr-3">
                                        <span class="text-xs font-bold truncate dark:text-slate-200">{{ channel.channel_title }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Prompt Template (Optional)</label>
                        <textarea v-model="formData.prompt_template" rows="2" class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white" placeholder="Custom prompt for AI story generation..."></textarea>
                    </div>
                </div>
                <div class="p-6 border-t border-slate-200 dark:border-slate-800 flex justify-end space-x-3">
                    <button @click="closeModal" class="px-6 py-2 rounded-xl font-bold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">Cancel</button>
                    <button @click="saveSchedule" :disabled="loading" class="px-6 py-2 rounded-xl font-bold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors disabled:opacity-50">
                        {{ editingSchedule ? 'Update' : 'Create' }} Schedule
                    </button>
                </div>
            </div>
        </div>
    </AppLayout>
</template>

<style>
@keyframes pulse-slow {
    0%, 100% {
        box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4);
    }
    50% {
        box-shadow: 0 0 0 10px rgba(99, 102, 241, 0);
    }
}

.animate-pulse-slow {
    animation: pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
