<?php

namespace App\Jobs;

use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;

use App\Models\Story;
use App\Models\Scene;
use App\Jobs\UploadToYouTubeJob;
use App\Jobs\UploadToFacebookJob;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;

class ProcessStoryJob implements ShouldQueue
{
    use Queueable;

    public $timeout = 3600;

    public function __construct(public Story $story) {}

    public function handle(): void
    {
        try {
            $this->story->update(['status' => 'processing']);

            // STEP 1: Story Parser (Storyboard Creation)
            Log::info("STEP 1: Parsing story into storyboard for Story ID: {$this->story->id}");
            $storyboard = $this->parseStory($this->story->content);

            foreach ($storyboard as $index => $scene) {
                $this->story->scenes()->create([
                    'order' => $index,
                    'narration' => $scene['narration'],
                    'image_prompt' => $scene['image_prompt'],
                ]);
            }

            // STEPS 2, 3, & 4: Voice, Video, and Assembly (via Python Worker)
            Log::info("STEPS 2-4: Starting AI generation and assembly for Story ID: {$this->story->id}");
            $this->runAiWorker();
            Log::info("Workflow completed for Story ID: {$this->story->id}");

            $this->story->update(['status' => 'completed']);

            // STEP 5: Auto-upload to YouTube/Facebook if configured
            if ($this->story->youtube_token_id) {
                Log::info("Dispatching YouTube upload job for Story ID: {$this->story->id}");
                UploadToYouTubeJob::dispatch($this->story);
            }

            if ($this->story->facebook_page_id && $this->story->facebookPage) {
                Log::info("Dispatching Facebook upload job for Story ID: {$this->story->id}");
                UploadToFacebookJob::dispatch($this->story, $this->story->facebookPage);
            }
        } catch (\Exception $e) {
            Log::error('Video processing failed: ' . $e->getMessage());
            $this->story->update(['status' => 'failed']);
        }
    }

    /**
     * Step 1: Story Parser
     * Breaks the story into a "Storyboard" (Scene 1, Scene 2, etc.)
     */
    private function parseStory($content)
    {
        // Normalize text
        $content = str_replace(["\r", "\n"], " ", $content);

        // Split into sentences (Story Parser logic)
        $sentences = preg_split('/(?<=[.!?])\s+/', $content, -1, PREG_SPLIT_NO_EMPTY);

        $style = $this->story->style ?? 'story';
        $visualStyle = "Cinematic storybook illustration";

        if ($style === 'science_short') {
            $visualStyle = "High-tech scientific visualization, 8k, detailed, space/lab setting";
        } elseif ($style === 'hollywood_hype') {
            $visualStyle = "Glossy celebrity news style, paparazzi lighting, red carpet atmosphere";
        } elseif ($style === 'trade_wave') {
            $visualStyle = "Professional financial news, trading charts background, modern office, clean aesthetic";
        }

        $storyboard = [];
        foreach ($sentences as $sentence) {
            $sentence = trim($sentence);
            if (strlen($sentence) < 10) continue;

            $storyboard[] = [
                'narration' => $sentence,
                'image_prompt' => "{$visualStyle} of: " . $sentence,
            ];
        }

        return array_slice($storyboard, 0, 50);
    }

    /**
     * Steps 2-4: Automatic AI Generation & Assembly
     * Calls the Python worker to handle Voice, Video, and stitching.
     */
    private function runAiWorker()
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
            'style' => $this->story->style ?? 'story',
            'scenes' => $scenes,
            'aspect_ratio' => $this->story->aspect_ratio ?? '16:9',
            'output_dir' => storage_path("app/public/videos/{$this->story->id}"),
        ];

        if (!is_dir($inputData['output_dir'])) {
            mkdir($inputData['output_dir'], 0777, true);
        }

        $jsonInput = json_encode($inputData);
        $pythonPath = '/usr/bin/python3';
        $pythonScript = base_path('ai_worker/worker.py');

        $process = new Process([$pythonPath, $pythonScript, $jsonInput]);
        $process->setTimeout(1800); // 30 minutes
        $process->run();

        Log::info('AI Worker Output: ' . $process->getOutput());
        if ($process->getErrorOutput()) {
            Log::debug('AI Worker Debug/Error: ' . $process->getErrorOutput());
        }

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
