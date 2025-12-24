<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Story extends Model
{
    protected $fillable = ['title', 'content', 'status', 'video_path'];

    public function scenes()
    {
        return $this->hasMany(Scene::class)->orderBy('order');
    }
}
