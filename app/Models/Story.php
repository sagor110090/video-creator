<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\Event;
use App\Jobs\ProcessStoryJob;

class Story extends Model
{
    protected $fillable = [
        'title',
        'content',
        'style',
        'talking_style',
        'status',
        'video_path',
        'aspect_ratio',
        'youtube_title',
        'youtube_description',
        'youtube_tags',
        'youtube_video_id',
        'is_uploaded_to_youtube',
        'youtube_upload_status',
        'youtube_token_id',
        'youtube_error',
        'scheduled_for',
        'video_schedule_id',
    ];

    protected $casts = [
        'scheduled_for' => 'datetime',
    ];

    protected $with = ['youtubeChannel'];

    public function scenes()
    {
        return $this->hasMany(Scene::class)->orderBy('order');
    }

    public function videoSchedule()
    {
        return $this->belongsTo(VideoSchedule::class);
    }

    public function youtubeChannel()
    {
        return $this->belongsTo(YoutubeToken::class, 'youtube_token_id');
    }
}
