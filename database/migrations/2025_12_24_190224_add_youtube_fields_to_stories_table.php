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
        Schema::table('stories', function (Blueprint $table) {
            $table->string('youtube_title')->nullable();
            $table->text('youtube_description')->nullable();
            $table->text('youtube_tags')->nullable();
            $table->string('youtube_video_id')->nullable();
            $table->boolean('is_uploaded_to_youtube')->default(false);
            $table->string('youtube_upload_status')->nullable(); // pending, uploading, completed, failed
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('stories', function (Blueprint $table) {
            $table->dropColumn([
                'youtube_title',
                'youtube_description',
                'youtube_tags',
                'youtube_video_id',
                'is_uploaded_to_youtube',
                'youtube_upload_status'
            ]);
        });
    }
};
