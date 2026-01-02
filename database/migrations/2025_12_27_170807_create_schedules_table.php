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
        Schema::create('schedules', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->string('style');
            $table->string('aspect_ratio');
            $table->integer('videos_per_day');
            $table->string('timezone')->default('UTC');
            $table->json('upload_times');
            $table->boolean('is_active')->default(true);
            $table->foreignId('youtube_token_id')->nullable()->constrained('youtube_tokens')->onDelete('set null');
            $table->text('prompt_template')->nullable();
            $table->json('last_generated_dates')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('schedules');
    }
};
