<?php

namespace App\Jobs;

use App\Models\Story;
use App\Models\FacebookPage;
use App\Services\FacebookService;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Support\Facades\Log;

class UploadToFacebookJob implements ShouldQueue
{
    use Queueable;

    public function __construct(
        public Story $story,
        public FacebookPage $page
    ) {
    }

    public function handle(FacebookService $facebookService): void
    {
        try {
            Log::info("Starting Facebook upload for Story ID: {$this->story->id}");
            
            $this->story->update(['facebook_upload_status' => 'uploading']);
            
            $videoId = $facebookService->uploadVideo($this->story, $this->page);
            
            Log::info("Facebook upload successful for Story ID: {$this->story->id}. Video ID: {$videoId}");
            
        } catch (\Exception $e) {
            Log::error("Facebook upload failed for Story ID: {$this->story->id}: " . $e->getMessage());
            $this->story->update(['facebook_upload_status' => 'failed']);
        }
    }
}
