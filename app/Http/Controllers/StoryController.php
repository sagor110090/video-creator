<?php

namespace App\Http\Controllers;

use App\Models\Story;
use App\Jobs\ProcessStoryJob;
use Illuminate\Http\Request;

class StoryController extends Controller
{
    public function index()
    {
        return Story::latest()->get();
    }

    public function store(Request $request)
    {
        $request->validate([
            'content' => 'required|string|min:10',
            'title' => 'nullable|string|max:255',
        ]);

        $story = Story::create([
            'title' => $request->title ?? 'Untitled Story',
            'content' => $request->content,
            'status' => 'pending',
        ]);

        ProcessStoryJob::dispatch($story);

        return response()->json($story, 201);
    }

    public function show(Story $story)
    {
        return $story->load('scenes');
    }
}
