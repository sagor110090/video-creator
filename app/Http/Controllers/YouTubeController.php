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
            $token = $this->youtubeService->storeToken($request->code);
            return response()->json([
                'message' => 'YouTube authentication successful!',
                'channel' => [
                    'title' => $token->channel_title,
                    'thumbnail' => $token->channel_thumbnail
                ]
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
}
