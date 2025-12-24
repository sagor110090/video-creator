<?php

namespace App\Jobs;

use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;

use App\Models\Story;
use App\Models\Scene;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;

class ProcessStoryJob implements ShouldQueue
{
    use Queueable;

    public function __construct(public Story $story) {}

    public function handle(): void
    {
        try {
            $this->story->update(['status' => 'processing']);

            // 1. Mock LLM: Split story into 6 scenes
            $scenesData = $this->generateScenesMock($this->story->content);

            foreach ($scenesData as $index => $data) {
                $this->story->scenes()->create([
                    'order' => $index,
                    'narration' => $data['narration'],
                    'image_prompt' => $data['image_prompt'],
                ]);
            }

            // 2. Call Python Worker
            Log::info('Starting video processing for Story ID: ' . $this->story->id);
            $this->processVideo();
            Log::info('Finished video processing for Story ID: ' . $this->story->id);

            $this->story->update(['status' => 'completed']);
        } catch (\Exception $e) {
            Log::error('Video processing failed: ' . $e->getMessage());
            $this->story->update(['status' => 'failed']);
        }
    }

    private function generateScenesMock($content)
    {
        // First, normalize the text: replace newlines with spaces to handle blocks of text
        $content = str_replace(["\r", "\n"], " ", $content);

        // Use a more robust regex to split into sentences
        // This splits by . ! or ? followed by a space OR end of string
        $sentences = preg_split('/(?<=[.!?])\s+/', $content, -1, PREG_SPLIT_NO_EMPTY);

        $scenes = [];
        foreach ($sentences as $sentence) {
            $sentence = trim($sentence);
            if (strlen($sentence) < 10) continue; // Skip very short fragments

            $scenes[] = [
                'narration' => $sentence,
                'image_prompt' => "Cinematic storybook illustration of: " . $sentence,
            ];
        }

        // Return all scenes, up to 50 for safety
        return array_slice($scenes, 0, 50);
    }

    private function processVideo()
    {
        $scenes = $this->story->scenes()->get()->map(function($scene) {
            return [
                'id' => $scene->id,
                'narration' => $scene->narration,
                'image_prompt' => $scene->image_prompt,
            ];
        })->toArray();

        $inputData = [
            'story_id' => $this->story->id,
            'scenes' => $scenes,
            'output_dir' => storage_path("app/public/videos/{$this->story->id}"),
        ];

        if (!is_dir($inputData['output_dir'])) {
            mkdir($inputData['output_dir'], 0777, true);
        }

        $jsonInput = json_encode($inputData);
        $pythonPath = '/opt/homebrew/bin/python3';
        $pythonScript = base_path('ai_worker/worker.py');

        $process = new Process([$pythonPath, $pythonScript, $jsonInput]);
        $process->setTimeout(600); // 10 minutes
        $process->run();

        Log::info('Python Worker Output: ' . $process->getOutput());
        Log::info('Python Worker Error: ' . $process->getErrorOutput());

        if (!$process->isSuccessful()) {
            throw new ProcessFailedException($process);
        }

        $output = json_decode($process->getOutput(), true);

        if (isset($output['video_path'])) {
            $this->story->update([
                'video_path' => str_replace(storage_path('app/public/'), '', $output['video_path'])
            ]);
        }
    }
}
