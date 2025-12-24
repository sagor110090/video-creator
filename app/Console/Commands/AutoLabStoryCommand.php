<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Services\AiStoryService;
use Illuminate\Support\Facades\Artisan;

class AutoLabStoryCommand extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'story:auto-lab';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Automatically generates a science topic for The 60s Lab and triggers video creation';

    private $channelDescription = "Welcome to The 60s Lab – Your daily dose of mind-blowing science, delivered in under a minute.

    Ever wondered how black holes work, why the sky is blue, or what happens at the edge of the universe? We break down the most complex mysteries of physics, biology, and technology into fast-paced, 60-second experiments and insights.

    🧪 What we do:
    Mind-bending Space & Physics facts.
    Human Body & Psychology hacks.
    Future Tech & AI updates.
    'Did you know' science secrets.

    Science doesn't have to be boring. We make it fast, visual, and easy to understand.";

    /**
     * Execute the console command.
     */
    public function handle(AiStoryService $aiService)
    {
        $this->info("🧪 Welcome to The 60s Lab Automation!");

        // STEP 1: Generate a topic based on channel context
        $this->info("🤖 Thinking of a mind-blowing science topic...");
        $topic = $aiService->generateTopic($this->channelDescription);
        $this->info("🎯 Today's Topic: {$topic}");

        // STEP 2: Trigger the creation and upload command
        $this->info("🚀 Launching the video creation and upload engine...");

        // We use the existing command we built earlier, but with the science style
        // Note: I'll need to update the main command slightly to support the style parameter
        Artisan::call('story:create-and-upload', [
            'topic' => $topic,
            '--aspect' => '9:16',
            '--style' => 'science_short'
        ], $this->output);

        $this->info("🏁 Automation cycle complete!");
    }
}
