<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\StoryController;

Route::post('/stories', [StoryController::class, 'store']);
Route::post('/stories/generate', [StoryController::class, 'generate']);
Route::get('/stories/{story}', [StoryController::class, 'show']);
Route::get('/stories', [StoryController::class, 'index']);
