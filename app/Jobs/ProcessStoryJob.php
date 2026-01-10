<?php

namespace App\Jobs;

use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;

use App\Models\Story;
use App\Models\Scene;
use App\Jobs\UploadToYouTubeJob;
use App\Services\AiStoryService;
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

            // Reload the story to get any changes made during runAiWorker (like video_path)
            $freshStory = $this->story->fresh();

            // Auto-upload if it's from a schedule or has a channel selected
            if ($freshStory->youtube_token_id) {
                Log::info("Auto-dispatching YouTube upload for Story ID: {$freshStory->id}");
                UploadToYouTubeJob::dispatch($freshStory);
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

        // 1. Filter valid sentences first
        $validSentences = [];
        foreach ($sentences as $sentence) {
            $sentence = trim($sentence);
            if (strlen($sentence) < 10) continue;
            $validSentences[] = $sentence;
        }

        // 2. Generate AI Prompts in Batch
        $aiPrompts = [];
        try {
            $aiService = new AiStoryService();
            $aiPrompts = $aiService->generateImagePrompts($validSentences);
        } catch (\Exception $e) {
            Log::error("Failed to generate AI image prompts: " . $e->getMessage());
            // Fallback will happen in the loop below
        }

        // 3. Build Storyboard
        $storyboard = [];
        foreach ($validSentences as $index => $sentence) {

            // Get AI prompt or fall back to regex cleaner
            if (isset($aiPrompts[$index]) && $aiPrompts[$index] !== $sentence) {
                Log::info("Using AI Image Prompt for Scene {$index}: '{$aiPrompts[$index]}'");
                $finalPrompt = $aiPrompts[$index];
            } else {
                Log::info("AI Prompt missing/same for Scene {$index}. Using Fallback: '{$this->cleanImagePrompt($sentence)}'");
                $finalPrompt = $this->cleanImagePrompt($sentence);
            }

            $storyboard[] = [
                'narration' => $sentence,
                'image_prompt' => $visualPrefix . $finalPrompt,
            ];
        }

        return array_slice($storyboard, 0, 50);
    }

    /**
     * Cleans up narration text to create better image search prompts.
     * Removes conversational fillers and focuses on nouns/visuals.
     */
    private function cleanImagePrompt($text)
    {
        // 1. Remove common conversational fillers
        $fillers = [
            'so,', 'actually,', 'basically,', 'literally,', 'you see,', 'I mean,',
            'imagine if', 'imagine', 'think about', 'picture this', 'did you know',
            'what if', 'believe it or not', 'in fact', 'interestingly',
            'however', 'moreover', 'furthermore', 'consequently',
            'it turns out', 'as a result', 'in the end',
            'so here is my question', 'so heres my question', 'here is my question', 'heres my question',
            'so ', 'if we '
        ];

        $clean = str_ireplace($fillers, '', $text);

        // 2. Remove non-visual abstract words (basic list)
        // This is a heuristic; for better results we'd need NLP
        $clean = preg_replace('/\b(really|very|just|only|maybe|perhaps|probably)\b/i', '', $clean);

        // 3. Remove punctuation that might confuse search
        $clean = preg_replace('/[?!.,;:"\']/', '', $clean);

        // 4. Clean up extra spaces
        $clean = trim(preg_replace('/\s+/', ' ', $clean));

        // 5. If result is too short, fall back to original (minus basic punctuation)
        if (strlen($clean) < 5) {
            return trim(preg_replace('/[?!.,;:"\']/', '', $text));
        }

        return $clean;
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
        $tempFile = storage_path('app/temp_input_' . $this->story->id . '_' . time() . '.json');
        file_put_contents($tempFile, $jsonInput);

        $pythonPath = base_path('ai_worker/.venv/bin/python');
        $pythonScript = base_path('ai_worker/worker.py');

        $process = new Process([$pythonPath, $pythonScript, $tempFile], null, null, null);
        $process->setTimeout(3600); // 60 minutes - increased from 30 minutes
        $process->setIdleTimeout(1800); // 30 minutes idle timeout
        $process->setWorkingDirectory(base_path('ai_worker'));

        try {
            $process->run();

            if (!$process->isSuccessful()) {
                throw new ProcessFailedException($process);
            }

            $outputRaw = $process->getOutput();
            Log::info('AI Worker Raw Output: ' . $outputRaw);

            $errorOutput = $process->getErrorOutput();
            if (!empty($errorOutput)) {
                Log::warning('AI Worker Error Output: ' . $errorOutput);
            }

            $output = null;
            if (preg_match('/\{.*"video_path":.*\}/s', $outputRaw, $matches)) {
                $output = json_decode($matches[0], true);
            } else {
                $output = json_decode($outputRaw, true);
            }

            if (!is_array($output) || !isset($output['video_path'])) {
                throw new \Exception("AI Worker failed to return video path. Output: " . $outputRaw . " | Error Output: " . $errorOutput);
            }

            $fullPath = $output['video_path'];
            $storagePrefix = storage_path('app/public/');

            if (is_file($fullPath)) {
                $relativePath = str_replace($storagePrefix, '', $fullPath);
                $this->story->update([
                    'video_path' => $relativePath
                ]);
            } else {
                throw new \Exception("AI Worker reported success but video file not found at: " . $fullPath);
            }
        } catch (ProcessFailedException $e) {
            $errorOutput = $process->getErrorOutput();
            $exitCode = $process->getExitCode();
            Log::error("AI Worker Process Failed. Exit Code: {$exitCode}. Error: " . $errorOutput);
            throw new \Exception("AI Worker process failed with exit code {$exitCode}: " . $errorOutput);
        } finally {
            if (file_exists($tempFile)) {
                unlink($tempFile);
            }
        }
    }
}
