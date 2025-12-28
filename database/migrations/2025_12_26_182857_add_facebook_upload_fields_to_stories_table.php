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
            $table->unsignedBigInteger('facebook_page_id')->nullable()->after('youtube_token_id');
            $table->string('facebook_video_id')->nullable()->after('youtube_video_id');
            $table->boolean('is_uploaded_to_facebook')->default(false)->after('is_uploaded_to_youtube');
            $table->string('facebook_upload_status')->nullable()->after('youtube_upload_status');
            $table->text('facebook_error')->nullable()->after('youtube_error');
            
            $table->foreign('facebook_page_id')->references('id')->on('facebook_pages')->onDelete('set null');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('stories', function (Blueprint $table) {
            $table->dropForeign(['facebook_page_id']);
            $table->dropColumn(['facebook_page_id', 'facebook_video_id', 'is_uploaded_to_facebook', 'facebook_upload_status', 'facebook_error']);
        });
    }
};
