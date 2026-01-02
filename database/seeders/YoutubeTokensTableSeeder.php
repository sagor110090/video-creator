<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class YoutubeTokensTableSeeder extends Seeder
{

    /**
     * Auto generated seed file
     *
     * @return void
     */
    public function run()
    {


        \DB::table('youtube_tokens')->delete();

        \DB::table('youtube_tokens')->insert(array (
            0 =>
            array (
                'id' => 1,
                'access_token' => '{"access_token":"PLACEHOLDER","expires_in":3599,"scope":"https:\\/\\/www.googleapis.com\\/auth\\/youtube.readonly https:\\/\\/www.googleapis.com\\/auth\\/youtube.upload","token_type":"Bearer","refresh_token":"PLACEHOLDER"}',
                'refresh_token' => 'PLACEHOLDER',
                'expires_at' => '2025-12-31 16:29:41',
                'created_at' => '2025-12-26 06:26:07',
                'updated_at' => '2025-12-31 15:29:42',
                'channel_id' => 'UCQcUoliFnEAqdo_luaazSAA',
                'channel_title' => 'The 60s Lab',
                'channel_thumbnail' => 'https://yt3.ggpht.com/ciE7GGhjI7rlH6DRLsM0AqtxG3Ixva6XYfhwM_C5GW3-mkgUgyLpcK_cb0UsqZ-Vtf-5PbEVqA=s88-c-k-c0x00ffffff-no-rj',
            ),
            1 =>
            array (
                'id' => 2,
                'access_token' => '{"access_token":"PLACEHOLDER","expires_in":3599,"scope":"https:\\/\\/www.googleapis.com\\/auth\\/youtube.upload https:\\/\\/www.googleapis.com\\/auth\\/youtube.readonly","token_type":"Bearer","refresh_token":"PLACEHOLDER"}',
                'refresh_token' => 'PLACEHOLDER',
                'expires_at' => '2025-12-31 22:28:32',
                'created_at' => '2025-12-26 06:26:38',
                'updated_at' => '2025-12-31 21:28:33',
                'channel_id' => 'UCN2rp42lJNM71hnJqwlU3rQ',
                'channel_title' => 'Hollywood Hype',
                'channel_thumbnail' => 'https://yt3.ggpht.com/L6Q1ulw_gIV_M5vJTI5KKua_Opv-V3Z_B8bySo1RzQKUGEAVn_isXnCa2Hhr8wNkQHubjVEYKec=s88-c-k-c0x00ffffff-no-rj',
            ),
            2 =>
            array (
                'id' => 3,
                'access_token' => '{"access_token":"PLACEHOLDER","expires_in":3599,"scope":"https:\\/\\/www.googleapis.com\\/auth\\/youtube.upload https:\\/\\/www.googleapis.com\\/auth\\/youtube.readonly","token_type":"Bearer","refresh_token":"PLACEHOLDER"}',
                'refresh_token' => 'PLACEHOLDER',
                'expires_at' => '2025-12-31 04:24:00',
                'created_at' => '2025-12-26 06:27:02',
                'updated_at' => '2025-12-31 03:24:01',
                'channel_id' => 'UCZ9Fj9bre15ebqszak7T7Jg',
                'channel_title' => 'TradeWave',
                'channel_thumbnail' => 'https://yt3.ggpht.com/EPFVD9kJ4yP3km2J5I2APK9w3wcHZibW388msVSAXMGOCJC3bJN2QiZMzPCA4PKmnTspPwlY=s88-c-k-c0x00ffffff-no-rj',
            ),
            3 =>
            array (
                'id' => 4,
                'access_token' => '{"access_token":"PLACEHOLDER","expires_in":3599,"scope":"https:\\/\\/www.googleapis.com\\/auth\\/youtube.readonly https:\\/\\/www.googleapis.com\\/auth\\/youtube.upload","token_type":"Bearer","refresh_token":"PLACEHOLDER"}',
                'refresh_token' => 'PLACEHOLDER',
                'expires_at' => '2025-12-31 12:18:40',
                'created_at' => '2025-12-31 11:18:41',
                'updated_at' => '2025-12-31 11:18:41',
                'channel_id' => 'UCAHhtou0fFA0m7zc9cT7FJw',
                'channel_title' => 'Developer Sagor',
                'channel_thumbnail' => 'https://yt3.ggpht.com/it19GccEQI_u0FMlGNgQUMJOo0oKmOwmnHcGqheRkSPhiEgMkiwB46t5-OS2AFAKjHfPUGCe=s88-c-k-c0x00ffffff-no-rj',
            ),
        ));


    }
}
