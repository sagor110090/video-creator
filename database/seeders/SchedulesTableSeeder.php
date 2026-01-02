<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class SchedulesTableSeeder extends Seeder
{

    /**
     * Auto generated seed file
     *
     * @return void
     */
    public function run()
    {


        \DB::table('schedules')->delete();

        \DB::table('schedules')->insert(array (
            0 =>
            array (
                'id' => 1,
                'user_id' => 1,
                'name' => 'The 60s Lab',
                'style' => 'science_short',
                'aspect_ratio' => '9:16',
                'videos_per_day' => 6,
                'timezone' => 'Asia/Dhaka',
                'upload_times' => '["00:00","02:00","12:00","15:00","18:00","21:00"]',
                'is_active' => 1,
                'youtube_token_id' => 1,
                'facebook_page_id' => 4,
            'prompt_template' => 'Explain one mind-blowing astrophysics concept (black holes, neutron stars, dark matter, or time dilation) in a simple and engaging way for a general audience.',
                'last_generated_dates' => '{"Asia\\/Dhaka_2025-12-27":[34,35],"Asia\\/Dhaka_2025-12-27_slot_1":[46],"Asia\\/Dhaka_2025-12-28_slot_2":[50],"Asia\\/Dhaka_2025-12-28_slot_3":[58],"Asia\\/Dhaka_2025-12-28_slot_4":[62],"Asia\\/Dhaka_2025-12-28_slot_5":[66],"Asia\\/Dhaka_2025-12-28_slot_0":[67],"Asia\\/Dhaka_2025-12-30_slot_0":[76],"Asia\\/Dhaka_2025-12-30_slot_1":[79],"Asia\\/Dhaka_2025-12-31_slot_2":[83],"Asia\\/Dhaka_2025-12-31_slot_3":[84],"Asia\\/Dhaka_2025-12-31_slot_4":[86],"Asia\\/Dhaka_2025-12-31_slot_5":[87],"Asia\\/Dhaka_2025-12-31_slot_0":[89],"Asia\\/Dhaka_2025-12-31_slot_1":[90],"Asia\\/Dhaka_2026-01-01_slot_2":[94],"Asia\\/Dhaka_2026-01-01_slot_3":[95]}',
                'created_at' => '2025-12-27 17:37:35',
                'updated_at' => '2026-01-01 09:00:19',
            ),
            1 =>
            array (
                'id' => 3,
                'user_id' => 1,
                'name' => 'TradeWave',
                'style' => 'trade_wave',
                'aspect_ratio' => '9:16',
                'videos_per_day' => 1,
                'timezone' => 'Asia/Dhaka',
                'upload_times' => '["09:00"]',
                'is_active' => 1,
                'youtube_token_id' => 3,
                'facebook_page_id' => NULL,
                'prompt_template' => 'update the latest market',
                'last_generated_dates' => '{"UTC_2025-12-28_slot_0":[47],"Asia\\/Dhaka_2025-12-28_slot_2":[51],"Asia\\/Dhaka_2025-12-31_slot_0":[82],"Asia\\/Dhaka_2026-01-01_slot_0":[93]}',
                'created_at' => '2025-12-27 18:33:17',
                'updated_at' => '2026-01-01 03:00:19',
            ),
            2 =>
            array (
                'id' => 4,
                'user_id' => 1,
                'name' => 'Hollywood Hype',
                'style' => 'hollywood_hype',
                'aspect_ratio' => '9:16',
                'videos_per_day' => 2,
                'timezone' => 'Asia/Dhaka',
                'upload_times' => '["03:00","23:30"]',
                'is_active' => 1,
                'youtube_token_id' => 2,
                'facebook_page_id' => NULL,
                'prompt_template' => 'fashan, relationship, latest news',
                'last_generated_dates' => '{"UTC_2025-12-28_slot_0":[48,49],"Asia\\/Dhaka_2025-12-28_slot_1":[52,53],"Asia\\/Dhaka_2025-12-28_slot_2":[59,60],"Asia\\/Dhaka_2025-12-28_slot_3":[63,64],"Asia\\/Dhaka_2025-12-30_slot_0":[80],"Asia\\/Dhaka_2025-12-30_slot_1":[81],"Asia\\/Dhaka_2025-12-31_slot_1":[88],"Asia\\/Dhaka_2025-12-31_slot_0":[92]}',
                'created_at' => '2025-12-27 18:36:12',
                'updated_at' => '2025-12-31 21:00:19',
            ),
            3 =>
            array (
                'id' => 5,
                'user_id' => 1,
                'name' => 'Mehedi Hasan Sagor',
                'style' => 'story',
                'aspect_ratio' => '9:16',
                'videos_per_day' => 1,
                'timezone' => 'Asia/Dhaka',
                'upload_times' => '["02:30"]',
                'is_active' => 1,
                'youtube_token_id' => 4,
                'facebook_page_id' => NULL,
                'prompt_template' => 'Create an interesting and easy-to-understand fact about artificial intelligence, app development, or modern technology.',
                'last_generated_dates' => '{"Asia\\/Dhaka_2025-12-31_slot_0":[91]}',
                'created_at' => '2025-12-31 11:28:20',
                'updated_at' => '2025-12-31 20:30:18',
            ),
        ));


    }
}
