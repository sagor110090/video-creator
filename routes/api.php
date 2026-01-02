<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\StoryController;

Route::post('/stories', [StoryController::class, 'store']);
Route::post('/ai/generate-story', [StoryController::class, 'generate']);
Route::post('/ai/search-news', [StoryController::class, 'searchNews']);
Route::patch('/stories/{story}', [StoryController::class, 'update']);
Route::post('/stories/{story}/upload', [StoryController::class, 'uploadToYouTube']);
Route::post('/stories/{story}/generate-metadata', [StoryController::class, 'generateMetadata']);
Route::get('/stories/{story}', [StoryController::class, 'show']);
Route::get('/stories', [StoryController::class, 'index']);
Route::delete('/stories/{story}', [StoryController::class, 'destroy']);
Route::post('/stories/{story}/regenerate', [StoryController::class, 'regenerate']);

Route::get('/youtube/channels', [\App\Http\Controllers\YouTubeController::class, 'channels']);
Route::delete('/youtube/channels/{id}', [\App\Http\Controllers\YouTubeController::class, 'disconnect']);
Route::post('/youtube/refresh/{id}', [\App\Http\Controllers\YouTubeController::class, 'refresh']);

Route::get('/statistics', [\App\Http\Controllers\StatisticsController::class, 'index']);

Route::apiResource('schedules', \App\Http\Controllers\ScheduleController::class);
Route::post('/schedules/{schedule}/generate', [\App\Http\Controllers\ScheduleController::class, 'generateVideo']);
