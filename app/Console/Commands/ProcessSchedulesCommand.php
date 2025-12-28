<?php

namespace App\Console\Commands;

use App\Models\Schedule;
use App\Models\Story;
use App\Jobs\ProcessStoryJob;
use App\Services\AiStoryService;
use Carbon\Carbon;
use Illuminate\Console\Command;

class ProcessSchedulesCommand extends Command
{
    protected $signature = 'schedules:process';

    protected $description = 'Process schedules and generate videos based on upload times';

    public function handle()
    {
        $now = Carbon::now();
        $currentTime = $now->format('H:i');
        $currentDate = $now->format('Y-m-d');

        $schedules = Schedule::where('is_active', true)->get();

        foreach ($schedules as $schedule) {
            $scheduleTime = Carbon::now()->setTimezone($schedule->timezone)->format('H:i');

            if (!in_array($scheduleTime, $schedule->upload_times)) {
                continue;
            }

            $uploadTimesCount = count($schedule->upload_times);
            $videosPerTime = ceil($schedule->videos_per_day / $uploadTimesCount);

            $timeSlotIndex = array_search($scheduleTime, $schedule->upload_times);
            $lastGenerated = $schedule->last_generated_dates ?? [];
            $todayKey = $schedule->timezone . '_' . $currentDate . '_slot_' . $timeSlotIndex;

            if (isset($lastGenerated[$todayKey]) && count($lastGenerated[$todayKey]) >= $videosPerTime) {
                $this->info("Schedule {$schedule->name} time slot {$scheduleTime} already generated {$videosPerTime} videos");
                continue;
            }

            $generatedThisSlot = $lastGenerated[$todayKey] ?? [];
            $toGenerate = $videosPerTime - count($generatedThisSlot);

            $this->info("Schedule {$schedule->name} at {$scheduleTime}: Generating {$toGenerate} videos (slot {$timeSlotIndex}/{$uploadTimesCount}, {$videosPerTime} videos per time)");

            for ($i = 0; $i < $toGenerate; $i++) {
                try {
                    $aiService = app(AiStoryService::class);
                    $topic = $schedule->prompt_template ?? null;
                    $storyData = $aiService->generateStory($topic, $schedule->style);

                    $story = Story::create([
                        'user_id' => $schedule->user_id,
                        'title' => $storyData['title'],
                        'content' => $storyData['content'],
                        'style' => $schedule->style,
                        'aspect_ratio' => $schedule->aspect_ratio,
                        'status' => 'pending',
                        'youtube_title' => $storyData['youtube_title'],
                        'youtube_description' => $storyData['youtube_description'],
                        'youtube_tags' => $storyData['youtube_tags'],
                        'youtube_token_id' => $schedule->youtube_token_id,
                        'facebook_page_id' => $schedule->facebook_page_id,
                        'is_from_scheduler' => true,
                    ]);

                    ProcessStoryJob::dispatch($story);

                    $this->info("Created story #{$story->id} with full metadata");
                } catch (\Exception $e) {
                    $this->error("Failed to generate story: " . $e->getMessage());
                    continue;
                }

                $generatedThisSlot[] = $story->id;
            }

            $lastGenerated[$todayKey] = $generatedThisSlot;
            $schedule->update(['last_generated_dates' => $lastGenerated]);
        }

        return 0;
    }
}
