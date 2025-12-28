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

    public function uploadVideo(Story $story, FacebookPage $page)
    {
        try {
            Log::info("Starting Facebook Reels upload for Story ID: {$story->id} to page: {$page->name}");

            $story->update(['facebook_upload_status' => 'uploading']);

            $videoPath = public_path('storage/' . $story->video_path);

            if (!file_exists($videoPath) || is_dir($videoPath)) {
                $videoPath = $story->video_path;
            }

            if (!file_exists($videoPath) || is_dir($videoPath)) {
                throw new \Exception("Video file not found or is a directory: {$videoPath}");
            }

            $fileSize = filesize($videoPath);
            Log::info("Video file: {$videoPath}, Size: {$fileSize} bytes");

            // Step 1: Initialize upload session
            $videoId = $this->initializeUploadSession($page);
            Log::info("Upload session initialized. Video ID: {$videoId}");

            // Step 2: Upload the video file
            $this->uploadVideoFile($videoId, $videoPath, $fileSize, $page->access_token);
            Log::info("Video file uploaded successfully");

            // Step 3: Publish the reel
            $this->publishReel($videoId, $page, $story);
            Log::info("Reel published successfully");

            $story->update([
                'facebook_video_id' => $videoId,
                'is_uploaded_to_facebook' => true,
                'facebook_upload_status' => 'completed',
            ]);

            return $videoId;

        } catch (\Exception $e) {
            Log::error("Facebook upload failed for Story ID: {$story->id}: " . $e->getMessage());
            Log::error("Exception trace: " . $e->getTraceAsString());

            $story->update([
                'facebook_upload_status' => 'failed',
                'facebook_error' => $e->getMessage()
            ]);

            throw $e;
        }
    }

    private function initializeUploadSession(FacebookPage $page)
    {
        $endpoint = "https://graph.facebook.com/v18.0/{$page->page_id}/video_reels";

        $data = [
            'upload_phase' => 'start',
            'access_token' => $page->access_token,
        ];

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $endpoint);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode !== 200) {
            throw new \Exception("Failed to initialize upload session. HTTP {$httpCode}: {$response}");
        }

        $result = json_decode($response, true);

        if (!isset($result['video_id'])) {
            throw new \Exception("Invalid response from Facebook during initialization: {$response}");
        }

        return $result['video_id'];
    }

    private function uploadVideoFile($videoId, $videoPath, $fileSize, $accessToken)
    {
        $endpoint = "https://rupload.facebook.com/video-upload/{$videoId}";

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $endpoint);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Authorization: OAuth ' . $accessToken,
            'offset: 0',
            'file_size: ' . $fileSize,
        ]);
        curl_setopt($ch, CURLOPT_POSTFIELDS, file_get_contents($videoPath));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 0);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode !== 200) {
            throw new \Exception("Failed to upload video file. HTTP {$httpCode}: {$response}");
        }

        $result = json_decode($response, true);

        if (!isset($result['success']) || !$result['success']) {
            throw new \Exception("Video upload failed: {$response}");
        }
    }

    private function publishReel($videoId, FacebookPage $page, Story $story)
    {
        $endpoint = "https://graph.facebook.com/v18.0/{$page->page_id}/video_reels";

        $data = [
            'access_token' => $page->access_token,
            'video_id' => $videoId,
            'upload_phase' => 'finish',
            'video_state' => 'PUBLISHED',
            'description' => $story->content,
        ];

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $endpoint);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode !== 200) {
            throw new \Exception("Failed to publish reel. HTTP {$httpCode}: {$response}");
        }

        $result = json_decode($response, true);

        if (!isset($result['success']) || !$result['success']) {
            throw new \Exception("Publishing reel failed: {$response}");
        }
    }
}
