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

        $tokenData = [
            'channel_title' => $channel?->getSnippet()?->getTitle(),
            'channel_thumbnail' => $channel?->getSnippet()?->getThumbnails()?->getDefault()?->getUrl(),
            'access_token' => json_encode($accessToken),
            'expires_at' => now()->addSeconds($accessToken['expires_in']),
        ];

        if (!empty($accessToken['refresh_token'])) {
            $tokenData['refresh_token'] = $accessToken['refresh_token'];
        }

        return YoutubeToken::updateOrCreate(
            ['channel_id' => $channel?->getId()],
            $tokenData
        );
    }

    public function updateToken(YoutubeToken $token, $code)
    {
        $accessToken = $this->client->fetchAccessTokenWithAuthCode($code);

        if (isset($accessToken['error'])) {
            throw new \Exception('Error fetching access token: ' . $accessToken['error_description']);
        }

        $this->client->setAccessToken($accessToken);
        $youtube = new YouTube($this->client);
        $channels = $youtube->channels->listChannels('snippet', ['mine' => true]);
        $channel = $channels->getItems()[0] ?? null;

        $tokenData = [
            'channel_title' => $channel?->getSnippet()?->getTitle(),
            'channel_thumbnail' => $channel?->getSnippet()?->getThumbnails()?->getDefault()?->getUrl(),
            'access_token' => json_encode($accessToken),
            'expires_at' => now()->addSeconds($accessToken['expires_in']),
        ];

        if (!empty($accessToken['refresh_token'])) {
            $tokenData['refresh_token'] = $accessToken['refresh_token'];
        }

        $token->update($tokenData);
        return $token;
    }

    private function refreshAccessTokenIfExpired(YoutubeToken $token)
    {
        $accessToken = json_decode($token->access_token, true);
        $this->client->setAccessToken($accessToken);

        if ($this->client->isAccessTokenExpired()) {
            if ($token->refresh_token) {
                $newAccessToken = $this->client->fetchAccessTokenWithRefreshToken($token->refresh_token);

                if (isset($newAccessToken['error'])) {
                    $errorDescription = $newAccessToken['error_description'] ?? 'Unknown error';

                    // Check for expired/revoked token
                    if (stripos($errorDescription, 'expired') !== false || stripos($errorDescription, 'revoked') !== false) {
                        Log::warning("YouTube token for channel {$token->channel_title} is expired or revoked. Deleting token.");
                        $token->delete();
                        throw new \Exception('YouTube connection expired. Please reconnect your channel: ' . $token->channel_title);
                    }

                    throw new \Exception('Error refreshing access token: ' . $errorDescription);
                }

                $updateData = [
                    'access_token' => json_encode($newAccessToken),
                    'expires_at' => now()->addSeconds($newAccessToken['expires_in']),
                ];

                if (!empty($newAccessToken['refresh_token'])) {
                    $updateData['refresh_token'] = $newAccessToken['refresh_token'];
                }

                $token->update($updateData);
            } else {
                Log::warning("YouTube token for channel {$token->channel_title} expired and has no refresh token. Deleting token.");
                $token->delete();
                throw new \Exception('Access token expired and no refresh token available. Please reconnect your channel.');
            }
        }
    }

    public function refreshToken(YoutubeToken $token)
    {
        try {
            $accessToken = json_decode($token->access_token, true);
            $this->client->setAccessToken($accessToken);

            if (!$this->client->isAccessTokenExpired()) {
                return true;
            }

            if (!$token->refresh_token) {
                Log::warning("YouTube token for channel {$token->channel_title} has no refresh token");
                return false;
            }

            $newAccessToken = $this->client->fetchAccessTokenWithRefreshToken($token->refresh_token);

            if (isset($newAccessToken['error'])) {
                Log::error("Error refreshing token for {$token->channel_title}: " . $newAccessToken['error_description']);
                return false;
            }

            $updateData = [
                'access_token' => json_encode($newAccessToken),
                'expires_at' => now()->addSeconds($newAccessToken['expires_in']),
            ];

            if (!empty($newAccessToken['refresh_token'])) {
                $updateData['refresh_token'] = $newAccessToken['refresh_token'];
            }

            $token->update($updateData);
            Log::info("Successfully refreshed token for {$token->channel_title}");
            return true;

        } catch (\Exception $e) {
            Log::error("Error refreshing token for {$token->channel_title}: " . $e->getMessage());
            return false;
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

            if ($story->scheduled_for) {
                $scheduledTime = new \DateTime($story->scheduled_for);
                $status->setPublishAt($scheduledTime->format(\DateTime::ATOM));
                $status->setPrivacyStatus('private'); // Scheduled videos must be private initially
                Log::info("Scheduling video for: " . $scheduledTime->format(\DateTime::ATOM));
            } else {
                $status->setPrivacyStatus('public');
            }

            $video->setStatus($status);

            $videoPath = public_path('storage/' . $story->video_path);

            if (!file_exists($videoPath) || is_dir($videoPath)) {
                // Try absolute path if not in storage/ or if storage path is actually a directory
                $videoPath = $story->video_path;
            }

            if (!file_exists($videoPath) || is_dir($videoPath)) {
                throw new \Exception("Video file not found or is a directory: {$videoPath}");
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

            $uploadStatus = $story->scheduled_for ? 'scheduled' : 'completed';

            $story->update([
                'youtube_video_id' => $status['id'],
                'is_uploaded_to_youtube' => true,
                'youtube_upload_status' => $uploadStatus,
            ]);

            $message = $story->scheduled_for
                ? "Video scheduled for {$story->scheduled_for} and will be published by YouTube automatically"
                : "Video published successfully";

            Log::info("YouTube upload successful for Story ID: {$story->id}. {$message}");

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
