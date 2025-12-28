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
            $table->unsignedBigInteger('youtube_token_id')->nullable()->after('id');
            $table->foreign('youtube_token_id')->references('id')->on('youtube_tokens')->onDelete('set null');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('stories', function (Blueprint $table) {
            $table->dropForeign(['youtube_token_id']);
            $table->dropColumn('youtube_token_id');
        });
    }
};
