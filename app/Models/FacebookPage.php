<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class FacebookPage extends Model
{
    protected $fillable = [
        'user_id',
        'page_id',
        'name',
        'access_token',
        'category',
        'picture_url',
    ];

    protected $hidden = [
        'access_token',
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
