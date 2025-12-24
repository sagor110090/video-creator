<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class YoutubeToken extends Model
{
    protected $fillable = [
        'access_token',
        'refresh_token',
        'expires_at'
    ];
}
