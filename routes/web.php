<?php

use Illuminate\Support\Facades\Route;

use App\Http\Controllers\YouTubeController;

Route::get('/', function () {
    return view('welcome');
});

Route::get('/youtube/auth', [YouTubeController::class, 'auth'])->name('youtube.auth');
Route::get('/youtube/callback', [YouTubeController::class, 'callback'])->name('youtube.callback');
