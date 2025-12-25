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
            $this->apiKey = env('DEEPSEEK_API_KEY');
            $this->baseUrl = 'https://api.deepseek.com/chat/completions';
            $this->model = 'deepseek-chat';
        } else {
            $this->apiKey = env('GROQ_API_KEY');
            $this->baseUrl = 'https://api.groq.com/openai/v1/chat/completions';
            $this->model = 'llama-3.3-70b-versatile';
        }

        if (empty($this->apiKey)) {
            Log::error("AI Story Service: API key for {$this->provider} is missing!");
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
        } elseif ($style === 'hollywood_hype') {
            $prompt = "Write a gossipy, high-energy, and {$selectedStyle} Hollywood news script for a 60-second YouTube Short.
            Focus on the latest celebrity news, specifically regarding stars like Dakota Johnson or Jamie Dornan if mentioned.
            The script should be approximately 130-150 words.
            Use a 'shocking hook -> juicy details -> call to action' structure.
            The tone should be dramatic, exciting, and viral-ready.";
        } elseif ($style === 'trade_wave') {
            $prompt = "Write a professional, high-stakes, and {$selectedStyle} trading and investment script for a 60-second YouTube Short.
            Focus on market updates, crypto trends, stock analysis, or investment ideas.
            The script should be approximately 130-150 words.
            Use a 'market hook -> data analysis -> investment insight' structure.
            The tone should be authoritative, urgent, and insightful.";
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
            $hypeTopics = [
                "Dakota Johnson's latest red carpet look that has everyone talking",
                "Is Jamie Dornan returning for a new thriller?",
                "The Fifty Shades reunion fans are waiting for",
                "Dakota Johnson's secret to her flawless style",
                "Jamie Dornan's transition from model to superstar",
                "The most expensive celebrity homes in Hollywood",
                "Upcoming blockbuster movies in 2026",
                "Celebrity fashion trends that are taking over",
                "The truth behind the latest Hollywood rumors",
                "How stars prepare for the Oscars"
            ];
            $tradeTopics = [
                "Bitcoin's latest price surge and what it means for 2026",
                "The top 3 AI stocks to watch this month",
                "How the Federal Reserve's next move will impact your portfolio",
                "The rise of decentralized finance and its future",
                "Why gold is still the ultimate hedge in a volatile market",
                "Understanding the 'fear and greed' index in crypto",
                "The impact of global trade shifts on emerging markets",
                "Why dividend investing is making a massive comeback",
                "The truth about day trading vs long-term hodling",
                "How to spot the next big tech unicorn before the IPO"
            ];

            if ($style === 'hollywood_hype') {
                $randomTopic = $hypeTopics[array_rand($hypeTopics)];
            } elseif ($style === 'trade_wave') {
                $randomTopic = $tradeTopics[array_rand($tradeTopics)];
            } else {
                $randomTopic = $scienceTopics[array_rand($scienceTopics)];
            }

            $prompt .= " Choose an interesting and cinematic topic. You could talk about something like: {$randomTopic}. BUT DO NOT USE 'The Quantum Echo' as a title or theme.";
        }

        $wordCount = ($style === 'science_short' || $style === 'hollywood_hype' || $style === 'trade_wave') ? '130-150 words' : '350-400 words';

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
                'temperature' => 0.7,
            ];

            if ($this->provider === 'groq' || $this->provider === 'deepseek') {
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

    public function searchNews(string $query): array
    {
        $prompt = "Act as a news search engine. For the query: '{$query}', provide 3 realistic and recent-sounding news snippets.
        If the query is about Hollywood/Entertainment, focus on stars like Dakota Johnson or Jamie Dornan.
        If the query is about Trading/Finance/Market, focus on stocks, crypto, or economic updates.
        Each snippet should have a catchy 'title' and a 'snippet' (summary).
        Ensure the news sounds current and exciting.

        Format your response as a JSON array of objects, like this:
        [
          {\"title\": \"...\", \"snippet\": \"...\"},
          {\"title\": \"...\", \"snippet\": \"...\"},
          {\"title\": \"...\", \"snippet\": \"...\"}
        ]";

        try {
            $payload = [
                'model' => $this->model,
                'messages' => [
                    ['role' => 'system', 'content' => 'You are a real-time news aggregator for entertainment and finance. Output ONLY valid JSON.'],
                    ['role' => 'user', 'content' => $prompt]
                ],
                'temperature' => 0.8,
            ];

            if ($this->provider === 'groq' || $this->provider === 'deepseek') {
                $payload['response_format'] = ['type' => 'json_object'];
            }

            $response = Http::withHeaders([
                'Authorization' => 'Bearer ' . $this->apiKey,
                'Content-Type' => 'application/json',
            ])->post($this->baseUrl, $payload);

            if ($response->failed()) {
                throw new \Exception("News generation failed");
            }

            $data = $response->json();
            $rawContent = $data['choices'][0]['message']['content'];
            $cleanContent = preg_replace('/^```json\s*|\s*```$/', '', trim($rawContent));

            // If it's a single object instead of an array, wrap it
            $decoded = json_decode($cleanContent, true);
            if (isset($decoded['news'])) return $decoded['news'];
            return is_array($decoded) ? $decoded : [$decoded];

        } catch (\Exception $e) {
            Log::error('News simulation failed: ' . $e->getMessage());

            // Fallback based on query keywords
            if (stripos($query, 'crypto') !== false || stripos($query, 'stock') !== false || stripos($query, 'market') !== false || stripos($query, 'bitcoin') !== false) {
                return [
                    ['title' => "Bitcoin Breaks New Resistance", 'snippet' => "Bitcoin has surged past key resistance levels as institutional interest continues to grow."],
                    ['title' => "AI Stocks Rally on Tech Earnings", 'snippet' => "Major tech companies report better-than-expected earnings, sending AI-focused stocks to new highs."],
                    ['title' => "Federal Reserve Holds Rates", 'snippet' => "The Fed decided to keep interest rates steady, sparking a relief rally across global markets."]
                ];
            }

            return [
                ['title' => "Dakota Johnson Spotted in London", 'snippet' => "The star was seen filming her latest project in central London, looking as stylish as ever."],
                ['title' => "Jamie Dornan's New Project Revealed", 'snippet' => "Sources confirm Jamie Dornan has signed on for a high-stakes thriller filming this summer."],
                ['title' => "Fifty Shades Duo Reunite?", 'snippet' => "Rumors are swirling about a potential project featuring both Dakota and Jamie. Fans are ecstatic."]
            ];
        }
    }
}
