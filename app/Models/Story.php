<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Story extends Model
{
    protected $fillable = [
        'title',
        'content',
        'status',
        'video_path',
        'aspect_ratio',
        'youtube_title',
        'youtube_description',
        'youtube_tags',
        'youtube_video_id',
        'is_uploaded_to_youtube',
        'youtube_upload_status'
    ];

    public function scenes()
    {
        return $this->hasMany(Scene::class)->orderBy('order');
    }
}
