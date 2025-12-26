<?php

namespace App\Services;

use Google\Client;
use Google\Service\YouTube;
use App\Models\YoutubeToken;
use App\Models\Story;
use Illuminate\Support\Facades\Log;
use Google\Service\YouTube\Video;
use Google\Service\YouTube\VideoSnippet;
use Google\Service\YouTube\VideoStatus;

class YouTubeService
{
    private $client;

    public function __construct()
    {
        $clientId = trim(config('services.youtube.client_id'));
        $clientSecret = trim(config('services.youtube.client_secret'));
        $redirectUri = trim(config('services.youtube.redirect_uri'));

        if (!$clientId || !$clientSecret) {
            Log::error('YouTube API credentials missing in .env file');
        }

        $this->client = new Client();
        $this->client->setClientId($clientId);
        $this->client->setClientSecret($clientSecret);
        $this->client->setRedirectUri($redirectUri);
        $this->client->addScope(YouTube::YOUTUBE_UPLOAD);
        $this->client->addScope(YouTube::YOUTUBE_READONLY);
        $this->client->setAccessType('offline');
        $this->client->setPrompt('select_account consent');
    }

    public function getAuthUrl()
    {
        $url = $this->client->createAuthUrl();
        Log::info('Generated YouTube Auth URL: ' . $url);
        return $url;
    }

    public function storeToken($code)
    {
        $accessToken = $this->client->fetchAccessTokenWithAuthCode($code);

        if (isset($accessToken['error'])) {
            throw new \Exception('Error fetching access token: ' . $accessToken['error_description']);
        }

        $this->client->setAccessToken($accessToken);
        $youtube = new YouTube($this->client);
        $channels = $youtube->channels->listChannels('snippet', ['mine' => true]);
        $channel = $channels->getItems()[0] ?? null;

        return YoutubeToken::updateOrCreate(
            ['channel_id' => $channel?->getId()],
            [
                'channel_title' => $channel?->getSnippet()?->getTitle(),
                'channel_thumbnail' => $channel?->getSnippet()?->getThumbnails()?->getDefault()?->getUrl(),
                'access_token' => json_encode($accessToken),
                'refresh_token' => $accessToken['refresh_token'] ?? null,
                'expires_at' => now()->addSeconds($accessToken['expires_in']),
            ]
        );
    }

    private function refreshAccessTokenIfExpired(YoutubeToken $token)
    {
        $accessToken = json_decode($token->access_token, true);
        $this->client->setAccessToken($accessToken);

        if ($this->client->isAccessTokenExpired()) {
            if ($token->refresh_token) {
                $newAccessToken = $this->client->fetchAccessTokenWithRefreshToken($token->refresh_token);

                if (isset($newAccessToken['error'])) {
                    throw new \Exception('Error refreshing access token: ' . $newAccessToken['error_description']);
                }

                $token->update([
                    'access_token' => json_encode($newAccessToken),
                    'expires_at' => now()->addSeconds($newAccessToken['expires_in']),
                ]);
            } else {
                throw new \Exception('Access token expired and no refresh token available.');
            }
        }
    }

    public function uploadVideo(Story $story)
    {
        try {
            $token = $story->youtube_token_id
                ? YoutubeToken::find($story->youtube_token_id)
                : YoutubeToken::first();

            if (!$token) {
                throw new \Exception('No YouTube account connected. Please connect a channel first.');
            }

            Log::info("Attempting YouTube upload for Story ID: {$story->id} using channel: {$token->channel_title} (ID: {$token->channel_id})");

            $this->refreshAccessTokenIfExpired($token);

            $youtube = new YouTube($this->client);

            $video = new Video();
            $snippet = new VideoSnippet();
            $snippet->setTitle($story->youtube_title ?: $story->title);
            $snippet->setDescription($story->youtube_description ?: $story->content);

            if ($story->youtube_tags) {
                $tags = is_array($story->youtube_tags) ? $story->youtube_tags : explode(',', $story->youtube_tags);
                $snippet->setTags(array_map('trim', $tags));
            }

            $video->setSnippet($snippet);

            $status = new VideoStatus();
            $status->setPrivacyStatus('public'); // or 'unlisted' or 'private'
            $video->setStatus($status);

            $videoPath = public_path('storage/' . $story->video_path);

            if (!file_exists($videoPath)) {
                // Try absolute path if not in storage/
                $videoPath = $story->video_path;
            }

            if (!file_exists($videoPath)) {
                throw new \Exception("Video file not found at: {$videoPath}");
            }

            $chunkSizeBytes = 1 * 1024 * 1024;
            $this->client->setDefer(true);

            $insertRequest = $youtube->videos->insert('status,snippet', $video);

            $media = new \Google\Http\MediaFileUpload(
                $this->client,
                $insertRequest,
                'video/*',
                null,
                true,
                $chunkSizeBytes
            );
            $media->setFileSize(filesize($videoPath));

            $status = false;
            $handle = fopen($videoPath, "rb");
            while (!$status && !feof($handle)) {
                $chunk = fread($handle, $chunkSizeBytes);
                $status = $media->nextChunk($chunk);
            }
            fclose($handle);

            $this->client->setDefer(false);

            $story->update([
                'youtube_video_id' => $status['id'],
                'is_uploaded_to_youtube' => true,
                'youtube_upload_status' => 'completed',
            ]);

            return $status['id'];

        } catch (\Exception $e) {
            $errorMessage = $e->getMessage();

            // Extract meaningful message from JSON error if possible
            if (strpos($errorMessage, '{') !== false) {
                $decoded = json_decode(substr($errorMessage, strpos($errorMessage, '{')), true);
                if (isset($decoded['error']['message'])) {
                    $errorMessage = $decoded['error']['message'];
                }
            }

            Log::error("YouTube upload failed for {$token->channel_title}: " . $e->getMessage());

            $finalError = $errorMessage;
            if (strpos($errorMessage, 'uploadLimitExceeded') !== false || strpos($errorMessage, 'exceeded the number of videos') !== false) {
                $finalError = "YouTube API upload limit reached for '{$token->channel_title}'. Note: API upload limits are separate and more restrictive than YouTube Studio manual uploads. Please try again in 24 hours or request a quota increase in Google Cloud Console.";
            }

            $story->update([
                'youtube_upload_status' => 'failed',
                'youtube_error' => $finalError
            ]);
            throw $e;
        }
    }
}
