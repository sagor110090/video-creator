<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class YoutubeToken extends Model
{
    protected $fillable = [
        'channel_id',
        'channel_title',
        'channel_thumbnail',
        'access_token',
        'refresh_token',
        'expires_at'
    ];
}
