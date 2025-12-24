<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\Story;
use App\Services\AiStoryService;
use App\Services\YouTubeService;
use App\Jobs\ProcessStoryJob;
use App\Jobs\UploadToYouTubeJob;
use Illuminate\Support\Facades\Log;

class CreateAndUploadStoryCommand extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'story:create-and-upload {topic? : The topic of the story} {--aspect=9:16 : Aspect ratio (9:16 or 16:9)} {--style=story : The style of content (story or science_short)}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Automates story generation, video creation, and YouTube upload';

    /**
     * Execute the console command.
     */
    public function handle(AiStoryService $aiService, YouTubeService $youtubeService)
    {
        $topic = $this->argument('topic');
        $aspectRatio = $this->option('aspect');
        $style = $this->option('style');

        $this->info("🚀 Starting automated workflow...");
        if ($topic) {
            $this->comment("Topic: {$topic}");
        }
        $this->comment("Aspect Ratio: {$aspectRatio}");
        $this->comment("Style: {$style}");

        // STEP 1: Generate Content via AI
        $this->info("🤖 Generating story content and metadata via AI...");
        try {
            $storyData = $aiService->generateStory($topic, $style);
            $this->info("✅ Content generated: " . $storyData['title']);
        } catch (\Exception $e) {
            $this->error("❌ AI Generation failed: " . $e->getMessage());
            return 1;
        }

        // STEP 2: Create Story Record
        $this->info("📝 Creating database record...");
        $story = Story::create([
            'title' => $storyData['title'],
            'content' => $storyData['content'],
            'status' => 'pending',
            'aspect_ratio' => $aspectRatio,
            'youtube_title' => $storyData['youtube_title'],
            'youtube_description' => $storyData['youtube_description'],
            'youtube_tags' => $storyData['youtube_tags'],
        ]);
        $this->info("✅ Story ID: {$story->id}");

        // STEP 3: Trigger Video Generation
        $this->info("🎬 Dispatching video generation job...");
        ProcessStoryJob::dispatch($story);

        $this->info("⏳ Waiting for video generation to complete (this may take up to 20-30 minutes for long stories)...");

        $completed = false;
        $timeout = 1800; // 30 minutes timeout
        $elapsed = 0;

        $bar = $this->output->createProgressBar(100);
        $bar->start();

        while (!$completed && $elapsed < $timeout) {
            sleep(5);
            $elapsed += 5;
            $story->refresh();

            if ($story->status === 'completed') {
                $completed = true;
                $bar->setProgress(100);
                $bar->finish();
                $this->newLine();
                $this->info("✅ Video generation completed!");
            } elseif ($story->status === 'failed') {
                $bar->finish();
                $this->newLine();
                $this->error("❌ Video generation failed.");
                return 1;
            } else {
                // If we can get scene progress, use it
                $totalScenes = $story->scenes()->count();
                if ($totalScenes > 0) {
                    // Count scenes that have an image_path or audio_path (if worker updates them)
                    // Currently worker doesn't update them, so we'll fallback to time-based estimation
                    // but with a slower increment as it nears 95%
                    $progress = min(98, ($elapsed / ($timeout / 2)) * 100);
                    if ($progress > 90) {
                        // Slow down as we approach the end
                        $progress = 90 + (($progress - 90) / 5);
                    }
                    $bar->setProgress($progress);
                } else {
                    $bar->setProgress(min(10, ($elapsed / 60) * 10)); // First 10% for parsing
                }
            }
        }

        if (!$completed) {
            $this->error("❌ Timeout waiting for video generation.");
            return 1;
        }

        // STEP 4: Upload to YouTube
        $this->info("📺 Starting YouTube upload...");
        try {
            // We use the service directly here to provide console feedback,
            // but we could also use the job. Using the service gives more immediate output.
            $this->comment("Uploading: " . ($story->youtube_title ?: $story->title));

            // Re-check token before upload
            $this->info("Checking YouTube authentication...");

            $videoId = $youtubeService->uploadVideo($story);

            $this->info("🎉 SUCCESS! Video uploaded to YouTube.");
            $this->info("🔗 URL: https://youtube.com/watch?v={$videoId}");

            return 0;
        } catch (\Exception $e) {
            $this->error("❌ YouTube upload failed: " . $e->getMessage());
            $this->comment("You can try uploading manually later via the UI.");
            return 1;
        }
    }
}
