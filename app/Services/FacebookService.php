<?php

namespace App\Services;

use Facebook\Facebook;
use App\Models\FacebookPage;
use App\Models\Story;
use Illuminate\Support\Facades\Log;

class FacebookService
{
    protected $fb;

    public function __construct()
    {
        $this->fb = new Facebook([
            'app_id' => env('FACEBOOK_CLIENT_ID'),
            'app_secret' => env('FACEBOOK_CLIENT_SECRET'),
            'default_graph_version' => 'v18.0',
        ]);
    }

    public function uploadReel(Story $story, FacebookPage $page)
    {
        try {
            Log::info("Starting Facebook Reels upload for Story ID: {$story->id} to page: {$page->name}");
            $story->update(['facebook_upload_status' => 'uploading']);

            $videoPath = public_path('storage/' . $story->video_path);
            if (!file_exists($videoPath) || is_dir($videoPath)) {
                $videoPath = $story->video_path;
            }

            if (!file_exists($videoPath) || is_dir($videoPath)) {
                throw new \Exception("Video file not found: {$videoPath}");
            }

            $fileSize = filesize($videoPath);
            $accessToken = $page->access_token;
            $pageId = $page->page_id;

            // Step 1: Initialize the Reels upload session
            Log::info("Step 1: Initializing Reels upload session");
            $initUrl = "https://graph.facebook.com/v18.0/{$pageId}/video_reels";
            $initData = [
                'upload_phase' => 'start',
                'access_token' => $accessToken
            ];

            $ch = curl_init($initUrl);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $initData);
            $response = curl_exec($ch);
            $initResult = json_decode($response, true);
            curl_close($ch);

            if (!isset($initResult['video_id']) || !isset($initResult['upload_url'])) {
                throw new \Exception("Failed to initialize Reels upload: " . $response);
            }

            $videoId = $initResult['video_id'];
            $uploadUrl = $initResult['upload_url'];

            // Step 2: Upload the video binary
            Log::info("Step 2: Uploading video binary to: {$uploadUrl}");
            $videoData = file_get_contents($videoPath);
            $ch = curl_init($uploadUrl);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                "Authorization: OAuth {$accessToken}",
                "offset: 0",
                "file_size: {$fileSize}",
                "Content-Type: application/octet-stream"
            ]);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $videoData);
            $response = curl_exec($ch);
            $uploadResult = json_decode($response, true);
            curl_close($ch);

            if (!isset($uploadResult['success']) || $uploadResult['success'] !== true) {
                throw new \Exception("Failed to upload video binary: " . $response);
            }

            // Step 3: Finish and Publish the Reel
            Log::info("Step 3: Finishing Reels upload and publishing");
            $finishUrl = "https://graph.facebook.com/v18.0/{$pageId}/video_reels";
            $finishData = [
                'upload_phase' => 'finish',
                'access_token' => $accessToken,
                'video_id' => $videoId,
                'video_state' => 'PUBLISHED',
                'description' => $story->title . "\n\n" . $story->content
            ];

            $ch = curl_init($finishUrl);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $finishData);
            $response = curl_exec($ch);
            $finishResult = json_decode($response, true);
            curl_close($ch);

            if (!isset($finishResult['success']) || $finishResult['success'] !== true) {
                throw new \Exception("Failed to publish Reel: " . $response);
            }

            Log::info("Facebook Reel upload successful for Story ID: {$story->id}. Video ID: {$videoId}");

            $story->update([
                'facebook_video_id' => $videoId,
                'is_uploaded_to_facebook' => true,
                'facebook_upload_status' => 'completed',
            ]);

            return $videoId;

        } catch (\Exception $e) {
            Log::error("Facebook Reel upload failed: " . $e->getMessage());
            $story->update([
                'facebook_upload_status' => 'failed',
                'facebook_error' => $e->getMessage()
            ]);
            throw $e;
        }
    }

    public function uploadVideo(Story $story, FacebookPage $page)
    {
        // Redirect all video uploads to Reels as requested by the user
        return $this->uploadReel($story, $page);
    }
}
