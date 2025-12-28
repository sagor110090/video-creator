<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Scene extends Model
{
    protected $fillable = [
        'story_id',
        'order',
        'narration',
        'image_prompt',
        'image_path',
        'audio_path'
    ];

    public function story()
    {
        return $this->belongsTo(Story::class);
    }
}
