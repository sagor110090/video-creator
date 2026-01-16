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

            'bollywood_masala' => "Generate ONE trending Bollywood or Indian Celebrity topic. Today's date is {$currentDate}.
            - Focus on: Top stars (SRK, Salman, Deepika, Alia), major movie releases, or viral Indian pop culture moments.
            - Examples: 'Pathaan Box Office Records', 'Alia Bhatt New Movie', 'Virat Kohli News'.
            - Ensure the topic is fresh and highly relevant.
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
                'bollywood_masala' => 'SRK New Movie',
                'trade_wave' => 'Bitcoin Update',
                'story' => 'The Hidden Library'
            ];
            return $fallbacks[$style] ?? 'Interesting Story';
        }
    }

    public function generateStory(string $topic = null, string $style = 'story', string $aspectRatio = '16:9', string $talkingStyle = 'none'): array
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
            'bollywood_masala' => [
                'name' => 'Bollywood',
                'instruction' => "Write a high-energy, 'masala' Bollywood news script for a {$duration} in PURE HINDI (Devanagari Script). {$randomPerspective}
                - LANGUAGE: HINDI (Written in Devanagari script: 'नमस्ते, आज हम बात करेंगे...').
                - Word count: {$wordCountRange} words.
                - Start with 'अरे सुनो! तुम्हें पता है क्या हुआ?' or 'भाई, यह क्या हो गया!'
                - Use Bollywood slang naturally (धमाल, ब्लॉकबस्टर, सीन, बवाल).
                - Make it feel like a chat with a filmy friend.
                - Focus on specific details, box office numbers, and spicy rumors.
                - End with 'तुम्हारा क्या ख्याल है? कमेंट्स में बताओ!'",
                'structure' => "Breaking News (Dhamaka) -> The Juicy Details (Masala) -> Fan Reactions (Public Ka Mood) -> Your Hot Take -> Engagement",
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

        // TALKING STYLE PATTERNS - Each has completely unique structure and opening
        $talkingStylePatterns = [
            'none' => [
                'opening' => '',
                'structure' => $currentStyle['structure'],
                'tone' => 'Follow the base style instructions exactly.',
            ],
            'vlog' => [
                'opening' => "MANDATORY FIRST WORDS: 'Okay, we NEED to talk about...' (exactly these words, no variations). Example: 'Okay, we NEED to talk about Taylor Swift's new album.'",
                'structure' => "Hook announcement → Shock/reaction → Behind-the-scenes research → Fan/audience perspective → Personal opinion → Call to action",
                'tone' => "Casual, conversational, energetic. Use phrases like: 'I'm shook', 'wait, hold on', 'the tea is hot', 'living for this', 'trust me on this', 'the crazy part is'. Make it feel like you FaceTiming a best friend.",
            ],
            'reaction' => [
                'opening' => "MANDATORY FIRST WORDS: Either 'WAIT. Hold on a second.' OR 'Okay, stop everything.' followed immediately by 'Did you see this?!'. Example: 'WAIT. Hold on a second. Did you see this?!'",
                'structure' => "Immediate shock → What happened → First thoughts → Emotional reaction → Breaking down the details → Final reaction",
                'tone' => "High energy, shocked, authentic. Use: 'no way no way no way', 'I literally can't', 'this is insane', 'I'm screaming', 'you won't believe this'. React as if seeing it for the first time right now.",
            ],
            'storytime' => [
                'opening' => "MANDATORY FIRST WORDS: Either 'Okay so storytime...' OR 'So this actually happened...' (exactly these phrases). Example: 'Okay so storytime... I was at the concert when...'",
                'structure' => "Setting the scene → The event → The drama/twist → What happened next → The resolution → Lesson/takeaway",
                'tone' => "Narrative, detailed, engaging. Use: 'let me tell you exactly what went down', 'and get this', 'the craziest part', 'so you're not gonna believe'. Tell it like a real story with dialogue and sensory details.",
            ],
            'opinion' => [
                'opening' => "MANDATORY FIRST WORDS: Either 'Okay, I need to say something about...' OR 'Here's my take on...' (exactly these phrases). Example: 'Okay, I need to say something about this new movie.'",
                'structure' => "Bold opinion → Your reasoning → Addressing counterarguments → Why you're right → Strong closing stance",
                'tone' => "Confident, unapologetic, strong stance. Use: 'honestly', 'I don't care who gets offended', 'here's the thing', 'people might say', 'but let me explain'. Make it a hot take, not neutral.",
            ],
            'educational' => [
                'opening' => "MANDATORY FIRST WORDS: Either 'Alright, so you've probably heard about...' OR 'Let me break this down for you...' (exactly these phrases). Example: 'Alright, so you've probably heard about Bitcoin ETFs.'",
                'structure' => "What people think → What's actually true → Simple explanation → Real-world example → Key takeaway",
                'tone' => "Clear, simple, teacher-like but casual. Use: 'think of it like', 'basically', 'the bottom line is', 'here's what you need to know', 'imagine if'. Break complex things into simple terms.",
            ],
        ];

        // Override Talking Style Patterns for Bollywood Masala (Hinglish)
        if ($style === 'bollywood_masala') {
            $talkingStylePatterns['vlog']['opening'] = "MANDATORY FIRST WORDS: 'अरे सुनो! तुम्हें पता है क्या हुआ?' (Use exactly this). Example: 'अरे सुनो! तुम्हें पता है क्या हुआ रणवीर के साथ?'";
            $talkingStylePatterns['vlog']['tone'] = "Casual, conversational Hindi (Devanagari). Use phrases like: 'यार, मैं तो हिल गया', 'भाई, सीन सेट है', 'मतलब कुछ भी हो रहा है'. Make it feel like a filmy gossip session.";

            $talkingStylePatterns['reaction']['opening'] = "MANDATORY FIRST WORDS: 'ओए होए! यह क्या देख लिया मैंने?!' OR 'रुको रुको! सच में?!'. Example: 'ओए होए! यह क्या देख लिया मैंने?!'";
            $talkingStylePatterns['reaction']['tone'] = "High energy, shocked, filmy drama. Use: 'भाई साहब!', 'उफ्फ, यह तो नेक्स्ट लेवल है', 'कसम से, मज़ा आ गया'. React like a true Bollywood fan.";

            $talkingStylePatterns['storytime']['opening'] = "MANDATORY FIRST WORDS: 'सुनो, एक किस्सा सुनाता हूँ...' OR 'भाई, एक ज़बरदस्त बात बताता हूँ...'.";
            $talkingStylePatterns['storytime']['tone'] = "Narrative, masala style. Use: 'कहानी में ट्विस्ट तब आया जब...', 'और फिर जो हुआ...', 'तुम मानोगे नहीं'.";

            $talkingStylePatterns['opinion']['opening'] = "MANDATORY FIRST WORDS: 'मेरी बात लिख के ले लो...' OR 'सच बोलूँ तो...'.";
            $talkingStylePatterns['opinion']['tone'] = "Confident, dabangg style. Use: 'दुनिया कुछ भी बोले', 'अपना तो सीधा हिसाब है'.";

            $talkingStylePatterns['educational']['opening'] = "MANDATORY FIRST WORDS: 'चलो, आज का ज्ञान लेते हैं...' OR 'इसका असली सच क्या है...'.";
            $talkingStylePatterns['educational']['tone'] = "Simple, clear Hindi. Explain like you're talking to a friend at a chai tapri.";
        }

        // Get the talking style pattern
        $talkingPattern = $talkingStylePatterns[$talkingStyle] ?? $talkingStylePatterns['none'];

        // Build the prompt based on talking style
        $commonRules = "

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
        - FORMAT: Conversational, rhythmic, and engaging.";

        if ($talkingStyle === 'none') {
            // Use original base style when talking style is none
            $prompt = "You are a master scriptwriter for YouTube. Write a script for a {$duration} about: '{$topic}'.

            STYLE: {$channelName}
             INSTRUCTIONS:
            {$currentStyle['instruction']}

            STRUCTURE:
            {$currentStyle['structure']}
            {$commonRules}

            Topic: {$topic}

            Format your response as a JSON object:
            {
              \"title\": \"A short, punchy 3-5 word title\",
              \"content\": \"The full script text here...\",
              \"youtube_title\": \"A viral, click-worthy YouTube title\",
              \"youtube_description\": \"A description with a summary and hashtags\",
              \"youtube_tags\": \"15 relevant tags separated by commas\"
            }";
        } else {
            // Add explicit language instruction for Bollywood even in Talking Style mode
            $languageInstruction = "";
            if ($style === 'bollywood_masala') {
                $languageInstruction = "LANGUAGE: HINDI (Written in Devanagari script). Use authentic Bollywood slang (e.g., 'धमाल', 'बवाल').";
            }

            // Use unique talking style pattern - COMPLETELY different from base style
            $prompt = "You are a master scriptwriter for YouTube. Write a script for a {$duration} about: '{$topic}'.

            TALKING STYLE: {$talkingStyle} (UPPERCASE - THIS IS CRITICAL)
            {$languageInstruction}

            MANDATORY OPENING (MUST USE EXACTLY):
            {$talkingPattern['opening']}

            STRUCTURE (STRICT - MUST FOLLOW):
            {$talkingPattern['structure']}

            TONE INSTRUCTIONS:
            {$talkingPattern['tone']}

            WORD COUNT: EXACTLY {$wordCountRange} words. No more, no less.

            CRITICAL RULES:
            1. The opening MUST match the talking style exactly. Do not use openings from other styles.
            2. The entire script must follow the {$talkingStyle} pattern - not the base {$channelName} style.
            3. Each talking style has a unique personality - maintain it throughout.
            4. Never mix talking styles (e.g., don't use vlog openings with reaction tone).
            5. The opening is the most important - it MUST start with the exact phrase for {$talkingStyle} style.

            {$commonRules}

            Topic: {$topic}

            Format your response as a JSON object:
            {
              \"title\": \"A short, punchy 3-5 word title\",
              \"content\": \"The full script text here...\",
              \"youtube_title\": \"A viral, click-worthy YouTube title\",
              \"youtube_description\": \"A description with a summary and hashtags\",
              \"youtube_tags\": \"15 relevant tags separated by commas\"
            }";
        }

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

    public function searchNews(string $query, string $style = 'hollywood_hype'): array
    {
        $currentDate = date('Y-m-d');

        // Context-aware prompts based on style
        if ($style === 'trade_wave') {
            $context = "Focus on: stock market movements, crypto prices, economic news, trading opportunities, market analysis, financial reports.";
        } elseif ($style === 'bollywood_masala') {
            $context = "Focus on: Bollywood celebrity gossip, Hindi movie releases, box office numbers, Indian music industry, Mumbai film industry news, viral Indian pop culture.";
        } else {
            $context = "Focus on: celebrity gossip, movie releases, box office news, TV shows, music industry, awards, Hollywood drama, entertainment viral moments.";
        }

        $prompt = "Today is {$currentDate}. Query: '{$query}'.
{$context}

Provide 5 trending news items. Each needs:
- 'title': Catchy headline
- 'snippet': 2-3 sentence summary with specific details

Return JSON array: [{\"title\": \"...\", \"snippet\": \"...\"}, ...]";

        try {
            $payload = [
                'model' => $this->model,
                'messages' => [
                    ['role' => 'system', 'content' => "You are a news API. Return ONLY valid JSON array. No markdown."],
                    ['role' => 'user', 'content' => $prompt]
                ],
                'temperature' => 0.85,
                'max_tokens' => 1500,
            ];

            if ($this->provider === 'groq' || $this->provider === 'deepseek') {
                $payload['response_format'] = ['type' => 'json_object'];
            }

            $response = Http::timeout(45)->withHeaders([
                'Authorization' => 'Bearer ' . $this->apiKey,
                'Content-Type' => 'application/json',
            ])->post($this->baseUrl, $payload);

            if ($response->failed()) {
                Log::error('News API request failed with status: ' . $response->status());
                throw new \Exception("News generation failed");
            }

            $data = $response->json();
            $rawContent = $data['choices'][0]['message']['content'];
            Log::info('News search raw response (first 1000 chars): ' . substr($rawContent, 0, 1000));
            $cleanContent = preg_replace('/^```json\s*|\s*```$/', '', trim($rawContent));

            // Parse JSON and handle various response formats from different AI providers
            $decoded = json_decode($cleanContent, true);

            if (json_last_error() !== JSON_ERROR_NONE) {
                Log::warning('News search JSON parse error: ' . json_last_error_msg());
                throw new \Exception('Invalid JSON response from AI');
            }

            // Handle various wrapper keys that AI might use
            $possibleKeys = ['news', 'results', 'items', 'data', 'articles', 'stories'];
            foreach ($possibleKeys as $key) {
                if (isset($decoded[$key]) && is_array($decoded[$key])) {
                    return array_slice($decoded[$key], 0, 5);
                }
            }

            // If it's already a flat array of news items
            if (is_array($decoded) && isset($decoded[0]) && isset($decoded[0]['title'])) {
                return array_slice($decoded, 0, 5);
            }

            // If it's a single news item object, wrap it
            if (isset($decoded['title']) && isset($decoded['snippet'])) {
                return [$decoded];
            }

            Log::warning('Unexpected news response format: ' . substr($cleanContent, 0, 500));
            throw new \Exception('Unexpected response format from AI');

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
