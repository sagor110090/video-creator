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

            if (!file_exists($videoPath)) {
                throw new \Exception("Video file not found at: {$videoPath}");
            }

            $fileSize = filesize($videoPath);
            Log::info("Video file: {$videoPath}, Size: {$fileSize} bytes");

            // Use cURL to upload directly to Facebook
            $endpoint = "https://graph-video.facebook.com/v18.0/{$page->page_id}/videos";
            
            $data = [
                'title' => $story->title ?: 'AI Generated Video',
                'description' => $story->content,
                'access_token' => $page->access_token,
                'source' => new \CURLFile($videoPath, 'video/mp4', basename($videoPath)),
            ];

            Log::info("Posting to Facebook endpoint: {$endpoint}");

            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $endpoint);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_TIMEOUT, 0); // No timeout for large uploads
            curl_setopt($ch, CURLOPT_NOPROGRESS, false);
            
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            $error = curl_error($ch);
            curl_close($ch);

            if ($error) {
                throw new \Exception("cURL Error: {$error}");
            }

            if ($httpCode !== 200) {
                Log::error("Facebook API HTTP {$httpCode}: {$response}");
                throw new \Exception("Facebook API returned HTTP {$httpCode}: {$response}");
            }

            $result = json_decode($response, true);
            
            if (!isset($result['id'])) {
                Log::error("Facebook API response: " . $response);
                throw new \Exception("Invalid response from Facebook: " . $response);
            }

            $videoId = $result['id'];
            Log::info("Facebook video upload successful for Story ID: {$story->id}. Video ID: {$videoId}");

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
}
