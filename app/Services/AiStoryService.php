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

    public function generateTopic(string $channelContext): string
    {
        $prompt = "Based on this YouTube channel description, generate ONE specific, mind-blowing science topic for a 60-second video.
        Only return the topic name, nothing else.

        Channel Context:
        {$channelContext}";

        try {
            $response = Http::withHeaders([
                'Authorization' => 'Bearer ' . $this->apiKey,
                'Content-Type' => 'application/json',
            ])->post($this->baseUrl, [
                'model' => $this->model,
                'messages' => [
                    ['role' => 'system', 'content' => 'You are a creative YouTube content strategist.'],
                    ['role' => 'user', 'content' => $prompt]
                ],
                'temperature' => 0.9,
            ]);

            if ($response->failed()) {
                throw new \Exception("Failed to generate topic");
            }

            $data = $response->json();
            return trim($data['choices'][0]['message']['content'], '" ');
        } catch (\Exception $e) {
            Log::error('Topic generation failed: ' . $e->getMessage());
            return "Black holes and the event horizon"; // Fallback
        }
    }

    public function generateStory(string $topic = null, string $style = 'science_short'): array
    {
        // Add more variability to the system prompt
        $randomStyles = ['cinematic', 'educational', 'thrilling', 'curious', 'mind-blowing', 'scientific', 'narrative'];
        $selectedStyle = $randomStyles[array_rand($randomStyles)];

        if ($style === 'science_short') {
            $prompt = "Write a fast-paced, {$selectedStyle} science script for a 60-second YouTube Short.
            The script should be approximately 130-150 words to fit within 60 seconds when spoken.
            Use a 'hook -> explanation -> mind-blowing fact' structure.
            The tone should be enthusiastic, professional, and easy to understand.";
        } else {
            $prompt = "Write a short, engaging, and {$selectedStyle} story that would make a 2.5 minute video.
            The story should be approximately 350-400 words.
            Focus on vivid descriptions and a clear narrative arc (beginning, middle, end).";
        }

        if ($topic) {
            $prompt .= " The topic is: {$topic}.";
        } else {
            $scienceTopics = [
                "The secret life of mushrooms and their fungal network",
                "How time dilation works near a black hole",
                "The possibility of life on Europa, Jupiter's moon",
                "Quantum entanglement explained simply",
                "The engineering marvel of the James Webb Space Telescope",
                "Why the ocean is still 95% unexplored",
                "The future of CRISPR and gene editing",
                "How bees communicate through the waggle dance",
                "The mystery of dark matter in the universe",
                "How the human brain stores memories",
                "The physics of a supernova",
                "Can we survive on Mars?",
                "The hidden world of tardigrades",
                "How artificial intelligence is evolving",
                "The science of dreams"
            ];
            $randomTopic = $scienceTopics[array_rand($scienceTopics)];
            $prompt .= " Choose an interesting and cinematic topic. You could talk about something like: {$randomTopic}. BUT DO NOT USE 'The Quantum Echo' as a title or theme.";
        }

        $wordCount = ($style === 'science_short') ? '130-150 words' : '350-400 words';

        $prompt .= "\n\nFormat your response as a JSON object with the following fields:
        'title': A short catchy title for the story. MUST NOT BE 'The Quantum Echo'.
        'content': The full story text ({$wordCount}).
        'youtube_title': A viral-style YouTube title (max 100 chars).
        'youtube_description': A professional YouTube description including a summary and hashtags.
        'youtube_tags': A comma-separated string of 10-15 relevant keywords.

        Unique Seed: " . bin2hex(random_bytes(16)) . "
        Current Microtime: " . microtime(true);

        try {
            $payload = [
                'model' => $this->model,
                'messages' => [
                    [
                        'role' => 'system',
                        'content' => 'You are a professional screenwriter and storyteller. You always output valid JSON. Be creative and unique with every response.'
                    ],
                    [
                        'role' => 'user',
                        'content' => $prompt . "\n\nIMPORTANT: Ensure this content is completely different from any previous generations. Explore a unique angle or a surprising fact."
                    ]
                ],
                'temperature' => 0.9,
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
                'youtube_title' => $content['youtube_title'] ?? '',
                'youtube_description' => $content['youtube_description'] ?? '',
                'youtube_tags' => $content['youtube_tags'] ?? '',
                'provider' => $this->provider
            ];
        } catch (\Exception $e) {
            Log::error('AI Story Generation failed: ' . $e->getMessage());
            throw $e;
        }
    }
}
