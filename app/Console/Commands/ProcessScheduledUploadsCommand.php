<?php

namespace App\Console\Commands;

use App\Models\Story;
use App\Jobs\UploadToYouTubeJob;
use App\Services\YouTubeService;
use Illuminate\Console\Command;

class ProcessScheduledUploadsCommand extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'stories:process-scheduled';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Process and upload scheduled stories to YouTube';

    /**
     * Execute the console command.
     */
    public function handle(YouTubeService $youtubeService)
    {
        $this->info('Checking for scheduled uploads...');

        // 1. Upload videos that are due but not yet uploaded
        $storiesToUpload = Story::where('status', 'completed')
            ->whereNotNull('scheduled_for')
            ->where('scheduled_for', '<=', now())
            ->where('is_uploaded_to_youtube', false)
            ->whereNull('youtube_upload_status') // Only pick up if not already uploading/uploaded/failed
            ->get();

        if ($storiesToUpload->isNotEmpty()) {
            foreach ($storiesToUpload as $story) {
                $this->info("Dispatching upload for story ID: {$story->id} - {$story->title}");
                
                // Mark as uploading so it doesn't get picked up again immediately
                $story->update(['youtube_upload_status' => 'uploading']);
                
                UploadToYouTubeJob::dispatch($story);
            }
            $this->info("Dispatched {$storiesToUpload->count()} stories for upload.");
        } else {
            $this->info('No pending uploads found.');
        }

        // 2. Publish videos that are uploaded (private) and now due
        $this->info('Checking for videos to publish...');
        
        $storiesToPublish = Story::where('is_uploaded_to_youtube', true)
            ->where('youtube_upload_status', 'scheduled')
            ->where('scheduled_for', '<=', now())
            ->get();

        if ($storiesToPublish->isNotEmpty()) {
            foreach ($storiesToPublish as $story) {
                $this->info("Publishing story ID: {$story->id} - {$story->title}");
                $youtubeService->publishScheduledVideo($story);
            }
            $this->info("Published {$storiesToPublish->count()} stories.");
        } else {
            $this->info('No videos to publish found.');
        }
    }
}
