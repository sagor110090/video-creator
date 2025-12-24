<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class AiStoryService
{
    protected $provider;
    protected $apiKey;
    protected $baseUrl;
    protected $model;

    public function __construct()
    {
        $this->provider = env('AI_STORY_PROVIDER', 'groq');

        if ($this->provider === 'deepseek') {
            $this->apiKey = config('services.deepseek.api_key');
            $this->baseUrl = 'https://api.deepseek.com/v1/chat/completions';
            $this->model = 'deepseek-chat';
        } else {
            $this->apiKey = config('services.groq.api_key');
            $this->baseUrl = 'https://api.groq.com/openai/v1/chat/completions';
            $this->model = 'llama-3.3-70b-versatile';
        }
    }

    public function generateStory(string $topic = null): array
    {
        $prompt = "Write a short, engaging story that would make a 2.5 minute video.
        The story should be approximately 350-400 words.
        Focus on vivid descriptions and a clear narrative arc (beginning, middle, end).";

        if ($topic) {
            $prompt .= " The topic of the story is: {$topic}.";
        } else {
            $prompt .= " Choose an interesting and cinematic topic.";
        }

        $prompt .= "\n\nFormat your response as a JSON object with 'title' and 'content' fields.
        The content should be the full story text.";

        try {
            $payload = [
                'model' => $this->model,
                'messages' => [
                    [
                        'role' => 'system',
                        'content' => 'You are a professional screenwriter and storyteller. You always output valid JSON.'
                    ],
                    [
                        'role' => 'user',
                        'content' => $prompt
                    ]
                ],
                'temperature' => 0.7,
            ];

            // Groq supports response_format, DeepSeek might need it in the prompt or different handling
            if ($this->provider === 'groq') {
                $payload['response_format'] = ['type' => 'json_object'];
            }

            $response = Http::withHeaders([
                'Authorization' => 'Bearer ' . $this->apiKey,
                'Content-Type' => 'application/json',
            ])->post($this->baseUrl, $payload);

            if ($response->failed()) {
                Log::error("{$this->provider} API error: " . $response->body());
                throw new \Exception("Failed to generate story from {$this->provider}");
            }

            $data = $response->json();
            $rawContent = $data['choices'][0]['message']['content'];

            // Clean up potential markdown code blocks if the AI includes them
            $cleanContent = preg_replace('/^```json\s*|\s*```$/', '', trim($rawContent));
            $content = json_decode($cleanContent, true);

            if (json_last_error() !== JSON_ERROR_NONE) {
                Log::error("Failed to decode JSON from {$this->provider}: " . $rawContent);
                throw new \Exception("Invalid JSON response from AI");
            }

            return [
                'title' => $content['title'] ?? 'Generated Story',
                'content' => $content['content'] ?? '',
                'provider' => $this->provider
            ];
        } catch (\Exception $e) {
            Log::error('AI Story Generation failed: ' . $e->getMessage());
            throw $e;
        }
    }
}
