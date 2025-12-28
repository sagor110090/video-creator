<?php

namespace App\Http\Controllers;

use App\Models\Schedule;
use App\Models\Story;
use App\Jobs\ProcessStoryJob;
use Illuminate\Http\Request;

class ScheduleController extends Controller
{
    public function index(Request $request)
    {
        $schedules = Schedule::with(['youtubeChannel', 'facebookPage'])
            ->where('user_id', auth()->id())
            ->orderBy('created_at', 'desc')
            ->get();

        return response()->json($schedules);
    }

    public function store(Request $request)
    {
        \Log::info('Schedule creation request:', $request->all());

        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'style' => 'required|in:story,science_short,hollywood_hype,trade_wave',
            'aspect_ratio' => 'required|in:16:9,9:16',
            'videos_per_day' => 'required|integer|min:1|max:50',
            'timezone' => 'required|string',
            'upload_times' => 'required|array|min:1',
            'upload_times.*' => 'required|string|date_format:H:i',
            'youtube_token_id' => 'nullable|integer|exists:youtube_tokens,id',
            'facebook_page_id' => 'nullable|integer|exists:facebook_pages,id',
            'prompt_template' => 'nullable|string',
        ]);

        $validated['user_id'] = auth()->id();
        $validated['is_active'] = true;
        $validated['last_generated_dates'] = [];

        \Log::info('Creating schedule with validated data:', $validated);

        $schedule = Schedule::create($validated);

        return response()->json($schedule->load(['youtubeChannel', 'facebookPage']), 201);
    }

    public function show($id)
    {
        $schedule = Schedule::where('id', $id)->where('user_id', auth()->id())->firstOrFail();

        return response()->json($schedule->load(['youtubeChannel', 'facebookPage']));
    }

    public function update(Request $request, $id)
    {
        $schedule = Schedule::where('id', $id)->where('user_id', auth()->id())->firstOrFail();

        $validated = $request->validate([
            'name' => 'sometimes|string|max:255',
            'style' => 'sometimes|in:story,science_short,hollywood_hype,trade_wave',
            'aspect_ratio' => 'sometimes|in:16:9,9:16',
            'videos_per_day' => 'sometimes|integer|min:1|max:50',
            'timezone' => 'sometimes|string',
            'upload_times' => 'sometimes|array|min:1',
            'upload_times.*' => 'sometimes|string|date_format:H:i',
            'youtube_token_id' => 'nullable|integer|exists:youtube_tokens,id',
            'facebook_page_id' => 'nullable|integer|exists:facebook_pages,id',
            'prompt_template' => 'nullable|string',
            'is_active' => 'sometimes|boolean',
        ]);

        $schedule->update($validated);

        return response()->json($schedule->load(['youtubeChannel', 'facebookPage']));
    }

    public function destroy($id)
    {
        $schedule = Schedule::where('id', $id)->where('user_id', auth()->id())->firstOrFail();

        $schedule->delete();

        return response()->json(null, 204);
    }

    public function generateVideo($id)
    {
        $schedule = Schedule::where('id', $id)->where('user_id', auth()->id())->firstOrFail();

        $story = Story::create([
            'user_id' => auth()->id(),
            'title' => $schedule->name . ' - ' . now()->format('Y-m-d H:i'),
            'content' => $schedule->prompt_template ?? 'Generate an interesting story',
            'style' => $schedule->style,
            'aspect_ratio' => $schedule->aspect_ratio,
            'status' => 'pending',
            'youtube_token_id' => $schedule->youtube_token_id,
            'facebook_page_id' => $schedule->facebook_page_id,
            'is_from_scheduler' => true,
        ]);

        ProcessStoryJob::dispatch($story);

        return response()->json($story, 201);
    }
}
