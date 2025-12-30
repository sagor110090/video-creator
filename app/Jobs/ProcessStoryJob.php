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

            // Clear existing scenes if any (idempotency)
            $this->story->scenes()->delete();

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

            // STEP 5: Auto-upload only if generated via Scheduler
            // Check if the story was created by the scheduler (it will have a user_id from the schedule but no manual trigger)
            if ($this->story->is_from_scheduler) {
                if ($this->story->youtube_token_id) {
                    Log::info("Scheduler: Dispatching YouTube upload job for Story ID: {$this->story->id}");
                    UploadToYouTubeJob::dispatch($this->story);
                }

                if ($this->story->facebook_page_id && $this->story->facebookPage) {
                    Log::info("Scheduler: Dispatching Facebook upload job for Story ID: {$this->story->id}");
                    UploadToFacebookJob::dispatch($this->story, $this->story->facebookPage);
                }
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
        $visualPrefix = "";

        if ($style === 'science_short') {
            $visualPrefix = "science, technology, ";
        } elseif ($style === 'hollywood_hype') {
            $visualPrefix = "news, celebrity, ";
        } elseif ($style === 'trade_wave') {
            $visualPrefix = "finance, business, ";
        }

        $storyboard = [];
        foreach ($sentences as $sentence) {
            $sentence = trim($sentence);
            if (strlen($sentence) < 10) continue;

            // Generate a clean, search-friendly prompt
            // Focus on the core sentence content without AI jargon
            $storyboard[] = [
                'narration' => $sentence,
                'image_prompt' => $visualPrefix . $sentence,
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
            'background_music' => public_path('audio/background.mp3'),
        ];

        if (!is_dir($inputData['output_dir'])) {
            mkdir($inputData['output_dir'], 0777, true);
        }

        $jsonInput = json_encode($inputData);

        $pythonPath = base_path('ai_worker/venv/bin/python3');
        $pythonScript = base_path('ai_worker/worker.py');

        $process = new Process([$pythonPath, $pythonScript, $jsonInput], null, null, null);
        $process->setTimeout(1800); // 30 minutes
        $process->setWorkingDirectory(base_path('ai_worker'));
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
            $fullPath = $output['video_path'];
            $storagePrefix = storage_path('app/public/');

            // Ensure we are saving the file path, not the directory path
            if (is_file($fullPath)) {
                $relativePath = str_replace($storagePrefix, '', $fullPath);
                $this->story->update([
                    'video_path' => $relativePath
                ]);
            } else {
                throw new \Exception("AI Worker reported success but video file not found at: " . $fullPath);
            }
        }
    }
}
