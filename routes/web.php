<?php

use Illuminate\Support\Facades\Route;

use App\Http\Controllers\YouTubeController;

use Inertia\Inertia;

Route::get('/', function () {
    return Inertia::render('Welcome');
});

Route::get('/youtube/auth', [YouTubeController::class, 'auth'])->name('youtube.auth');
Route::get('/youtube/callback', [YouTubeController::class, 'callback'])->name('youtube.callback');
Route::get('/youtube/reconnect/{id}', [YouTubeController::class, 'reconnect'])->name('youtube.reconnect');
Route::get('/youtube/channels', function () {
    return Inertia::render('YouTubeChannels');
})->name('youtube.channels');

Route::get('/statistics', function () {
    return Inertia::render('Statistics');
})->name('statistics');



Route::get('/videos/{path}', function ($path) {
    $fullPath = storage_path('app/public/videos/' . $path);

    if (!file_exists($fullPath)) {
        abort(404);
    }

    return response()->file($fullPath, [
        'Content-Type' => 'video/mp4',
        'Accept-Ranges' => 'bytes',
    ]);
})->where('path', '.*')->name('videos.stream');
