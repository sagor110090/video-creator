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
        Schema::table('video_schedules', function (Blueprint $table) {
            $table->time('scheduled_time')->after('aspect_ratio');
            $table->date('last_run_at')->nullable()->after('story_id');
            $table->dropColumn('scheduled_at');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('video_schedules', function (Blueprint $table) {
            $table->dateTime('scheduled_at')->nullable();
            $table->dropColumn(['scheduled_time', 'last_run_at']);
        });
    }
};
