<?php

namespace App\Console\Commands;

use App\Models\Story;
use App\Jobs\UploadToYouTubeJob;
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
    public function handle()
    {
        $this->info('Checking for scheduled uploads...');

        $stories = Story::where('status', 'completed')
            ->whereNotNull('scheduled_for')
            ->where('scheduled_for', '<=', now())
            ->where('is_uploaded_to_youtube', false)
            ->whereNull('youtube_upload_status') // Only pick up if not already uploading/uploaded/failed
            ->get();

        if ($stories->isEmpty()) {
            $this->info('No scheduled uploads found.');
            return;
        }

        foreach ($stories as $story) {
            $this->info("Dispatching upload for story ID: {$story->id} - {$story->title}");
            
            // Mark as uploading so it doesn't get picked up again immediately if job is slow to start
            // The job will update this status as well
            $story->update(['youtube_upload_status' => 'uploading']);
            
            UploadToYouTubeJob::dispatch($story);
        }

        $this->info("Dispatched {$stories->count()} stories for upload.");
    }
}
