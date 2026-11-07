<?php

namespace App\Jobs;

use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Support\Facades\Log;

class TimeoutProbeJob implements ShouldQueue
{
    use Queueable;

    public function handle(): void
    {
        sleep(65);
        Log::info('TimeoutProbeJob completed after 65 seconds');
    }
}
