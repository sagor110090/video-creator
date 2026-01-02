<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Schedule extends Model
{
    protected $fillable = [
        'name',
        'style',
        'aspect_ratio',
        'videos_per_day',
        'timezone',
        'upload_times',
        'is_active',
        'youtube_token_id',
        'prompt_template',
        'last_generated_dates',
    ];

    protected $casts = [
        'upload_times' => 'array',
        'last_generated_dates' => 'array',
        'is_active' => 'boolean',
    ];

    public function youtubeChannel()
    {
        return $this->belongsTo(YoutubeToken::class, 'youtube_token_id');
    }
}
