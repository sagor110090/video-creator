<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\StoryController;

Route::post('/stories', [StoryController::class, 'store']);
Route::post('/ai/generate-story', [StoryController::class, 'generate']);
Route::post('/ai/search-news', [StoryController::class, 'searchNews']);
Route::patch('/stories/{story}', [StoryController::class, 'update']);
Route::post('/stories/{story}/upload', [StoryController::class, 'uploadToYouTube']);
Route::post('/stories/{story}/schedule', [StoryController::class, 'schedule']);
Route::post('/stories/{story}/generate-metadata', [StoryController::class, 'generateMetadata']);
Route::get('/stories/{story}', [StoryController::class, 'show']);
Route::get('/stories', [StoryController::class, 'index']);
Route::delete('/stories/{story}', [StoryController::class, 'destroy']);
Route::post('/stories/{story}/regenerate', [StoryController::class, 'regenerate']);

Route::get('/schedules', [\App\Http\Controllers\VideoScheduleController::class, 'index']);
Route::post('/schedules', [\App\Http\Controllers\VideoScheduleController::class, 'store']);
Route::patch('/schedules/{videoSchedule}', [\App\Http\Controllers\VideoScheduleController::class, 'update']);
Route::delete('/schedules/{videoSchedule}', [\App\Http\Controllers\VideoScheduleController::class, 'destroy']);

Route::get('/youtube/channels', [\App\Http\Controllers\YouTubeController::class, 'channels']);
Route::delete('/youtube/channels/{id}', [\App\Http\Controllers\YouTubeController::class, 'disconnect']);
Route::post('/youtube/refresh/{id}', [\App\Http\Controllers\YouTubeController::class, 'refresh']);

Route::get('/statistics', [\App\Http\Controllers\StatisticsController::class, 'index']);
