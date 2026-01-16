<?php

namespace App\Http\Controllers;

use App\Models\Story;
use App\Jobs\ProcessStoryJob;
use App\Jobs\UploadToYouTubeJob;
use App\Services\AiStoryService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class StoryController extends Controller
{
    public function index(Request $request)
    {
        $query = Story::with(['youtubeChannel'])->withCount('scenes')->latest();

        if ($request->has('channel_id') && $request->channel_id) {
            $query->where('youtube_token_id', $request->channel_id);
        }

        return $query->paginate(9);
    }

    public function generate(Request $request, AiStoryService $aiService)
    {
        $request->validate([
            'title' => 'nullable|string|max:255',
            'topic' => 'nullable|string|max:255',
            'style' => 'nullable|string|in:story,science_short,hollywood_hype,bollywood_masala,trade_wave',
            'talking_style' => 'nullable|string|in:none,opinion,storytime,educational,reaction,vlog',
            'aspect_ratio' => 'nullable|string|in:16:9,9:16',
        ]);

        try {
            $topic = $request->title ?? $request->topic;
            $storyData = $aiService->generateStory(
                $topic,
                $request->style ?? 'story',
                $request->aspect_ratio ?? '16:9',
                $request->talking_style ?? 'none'
            );
            return response()->json($storyData);
        } catch (\Exception $e) {
            return response()->json(['error' => 'Failed to generate story: ' . $e->getMessage()], 500);
        }
    }

    public function store(Request $request)
    {
        $request->validate([
            'content' => 'required|string|min:10',
            'title' => 'nullable|string|max:255',
            'style' => 'nullable|string|in:story,science_short,hollywood_hype,bollywood_masala,trade_wave',
            'talking_style' => 'nullable|string|in:none,opinion,storytime,educational,reaction,vlog',
            'aspect_ratio' => 'nullable|string|in:16:9,9:16',
            'youtube_title' => 'nullable|string|max:100',
            'youtube_description' => 'nullable|string',
            'youtube_tags' => 'nullable|string',
            'youtube_token_id' => 'nullable|exists:youtube_tokens,id',
            'scheduled_for' => 'nullable|date',
        ]);

        $story = Story::create([
            'title' => $request->title ?? 'Untitled Story',
            'content' => $request->content,
            'style' => $request->style ?? 'story',
            'talking_style' => $request->talking_style ?? 'none',
            'status' => 'pending',
            'aspect_ratio' => $request->aspect_ratio ?? '16:9',
            'youtube_title' => $request->youtube_title,
            'youtube_description' => $request->youtube_description,
            'youtube_tags' => $request->youtube_tags,
            'youtube_token_id' => $request->youtube_token_id,
            'scheduled_for' => $request->scheduled_for,
        ]);

        ProcessStoryJob::dispatch($story);

        return response()->json($story, 201);
    }

    public function update(Request $request, Story $story)
    {
        $request->validate([
            'youtube_title' => 'nullable|string|max:100',
            'youtube_description' => 'nullable|string',
            'youtube_tags' => 'nullable|string',
            'youtube_token_id' => 'nullable|exists:youtube_tokens,id',
        ]);

        $story->update($request->only([
            'youtube_title',
            'youtube_description',
            'youtube_tags',
            'youtube_token_id'
        ]));

        return response()->json($story->load('youtubeChannel'));
    }

    public function uploadToYouTube(Story $story)
    {
        if ($story->status !== 'completed') {
            return response()->json(['error' => 'Video generation is not completed yet.'], 400);
        }

        if (!$story->youtube_title) {
            return response()->json(['error' => 'YouTube title is required for upload.'], 400);
        }

        // If scheduled_for is set, we don't dispatch immediately
        if ($story->scheduled_for && $story->scheduled_for->isFuture()) {
             // Reset error if any
            $story->update(['youtube_error' => null]);
            return response()->json(['message' => 'Video scheduled for upload.']);
        }

        UploadToYouTubeJob::dispatch($story);

        return response()->json(['message' => 'Upload queued successfully.']);
    }

    public function schedule(Request $request, Story $story)
    {
        \Log::info('Scheduling Request:', [
            'story_id' => $story->id,
            'input' => $request->all(),
            'server_time' => now()->toDateTimeString(),
            'timezone' => config('app.timezone'),
        ]);

        $request->validate([
            'scheduled_for' => 'nullable|date',
            'youtube_title' => 'nullable|string|max:100',
            'youtube_description' => 'nullable|string',
            'youtube_tags' => 'nullable|string',
            'youtube_token_id' => 'nullable|exists:youtube_tokens,id',
        ]);

        $story->update([
            'scheduled_for' => $request->scheduled_for,
            'youtube_title' => $request->youtube_title ?? $story->youtube_title,
            'youtube_description' => $request->youtube_description ?? $story->youtube_description,
            'youtube_tags' => $request->youtube_tags ?? $story->youtube_tags,
            'youtube_token_id' => $request->youtube_token_id ?? $story->youtube_token_id,
            'youtube_upload_status' => 'uploading',
        ]);

        if ($story->scheduled_for) {
            \Log::info("Dispatching immediate upload for scheduled story ID: {$story->id}");
            UploadToYouTubeJob::dispatch($story);
        }

        return response()->json($story->load('youtubeChannel'));
    }

    public function generateMetadata(Story $story, AiStoryService $aiService)
    {
        try {
            $metadata = $aiService->generateMetadata($story->content);

            $story->update([
                'youtube_title' => $metadata['youtube_title'] ?? $story->youtube_title,
                'youtube_description' => $metadata['youtube_description'] ?? $story->youtube_description,
                'youtube_tags' => $metadata['youtube_tags'] ?? $story->youtube_tags,
            ]);

            return response()->json($story);
        } catch (\Exception $e) {
            return response()->json(['error' => 'Failed to generate metadata'], 500);
        }
    }

    public function show(Story $story)
    {
        return $story->load('scenes');
    }

    public function destroy(Story $story)
    {
        $videoDir = storage_path('app/public/videos/' . $story->id);

        if (is_dir($videoDir)) {
            $files = array_diff(scandir($videoDir), array('.', '..'));
            foreach ($files as $file) {
                $filePath = $videoDir . '/' . $file;
                if (is_file($filePath)) {
                    unlink($filePath);
                }
            }
            rmdir($videoDir);
        }

        $story->delete();
        return response()->json(['message' => 'Story deleted successfully']);
    }

    public function regenerate(Story $story)
    {
        // Reset status to pending
        $story->update(['status' => 'pending']);

        // Re-dispatch the processing job
        ProcessStoryJob::dispatch($story);

        return response()->json(['message' => 'Video regeneration started.']);
    }

    public function searchNews(Request $request)
    {
        $query = $request->input('query') ?? $request->query('q');
        if (!$query) {
            return response()->json([]);
        }

        // Use Google Search via a simple scraping or a proper API if available
        // For now, let's use a simpler approach: use AI to "simulate" or provide latest info if it has web access
        // OR we can use a free news API. Let's try to use a simple news search service if available.
        // For this demo, I'll use a public news API or simulate with AI if no key is provided.

        try {
            // Using AI to generate "news" snippets based on the query as a fallback/simulator
            // or we could use a real API like NewsAPI.org if the user has a key.
            // Let's implement a simple AI-based news summary generator for now to avoid dependency on external API keys.

            $aiService = app(AiStoryService::class);
            // Pass style to get context-aware news (hollywood vs finance)
            $style = $request->input('style', 'hollywood_hype');
            $news = $aiService->searchNews($query, $style);

            return response()->json($news);
        } catch (\Exception $e) {
            Log::error('News search failed: ' . $e->getMessage());
            return response()->json(['error' => 'Failed to search news'], 500);
        }
    }
}
