<?php

use Illuminate\Support\Facades\Route;

use App\Http\Controllers\YouTubeController;
use App\Http\Controllers\AuthController;
use App\Http\Controllers\FacebookController;

use Inertia\Inertia;

Route::get('/login', [AuthController::class, 'showLogin'])->name('login')->middleware('guest');
Route::post('/login', [AuthController::class, 'login']);
Route::post('/logout', [AuthController::class, 'logout'])->name('logout');

Route::get('/', function () {
    return Inertia::render('Welcome');
})->middleware('auth');

Route::get('/youtube/auth', [YouTubeController::class, 'auth'])->name('youtube.auth')->middleware('auth');
Route::get('/youtube/callback', [YouTubeController::class, 'callback'])->name('youtube.callback')->middleware('auth');

Route::get('/oauth/facebook/auth', [FacebookController::class, 'auth'])->name('facebook.auth')->middleware('auth');
Route::get('/oauth/facebook/callback', [FacebookController::class, 'callback'])->name('facebook.callback')->middleware('auth');

Route::get('/statistics', function () {
    return Inertia::render('Statistics');
})->middleware('auth')->name('statistics');

Route::get('/schedules', function () {
    return Inertia::render('Schedules');
})->middleware('auth')->name('schedules');
