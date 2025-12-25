<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('youtube_tokens', function (Blueprint $table) {
            $table->string('channel_id')->nullable()->after('id');
            $table->string('channel_title')->nullable()->after('channel_id');
            $table->string('channel_thumbnail')->nullable()->after('channel_title');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('youtube_tokens', function (Blueprint $table) {
            $table->dropColumn(['channel_id', 'channel_title', 'channel_thumbnail']);
        });
    }
};
