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
    public function index()
    {
        return Story::withCount('scenes')->latest()->get();
    }

    public function generate(Request $request, AiStoryService $aiService)
    {
        $request->validate([
            'topic' => 'nullable|string|max:255',
            'style' => 'nullable|string|in:story,science_short',
        ]);

        try {
            $storyData = $aiService->generateStory($request->topic, $request->style ?? 'story');
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
            'aspect_ratio' => 'nullable|string|in:16:9,9:16',
            'youtube_title' => 'nullable|string|max:100',
            'youtube_description' => 'nullable|string',
            'youtube_tags' => 'nullable|string',
        ]);

        $story = Story::create([
            'title' => $request->title ?? 'Untitled Story',
            'content' => $request->content,
            'status' => 'pending',
            'aspect_ratio' => $request->aspect_ratio ?? '16:9',
            'youtube_title' => $request->youtube_title,
            'youtube_description' => $request->youtube_description,
            'youtube_tags' => $request->youtube_tags,
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
        ]);

        $story->update($request->only([
            'youtube_title',
            'youtube_description',
            'youtube_tags'
        ]));

        return response()->json($story);
    }

    public function uploadToYouTube(Story $story)
    {
        if ($story->status !== 'completed') {
            return response()->json(['error' => 'Video generation is not completed yet.'], 400);
        }

        if (!$story->youtube_title) {
            return response()->json(['error' => 'YouTube title is required for upload.'], 400);
        }

        UploadToYouTubeJob::dispatch($story);

        return response()->json(['message' => 'Upload queued successfully.']);
    }

    public function generateMetadata(Story $story, AiStoryService $aiService)
    {
        try {
            $prompt = "Generate viral YouTube metadata for this story: \n\n" . $story->content;
            $metadata = $aiService->generateStory($prompt); // This might need a specialized method but generateStory can work if we adjust it

            $story->update([
                'youtube_title' => $metadata['youtube_title'],
                'youtube_description' => $metadata['youtube_description'],
                'youtube_tags' => $metadata['youtube_tags'],
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
}
