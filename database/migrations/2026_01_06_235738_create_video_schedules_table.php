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
        Schema::create('video_schedules', function (Blueprint $table) {
            $table->id();
            $table->string('topic');
            $table->string('style')->default('story');
            $table->string('aspect_ratio')->default('16:9');
            $table->dateTime('scheduled_at');
            $table->foreignId('youtube_token_id')->nullable()->constrained('youtube_tokens')->nullOnDelete();
            $table->string('status')->default('pending'); // pending, processing, completed, failed
            $table->foreignId('story_id')->nullable()->constrained('stories')->nullOnDelete();
            $table->text('last_error')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('video_schedules');
    }
};
