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
                'id' => 2,
                'access_token' => 'PLACEHOLDER_ACCESS_TOKEN',
                'refresh_token' => 'PLACEHOLDER_REFRESH_TOKEN',
                'expires_at' => '2025-12-25 06:51:31',
                'created_at' => '2025-12-24 21:39:18',
                'updated_at' => '2025-12-25 05:51:32',
                'channel_id' => 'UCQcUoliFnEAqdo_luaazSAA',
                'channel_title' => 'The 60s Lab',
                'channel_thumbnail' => 'https://yt3.ggpht.com/ciE7GGhjI7rlH6DRLsM0AqtxG3Ixva6XYfhwM_C5GW3-mkgUgyLpcK_cb0UsqZ-Vtf-5PbEVqA=s88-c-k-c0x00ffffff-no-rj',
            ),
            1 =>
            array (
                'id' => 3,
                'access_token' => 'PLACEHOLDER_ACCESS_TOKEN',
                'refresh_token' => 'PLACEHOLDER_REFRESH_TOKEN',
                'expires_at' => '2025-12-25 10:38:37',
                'created_at' => '2025-12-24 21:44:02',
                'updated_at' => '2025-12-25 09:38:38',
                'channel_id' => 'UCN2rp42lJNM71hnJqwlU3rQ',
                'channel_title' => 'Hollywood Hype',
                'channel_thumbnail' => 'https://yt3.ggpht.com/L6Q1ulw_gIV_M5vJTI5KKua_Opv-V3Z_B8bySo1RzQKUGEAVn_isXnCa2Hhr8wNkQHubjVEYKec=s88-c-k-c0x00ffffff-no-rj',
            ),
            2 =>
            array (
                'id' => 4,
                'access_token' => 'PLACEHOLDER_ACCESS_TOKEN',
                'refresh_token' => 'PLACEHOLDER_REFRESH_TOKEN',
                'expires_at' => '2025-12-25 11:33:24',
                'created_at' => '2025-12-25 10:33:25',
                'updated_at' => '2025-12-25 10:33:25',
                'channel_id' => 'UCZ9Fj9bre15ebqszak7T7Jg',
                'channel_title' => 'TradeWave',
                'channel_thumbnail' => 'https://yt3.ggpht.com/EPFVD9kJ4yP3km2J5I2APK9w3wcHZibW388msVSAXMGOCJC3bJN2QiZMzPCA4PKmnTspPwlY=s88-c-k-c0x00ffffff-no-rj',
            ),
        ));


    }
}
