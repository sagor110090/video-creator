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

    public function generateTopic(string $channelContext, string $style = 'story'): string
    {
        $stylePrompts = [
            'science_short' => "Generate ONE specific, high-interest science or technology topic.
            - Focus on: Astrophysics, Quantum Physics, Deep Sea, AI, or Future Tech.
            - Examples: 'The James Webb Space Telescope', 'Quantum Entanglement', 'Mariana Trench Secrets'.
            - Return ONLY the topic name (2-5 words). No punctuation.",

            'hollywood_hype' => "Generate ONE trending Hollywood or Celebrity topic.
            - Focus on: A-list stars, major movie releases, or viral pop culture moments.
            - Examples: 'Dakota Johnson Movie Rumors', 'Oscars Best Picture Controversy', 'Celebrity Fashion Trends'.
            - Return ONLY the topic name (2-5 words). No punctuation.",

            'trade_wave' => "Generate ONE high-impact Trading or Finance topic.
            - Focus on: Bitcoin/Crypto, S&P 500, Tech Stocks, or Global Economy.
            - Examples: 'Bitcoin Spot ETF Impact', 'AI Stock Market Rally', 'Interest Rate Decisions'.
            - Return ONLY the topic name (2-5 words). No punctuation.",

            'story' => "Generate ONE intriguing story concept.
            - Focus on: Mystery, Adventure, Sci-Fi, or Historical Secret.
            - Examples: 'The Lost City of Z', 'Time Travel Paradox', 'The Whispering Woods'.
            - Return ONLY the topic name (2-5 words). No punctuation."
        ];

        $prompt = $stylePrompts[$style] ?? $stylePrompts['story'];
        $prompt .= "\n\nChannel Context: {$channelContext}";

        try {
            $response = Http::withHeaders([
                'Authorization' => 'Bearer ' . $this->apiKey,
                'Content-Type' => 'application/json',
            ])->post($this->baseUrl, [
                'model' => $this->model,
                'messages' => [
                    ['role' => 'system', 'content' => 'You are a content researcher. Output ONLY the topic name.'],
                    ['role' => 'user', 'content' => $prompt]
                ],
                'temperature' => 0.7,
            ]);

            if ($response->failed()) throw new \Exception("Topic generation failed");

            $data = $response->json();
            return trim($data['choices'][0]['message']['content'], '" ');
        } catch (\Exception $e) {
            Log::error('Topic generation failed: ' . $e->getMessage());
            $fallbacks = [
                'science_short' => 'Black Holes',
                'hollywood_hype' => 'Celebrity News',
                'trade_wave' => 'Bitcoin Update',
                'story' => 'The Hidden Library'
            ];
            return $fallbacks[$style] ?? 'Interesting Story';
        }
    }

    public function generateStory(string $topic = null, string $style = 'story', string $aspectRatio = '16:9'): array
    {
        $isShorts = $aspectRatio === '9:16';

        // Define word counts and durations based on format
        $wordCountRange = $isShorts ? '140-160' : '500-600';
        $duration = $isShorts ? '60-second vertical Short' : '3-4 minute landscape video';

        // Add a "Random Perspective" to ensure uniqueness for YouTube monetization
        $perspectives = [
            "Focus on the hidden secrets and unknown facts that most people miss.",
            "Analyze the future implications and what this means for the next generation.",
            "Tell it from the perspective of an expert insider with behind-the-scenes knowledge.",
            "Make it slightly controversial and challenge the popular mainstream opinion.",
            "Focus on the emotional human impact and personal stories related to this.",
            "Break it down for a complete beginner using simple but powerful analogies."
        ];
        $randomPerspective = $perspectives[array_rand($perspectives)];

        $stylePrompts = [
            'science_short' => [
                'name' => '60s Lab',
                'instruction' => "Write a fast-paced, mind-blowing science script for a {$duration}. {$randomPerspective}
                - Word count: {$wordCountRange} words.
                - Start with a hook that challenges common knowledge.
                - Use 'Did you know...' or 'Imagine if...'
                - Explain complex concepts using simple, punchy analogies.
                - End with a thought-provoking question about the future.",
                'structure' => "Hook -> The Mystery -> The Science -> The 'Wow' Factor -> Future Question",
            ],
            'hollywood_hype' => [
                'name' => 'Hollywood',
                'instruction' => "Write a high-energy, 'spilling the tea' celebrity news script for a {$duration}. {$randomPerspective}
                - Word count: {$wordCountRange} words.
                - Start with 'Okay, we NEED to talk about...' or 'Y'all, did you see this?'
                - Use internet slang naturally (tea, shook, living for it, iconic).
                - Make it feel like a FaceTime call with a best friend.
                - Focus on specific details, fan reactions, and rumors.
                - End with 'What do you guys think? Let me know in the comments!'",
                'structure' => "Breaking News -> The Juicy Details -> Fan Reactions -> Your Hot Take -> Engagement",
            ],
            'trade_wave' => [
                'name' => 'TradeWave',
                'instruction' => "Write a sharp, professional yet accessible market analysis script for a {$duration}. {$randomPerspective}
                - Word count: {$wordCountRange} words.
                - Start with 'The markets are moving, and here's why...'
                - Use trader terminology (bullish, resistance, liquidity, breakout) but explain it simply.
                - Provide actionable insights or things to watch.
                - Mention specific tickers or coins if relevant.
                - End with a disclaimer and a call to watch the charts.",
                'structure' => "Market State -> Key Data/Chart Pattern -> Why it Matters -> What to Watch -> Disclaimer",
            ],
            'story' => [
                'name' => 'General Story',
                'instruction' => "Write a compelling, immersive narrative script for a {$duration}. {$randomPerspective}
                - Word count: {$wordCountRange} words.
                - Start in the middle of the action.
                - Use vivid sensory details (smell, sound, feeling).
                - Build tension and have a clear emotional payoff.
                - Use natural, conversational storytelling like you're around a campfire.
                - End with a thought-provoking resolution.",
                'structure' => "The Hook -> Building Tension -> The Climax -> The Twist/Reveal -> Resolution",
            ]
        ];

        $currentStyle = $stylePrompts[$style] ?? $stylePrompts['story'];
        $channelName = $currentStyle['name'];

        $prompt = "You are a master scriptwriter for YouTube. Write a script for a {$duration} about: '{$topic}'.

        STYLE: {$channelName}
        INSTRUCTIONS:
        {$currentStyle['instruction']}

        STRUCTURE:
        {$currentStyle['structure']}

        THE '70 RULE' FOR YPP APPROVAL (CRITICAL):
        - UNIQUE ANGLE: Do not just state facts. Include a strong personal opinion, a witty joke, or a non-mainstream theory related to the topic.
        - HUMAN PROOF: At least once in the script, include a 'Researcher's Insight' phrase like: \"When I was researching this for {$channelName}, I was actually shocked to find...\" or \"I spent hours digging into this, and the thing that really got me was...\" or \"In my opinion, this is exactly why...\". This proves a human did the research.
        - PERSONALITY: Inject a distinct 'creator' personality. Use phrases like \"Trust me on this,\" or \"I know what you're thinking, but hear me out.\"

        CRITICAL RULES FOR HUMAN-LIKE WRITING:
        - TONE: 100% human-like. Use contractions (it's, can't, won't).
        - VOCABULARY: Use simple, everyday words. Avoid complex AI-sounding words like 'delve', 'unleash', 'uncover', 'comprehensive', 'testament', 'vibrant', 'embark'.
        - NO ROBOT TALK: NEVER use phrases like 'In this video', 'Welcome back', 'Let's dive in', 'Today we are going to', 'In conclusion', 'Furthermore', 'Moreover'.
        - AUTHENTICITY: Write as if you're speaking to a friend. Use occasional filler words like 'so', 'actually', 'you see', 'the thing is'.
        - VARIATION: Vary sentence length. Some short. Some a bit longer. Use fragments for emphasis.
        - LENGTH: EXACTLY {$wordCountRange} words. Do not be shorter or longer.
        - FORMAT: Conversational, rhythmic, and engaging.

        Topic: {$topic}

        Format your response as a JSON object:
        {
          \"title\": \"A short, punchy 3-5 word title\",
          \"content\": \"The full script text here...\",
          \"youtube_title\": \"A viral, click-worthy YouTube title\",
          \"youtube_description\": \"A description with a summary and hashtags\",
          \"youtube_tags\": \"15 relevant tags separated by commas\"
        }";

        try {
            $systemMessage = "You are an expert human content creator. You write scripts that sound exactly like a real person talking, not an AI.
            Your writing is authentic, conversational, and completely avoids all AI tropes, clichés, and overused AI vocabulary.
            You use natural speech patterns, contractions, and a relaxed, engaging tone.
            You always output valid JSON.";

            $payload = [
                'model' => $this->model,
                'messages' => [
                    ['role' => 'system', 'content' => $systemMessage],
                    ['role' => 'user', 'content' => $prompt]
                ],
                'temperature' => 0.85,
            ];

            if ($this->provider === 'groq' || $this->provider === 'deepseek') {
                $payload['response_format'] = ['type' => 'json_object'];
            }

            $response = Http::withHeaders([
                'Authorization' => 'Bearer ' . $this->apiKey,
                'Content-Type' => 'application/json',
            ])->post($this->baseUrl, $payload);

            if ($response->failed()) {
                throw new \Exception("AI Generation failed: " . $response->body());
            }

            $data = $response->json();
            $content = json_decode($data['choices'][0]['message']['content'], true);

            return [
                'title' => $content['title'] ?? $topic,
                'content' => $content['content'] ?? '',
                'youtube_title' => $content['youtube_title'] ?? $content['title'],
                'youtube_description' => $content['youtube_description'] ?? '',
                'youtube_tags' => $content['youtube_tags'] ?? '',
                'provider' => $this->provider
            ];
        } catch (\Exception $e) {
            Log::error('AI Story Generation failed: ' . $e->getMessage());
            throw $e;
        }
    }

    public function generateMetadata(string $content): array
    {
        $prompt = "Generate viral YouTube metadata for the following video script.

        SCRIPT:
        {$content}

        IMPORTANT FOR MONETIZATION:
        - Include a professional AI Disclosure in the description (e.g., 'This video features AI-enhanced narration and visuals to bring you a more immersive experience.').
        - Ensure the title is click-worthy but not 'clickbait' that violates YouTube policies.

        Format your response as a JSON object:
        {
          \"youtube_title\": \"A viral, click-worthy YouTube title\",
          \"youtube_description\": \"A description with a summary, hashtags, and the required AI disclosure\",
          \"youtube_tags\": \"15 relevant tags separated by commas\"
        }";

        try {
            $payload = [
                'model' => $this->model,
                'messages' => [
                    ['role' => 'system', 'content' => 'You are a YouTube SEO expert. Output ONLY valid JSON.'],
                    ['role' => 'user', 'content' => $prompt]
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

            if ($response->failed()) throw new \Exception("Metadata generation failed");

            $data = $response->json();
            return json_decode($data['choices'][0]['message']['content'], true);
        } catch (\Exception $e) {
            Log::error('Metadata generation failed: ' . $e->getMessage());
            return [
                'youtube_title' => 'Amazing Story',
                'youtube_description' => 'Check out this amazing AI-generated story!',
                'youtube_tags' => 'ai, story, animation'
            ];
        }
    }

    public function searchNews(string $query): array
    {
        $prompt = "Act as a news search engine. For the query: '{$query}', provide 3 realistic and recent-sounding news snippets.
        If the query is about Hollywood/Entertainment, focus on relevant celebrities, movies, shows, and entertainment industry news.
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
                ['title' => "Breaking: Major Film Announced", 'snippet' => "A highly anticipated project has been officially confirmed, featuring top talent from across the industry."],
                ['title' => "Celebrity News Update", 'snippet' => "The entertainment world is buzzing with the latest developments in film and television."],
                ['title' => "Box Office Records Shattered", 'snippet' => "The latest blockbuster has exceeded all expectations, setting new records for weekend earnings."]
            ];
        }
    }

    public function generateImagePrompts(array $narrations): array
    {
        // Chunk narrations to avoid token limits (max 20 at a time)
        $chunks = array_chunk($narrations, 20);
        $allPrompts = [];

        foreach ($chunks as $chunk) {
            $prompt = "You are a visual director for a video production.
            For each of the following narration segments, generate a precise, high-quality image search query.
            - The query will be used to search for stock footage/photos (Pexels, Unsplash).
            - Extract the main visual subject.
            - Focus on nouns, setting, and action.
            - REMOVE conversational filler (e.g. 'Imagine if', 'So', 'Basically').
            - If the text is abstract, provide a metaphorical visual (e.g. 'Stock market crash' -> 'Red graph arrow going down').
            - Output specific keywords (e.g. 'Golden retriever running grass' instead of 'A dog running').

            INPUT NARRATIONS:
            " . json_encode($chunk) . "

            Format your response as a JSON object where keys are the indices (0, 1, 2...) matching the input array order, and values are the search prompts.
            Example:
            {
                \"0\": \"futuristic city skyline night\",
                \"1\": \"scientist looking at microscope\",
                \"2\": \"bitcoin gold coin pile\"
            }";

            try {
                $payload = [
                    'model' => $this->model,
                    'messages' => [
                        ['role' => 'system', 'content' => 'You are an expert visual prompt engineer. Output ONLY valid JSON.'],
                        ['role' => 'user', 'content' => $prompt]
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
                    throw new \Exception("Image prompt generation failed");
                }

                $data = $response->json();
                $content = $data['choices'][0]['message']['content'];

                // Clean markdown code blocks if present
                $content = preg_replace('/^```json\s*|\s*```$/', '', trim($content));

                $prompts = json_decode($content, true);

                if (is_array($prompts)) {
                    // Use array_values to ensure we just get the list of prompts
                    // However, we need to map them back to the original chunk indices if the LLM messed up keys.
                    // But usually, array_values of the JSON object (if it's an ordered map) works.
                    // Better: iterate through chunk keys.
                    foreach ($chunk as $index => $text) {
                        // The LLM might use the original index or 0-based index relative to chunk
                        // Let's assume 0-based relative to chunk for simplicity in prompt instructions
                        // But wait, array_chunk preserves keys? No, unless true is passed.
                        // Default array_chunk reindexes keys 0..n.
                        $allPrompts[] = $prompts[$index] ?? $prompts[(string)$index] ?? $text;
                    }
                } else {
                    // Fallback: use original text
                    foreach ($chunk as $text) {
                        $allPrompts[] = $text;
                    }
                }

            } catch (\Exception $e) {
                Log::error('Image prompt generation failed: ' . $e->getMessage());
                // Fallback: use original text
                foreach ($chunk as $text) {
                    $allPrompts[] = $text;
                }
            }
        }

        return $allPrompts;
    }
}
