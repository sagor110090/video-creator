<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Services\YouTubeService;
use Illuminate\Support\Facades\Redirect;

class YouTubeController extends Controller
{
    protected $youtubeService;

    public function __construct(YouTubeService $youtubeService)
    {
        $this->youtubeService = $youtubeService;
    }

    public function auth()
    {
        return Redirect::to($this->youtubeService->getAuthUrl());
    }

    public function callback(Request $request)
    {
        if ($request->has('code')) {
            $reconnectTokenId = session('youtube_reconnect_token_id');

            if ($reconnectTokenId) {
                $token = \App\Models\YoutubeToken::find($reconnectTokenId);
                session()->forget('youtube_reconnect_token_id');

                if ($token) {
                    $this->youtubeService->updateToken($token, $request->code);
                    return response()->json([
                        'message' => 'YouTube reconnection successful!',
                        'channel' => [
                            'title' => $token->channel_title,
                            'thumbnail' => $token->channel_thumbnail
                        ],
                        'reconnected' => true
                    ]);
                }
            }

            $token = $this->youtubeService->storeToken($request->code);
            return response()->json([
                'message' => 'YouTube authentication successful!',
                'channel' => [
                    'title' => $token->channel_title,
                    'thumbnail' => $token->channel_thumbnail
                ],
                'reconnected' => false
            ]);
        }

        return response()->json(['error' => 'Authentication failed'], 400);
    }

    public function channels()
    {
        return \App\Models\YoutubeToken::all(['id', 'channel_id', 'channel_title', 'channel_thumbnail']);
    }

    public function disconnect($id)
    {
        \App\Models\YoutubeToken::destroy($id);
        return response()->json(['message' => 'Channel disconnected successfully.']);
    }

    public function reconnect($id)
    {
        session(['youtube_reconnect_token_id' => $id]);
        return Redirect::to($this->youtubeService->getAuthUrl());
    }

    public function refresh($id)
    {
        $token = \App\Models\YoutubeToken::find($id);
        if (!$token) {
            return response()->json(['error' => 'Token not found'], 404);
        }

        $refreshed = $this->youtubeService->refreshToken($token);
        if ($refreshed) {
            return response()->json(['message' => 'Token refreshed successfully']);
        }

        return response()->json(['error' => 'Failed to refresh token'], 500);
    }
}
