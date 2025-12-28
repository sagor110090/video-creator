<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Schedule extends Model
{
    protected $fillable = [
        'user_id',
        'name',
        'style',
        'aspect_ratio',
        'videos_per_day',
        'timezone',
        'upload_times',
        'is_active',
        'youtube_token_id',
        'facebook_page_id',
        'prompt_template',
        'last_generated_dates',
    ];

    protected $casts = [
        'upload_times' => 'array',
        'last_generated_dates' => 'array',
        'is_active' => 'boolean',
    ];

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function youtubeChannel()
    {
        return $this->belongsTo(YoutubeToken::class, 'youtube_token_id');
    }

    public function facebookPage()
    {
        return $this->belongsTo(FacebookPage::class, 'facebook_page_id');
    }
}
