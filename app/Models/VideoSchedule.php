<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class VideoSchedule extends Model
{
    protected $fillable = [
        'topic',
        'style',
        'talking_style',
        'aspect_ratio',
        'scheduled_time',
        'youtube_token_id',
        'status',
        'story_id',
        'last_run_at',
        'last_error'
    ];

    protected $casts = [
        'last_run_at' => 'date',
    ];

    public function story()
    {
        return $this->belongsTo(Story::class);
    }

    public function youtubeToken()
    {
        return $this->belongsTo(YoutubeToken::class, 'youtube_token_id');
    }
}
