<?php

namespace App\Http\Controllers;

use App\Models\VideoSchedule;
use Illuminate\Http\Request;

class VideoScheduleController extends Controller
{
    public function index()
    {
        return VideoSchedule::with(['youtubeToken', 'story'])
            ->latest()
            ->paginate(20);
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'topic' => 'required|string|max:255',
            'style' => 'required|string',
            'aspect_ratio' => 'required|string',
            'scheduled_time' => 'required|string',
            'youtube_token_id' => 'nullable|exists:youtube_tokens,id',
        ]);

        $schedule = VideoSchedule::create($validated);

        return response()->json($schedule->load('youtubeToken'));
    }

    public function update(Request $request, VideoSchedule $videoSchedule)
    {
        $validated = $request->validate([
            'topic' => 'required|string|max:255',
            'style' => 'required|string',
            'aspect_ratio' => 'required|string',
            'scheduled_time' => 'required|string',
            'youtube_token_id' => 'nullable|exists:youtube_tokens,id',
        ]);

        $videoSchedule->update($validated);

        return response()->json($videoSchedule->load('youtubeToken'));
    }

    public function destroy(VideoSchedule $videoSchedule)
    {
        $videoSchedule::destroy($videoSchedule->id);
        return response()->json(['message' => 'Schedule deleted successfully.']);
    }
}
