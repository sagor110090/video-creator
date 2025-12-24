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
            $this->youtubeService->storeToken($request->code);
            return response()->json(['message' => 'YouTube authentication successful!']);
        }

        return response()->json(['error' => 'Authentication failed'], 400);
    }
}
