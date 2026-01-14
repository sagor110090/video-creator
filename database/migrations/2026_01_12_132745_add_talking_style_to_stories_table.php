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
            $table->string('talking_style')->nullable()->after('style');
        });

        Schema::table('video_schedules', function (Blueprint $table) {
            $table->string('talking_style')->nullable()->after('style');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('stories', function (Blueprint $table) {
            $table->dropColumn('talking_style');
        });

        Schema::table('video_schedules', function (Blueprint $table) {
            $table->dropColumn('talking_style');
        });
    }
};
