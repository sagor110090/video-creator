<?php

namespace App\Jobs;

use App\Models\Story;
use App\Services\YouTubeService;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Support\Facades\Log;

class UploadToYouTubeJob implements ShouldQueue
{
    use Queueable;

    /**
     * Create a new job instance.
     */
    public function __construct(public Story $story)
    {
        //
    }

    /**
     * Execute the job.
     */
    public function handle(YouTubeService $youtubeService): void
    {
        try {
            Log::info("Starting YouTube upload for Story ID: {$this->story->id}");
            
            $videoId = $youtubeService->uploadVideo($this->story);
            
            Log::info("YouTube upload successful for Story ID: {$this->story->id}. Video ID: {$videoId}");
            
        } catch (\Exception $e) {
            Log::error("YouTube upload failed for Story ID: {$this->story->id}: " . $e->getMessage());
            $this->story->update(['youtube_upload_status' => 'failed']);
        }
    }
}
