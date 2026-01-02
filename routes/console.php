<?php

use Illuminate\Foundation\Inspiring;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Schedule;

Artisan::command('inspire', function () {
    $this->comment(Inspiring::quote());
})->purpose('Display an inspiring quote');

Schedule::command('schedules:process')->everyMinute();

// Delete stories older than 2 days - runs daily
Schedule::call(function () {
    $stories = \App\Models\Story::where('created_at', '<', now()->subDays(2))->get();

    foreach ($stories as $story) {
        // Delete video file if exists
        if ($story->video_path && file_exists(public_path($story->video_path))) {
            unlink(public_path($story->video_path));
        }

        // Delete the story record
        $story->delete();
    }
})->daily();
