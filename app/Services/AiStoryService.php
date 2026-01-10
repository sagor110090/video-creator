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
        $currentDate = date('Y-m-d');
        $stylePrompts = [
            'science_short' => "Generate ONE specific, high-interest science or technology topic. Today's date is {$currentDate}.
            - Focus on: Astrophysics, Quantum Physics, Deep Sea, AI, or Future Tech.
            - Examples: 'The James Webb Space Telescope', 'Quantum Entanglement', 'Mariana Trench Secrets'.
            - Return ONLY the topic name (2-5 words). No punctuation.",

            'hollywood_hype' => "Generate ONE trending Hollywood or Celebrity topic. Today's date is {$currentDate}.
            - Focus on: A-list stars, major movie releases, or viral pop culture moments happening RIGHT NOW.
            - Examples: 'Dakota Johnson Movie Rumors', 'Oscars Best Picture Controversy', 'Celebrity Fashion Trends'.
            - Ensure the topic is fresh and highly relevant to the current week.
            - Return ONLY the topic name (2-5 words). No punctuation.",

            'trade_wave' => "Generate ONE high-impact Trading or Finance topic. Today's date is {$currentDate}.
            - Focus on: Bitcoin/Crypto, S&P 500, Tech Stocks, or Global Economy.
            - Examples: 'Bitcoin Spot ETF Impact', 'AI Stock Market Rally', 'Interest Rate Decisions'.
            - Focus on current market sentiment and breaking financial news.
            - Return ONLY the topic name (2-5 words). No punctuation.",

            'story' => "Generate ONE intriguing story concept.
            - Focus on: Mystery, Adventure, Sci-Fi, or Historical Secret.
            - Examples: 'The Lost City of Z', 'Time Travel Paradox', 'The Whispering Woods'.
            - Return ONLY the topic name (2-5 words). No punctuation."
        ];

        $prompt = $stylePrompts[$style] ?? $stylePrompts['story'];
        $prompt .= "\n\nChannel Context: {$channelContext}";

        try {
            $response = Http::timeout(60)->withHeaders([
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
        set_time_limit(180); // Increase PHP execution time for long story generation
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

            $response = Http::timeout(120)->withHeaders([
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

            $response = Http::timeout(60)->withHeaders([
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
        set_time_limit(120); // Increase PHP execution time for detailed news search
        $currentDate = date('Y-m-d');
        $prompt = "Act as a real-time news search engine. Today's date is {$currentDate}.
        For the query: '{$query}', provide 15 realistic, diverse, and very recent news snippets.
        If the query is about Hollywood/Entertainment, focus on the absolute latest celebrity gossip, movie announcements, box office results, and viral social media moments from the last 24-48 hours.
        If the query is about Trading/Finance/Market, focus on the latest stock movements, crypto price action, or economic breaking news.

        CRITICAL:
        - Ensure the news is different every time this is called by focusing on different sub-topics or recent events.
        - Use a variety of sources (simulated) and perspectives.
        - DO NOT repeat common old news. Look for the 'bleeding edge' of what might be happening NOW.
        - DESCRIPTION LENGTH: Each 'snippet' must be a detailed paragraph (3-5 sentences, approx 60-100 words). It should include specific details, names, numbers, and the context of why this is trending.

        Each snippet should have a catchy 'title' and a 'snippet' (detailed summary).

        Format your response as a JSON array of objects, like this:
        [
          {\"title\": \"...\", \"snippet\": \"...\"},
          ... (up to 15 items)
        ]";

        try {
            $payload = [
                'model' => $this->model,
                'messages' => [
                    ['role' => 'system', 'content' => "You are a real-time news aggregator for entertainment and finance. Today's date is {$currentDate}. Output ONLY valid JSON."],
                    ['role' => 'user', 'content' => $prompt]
                ],
                'temperature' => 0.95, // Even higher temperature for more variety
            ];

            if ($this->provider === 'groq' || $this->provider === 'deepseek') {
                $payload['response_format'] = ['type' => 'json_object'];
            }

            $response = Http::timeout(90)->withHeaders([
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
            if (isset($decoded['news'])) return array_slice($decoded['news'], 0, 15);
            $results = is_array($decoded) ? $decoded : [$decoded];
            return array_slice($results, 0, 15);

        } catch (\Exception $e) {
            Log::error('News simulation failed: ' . $e->getMessage());

            // Fallback based on query keywords
            if (stripos($query, 'crypto') !== false || stripos($query, 'stock') !== false || stripos($query, 'market') !== false || stripos($query, 'bitcoin') !== false) {
                return [
                    [
                        'title' => "Bitcoin Surges Past Key Resistance",
                        'snippet' => "Bitcoin has seen a massive spike in volume today, breaking through major resistance levels at $95,000 as institutional demand peaks. Analysts suggest that the influx of spot ETF inflows is driving the current rally, with several major hedge funds increasing their positions. This move has sparked a broader market recovery, lifting Ethereum and other major altcoins by nearly 10% in just 24 hours."
                    ],
                    [
                        'title' => "AI Tech Stocks Lead Market Rally",
                        'snippet' => "NVIDIA and other AI-focused tech giants are driving the S&P 500 to new record highs today following better-than-expected quarterly earnings. The surge in demand for high-performance computing chips continues to outpace supply, leading to a 5% jump in stock prices across the semiconductor sector. Investors are now closely watching upcoming reports from other big tech firms to see if the AI-driven growth trend is sustainable."
                    ],
                    [
                        'title' => "SEC Issues New Guidance on Digital Assets",
                        'snippet' => "The SEC has released an updated framework for digital asset classification, specifically targeting how decentralized autonomous organizations (DAOs) are regulated. This move has created a ripple effect through the industry, with many developers calling for clearer definitions to avoid potential legal challenges. Major exchanges are already reviewing their listings to ensure compliance with the newly issued guidelines."
                    ],
                    [
                        'title' => "Global Markets React to Inflation Data",
                        'snippet' => "Latest CPI data has come in lower than expected at 3.1%, fueling hopes for a potential interest rate cut by the Federal Reserve in the next quarter. European and Asian markets responded positively to the news, with major indices closing in the green as recession fears begin to subside. Economists warn, however, that wage growth remains a persistent factor that could keep inflation levels volatile in the coming months."
                    ],
                    [
                        'title' => "Ethereum Whale Activity Spikes",
                        'snippet' => "Large Ethereum transactions involving wallets with over 10,000 ETH have increased by 40% in the last 24 hours, suggesting a major institutional move is imminent. Data from on-chain analytics platforms indicates that a significant amount of supply is being moved off exchanges and into cold storage, which typically precedes a price breakout. Retail interest is also beginning to climb as social media mentions of 'ETH 2.0' hit a three-month high."
                    ]
                ];
            }

            return [
                [
                    'title' => "Hollywood Blockbuster Breaks Records",
                    'snippet' => "The latest summer blockbuster has officially crossed the $1 billion mark globally, setting a new industry record for the fastest film to reach this milestone. Driven by an aggressive social media marketing campaign and rave reviews from both critics and audiences, the movie has dominated the box office for three consecutive weeks. Studio executives are already fast-tracking a sequel and exploring potential spin-off series for their streaming platform."
                ],
                [
                    'title' => "A-List Actor Joins Marvel Cinematic Universe",
                    'snippet' => "In a shock announcement during a major fan convention, a legendary Oscar-winning actor has been officially cast in a pivotal role for the upcoming Avengers: Secret Wars. Fans have been speculating about this casting for months, and the reveal has already generated millions of views on social media. The actor is expected to bring a new level of gravitas to the franchise as it prepares for its most ambitious phase yet."
                ],
                [
                    'title' => "Streaming Giant Announces Massive Price Hike",
                    'snippet' => "One of the world's largest streaming platforms has announced a significant increase in subscription costs for its premium tier, effective immediately for new members. The company cites the rising costs of producing original content and a strategic shift towards ad-supported tiers as the primary reasons for the change. Industry analysts expect other major competitors to follow suit as they all prioritize profitability over subscriber growth in the coming year."
                ],
                [
                    'title' => "Celebrity Wedding of the Year",
                    'snippet' => "Two of Hollywood's biggest stars have reportedly tied the knot in an ultra-private, star-studded ceremony at a historic villa in Lake Como, Italy. While no official photos have been released, sources close to the couple describe the event as an elegant affair attended by A-list directors and fellow actors. The news has sent fans into a frenzy, with paparazzi drones reportedly being intercepted near the wedding venue throughout the weekend."
                ],
                [
                    'title' => "Awards Season Predictions Heating Up",
                    'snippet' => "With the first major international film festivals concluding, critics and industry insiders are already narrowing down their frontrunners for the next Academy Awards. A low-budget indie drama from a first-time director has emerged as a surprise contender, earning standing ovations and early buzz for Best Picture. Meanwhile, several big-budget biopics are facing criticism for historical inaccuracies, potentially complicating their path to the Oscars."
                ]
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

                $response = Http::timeout(120)->withHeaders([
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
