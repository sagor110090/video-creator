<?php

namespace App\Console\Commands;

use App\Models\VideoSchedule;
use App\Models\Story;
use App\Jobs\ProcessStoryJob;
use App\Services\AiStoryService;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Log;

class ProcessVideoSchedulesCommand extends Command
{
    protected $signature = 'video-schedules:process';
    protected $description = 'Process due video schedules and start generation';

    public function handle(AiStoryService $aiService)
    {
        $this->info('Checking for due recurring video schedules...');

        $now = now();
        $currentTime = $now->format('H:i');
        $today = $now->toDateString();

        // Find schedules that:
        // 1. Are NOT already run today (last_run_at != today)
        // 2. Their scheduled_time is <= current time
        $schedules = VideoSchedule::where(function($query) use ($today) {
                $query->whereNull('last_run_at')
                      ->orWhere('last_run_at', '<', $today);
            })
            ->where('scheduled_time', '<=', $currentTime)
            ->get();

        if ($schedules->isEmpty()) {
            $this->info('No schedules due at this time.');
            return;
        }

        foreach ($schedules as $schedule) {
            $this->info("Processing recurring schedule ID: {$schedule->id} for topic: {$schedule->topic} (Time: {$schedule->scheduled_time})");

            try {
                // Mark as run for today immediately to prevent double processing
                $schedule->update([
                    'status' => 'processing',
                    'last_run_at' => $today
                ]);

                // 1. Generate Story Content using AI
                $topic = $schedule->topic;

                // If the style is news-based, search for latest news first
                $newsBasedStyles = ['hollywood_hype', 'bollywood_masala', 'trade_wave'];
                if (in_array($schedule->style, $newsBasedStyles)) {
                    $this->info("Searching for latest news for: {$schedule->topic}...");
                    try {
                        $newsItems = $aiService->searchNews($schedule->topic, $schedule->style);
                        if (!empty($newsItems)) {
                            // Pick the first/best news item
                            $news = $newsItems[0];
                            // Enrich the topic with the actual news content
                            $topic = "Create a video about this news: {$news['title']}. Details: {$news['snippet']}";
                            $this->info("Found news: {$news['title']}");
                        } else {
                            $this->warn("No news found for {$schedule->topic}, falling back to generic generation.");
                        }
                    } catch (\Exception $e) {
                        $this->error("News search failed: " . $e->getMessage());
                        // Fallback to original topic
                    }
                }

                $this->info("Generating story content for: {$topic}");
                $aiResponse = $aiService->generateStory(
                    $topic ?: 'a random interesting story',
                    $schedule->style,
                    $schedule->aspect_ratio,
                    $schedule->talking_style ?? 'none'
                );

                // 2. Create Story record
                $story = Story::create([
                    'title' => $aiResponse['title'] ?? $schedule->topic,
                    'content' => $aiResponse['content'],
                    'style' => $schedule->style,
                    'talking_style' => $schedule->talking_style ?? 'none',
                    'aspect_ratio' => $schedule->aspect_ratio,
                    'status' => 'pending',
                    'youtube_token_id' => $schedule->youtube_token_id,
                    'youtube_title' => $aiResponse['youtube_title'] ?? $aiResponse['title'],
                    'youtube_description' => $aiResponse['youtube_description'] ?? $aiResponse['content'],
                    'youtube_tags' => $aiResponse['youtube_tags'] ?? 'ai, story, animation',
                    'video_schedule_id' => $schedule->id,
                    'scheduled_for' => $now, // Record when this was scheduled for
                ]);

                $schedule->update([
                    'status' => 'completed',
                    'story_id' => $story->id
                ]);

                // 3. Dispatch processing job
                ProcessStoryJob::dispatch($story);

                $this->info("Successfully started generation for Story ID: {$story->id}");

            } catch (\Exception $e) {
                Log::error("Failed to process schedule ID: {$schedule->id}: " . $e->getMessage());
                $schedule->update([
                    'status' => 'failed',
                    'last_error' => $e->getMessage()
                ]);
                $this->error("Failed to process schedule ID: {$schedule->id}");
            }
        }

        $this->info('Finished processing schedules.');
    }
}
