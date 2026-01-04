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
        Schema::dropIfExists('schedules');

        if (Schema::hasColumn('stories', 'is_from_scheduler')) {
            Schema::table('stories', function (Blueprint $table) {
                $table->dropColumn('is_from_scheduler');
            });
        }
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        if (!Schema::hasTable('schedules')) {
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

        if (!Schema::hasColumn('stories', 'is_from_scheduler')) {
            Schema::table('stories', function (Blueprint $table) {
                $table->boolean('is_from_scheduler')->default(false);
            });
        }
    }
};
