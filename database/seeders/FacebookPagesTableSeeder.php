<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class FacebookPagesTableSeeder extends Seeder
{

    /**
     * Auto generated seed file
     *
     * @return void
     */
    public function run()
    {


        \DB::table('facebook_pages')->delete();

        \DB::table('facebook_pages')->insert(array (
            0 =>
            array (
                'id' => 4,
                'user_id' => 1,
                'page_id' => '981059701749391',
                'name' => 'The 60s Lab',
                'access_token' => 'EAAOynq1AttkBQSmTU5hWpqvQHydJnDYQzYMg6Bg5JeDgHc7ECF5wYCUwlQWu7wf48qvcf9JFEvDX9XABtaVH3POw50uoK2KyklydZBZBwRRzRYpJQ4J13QMKEZAUhkZA5hQn0PmwtIeOmOoE2iv507081zGsAgl01jTL31Xm8jiSIflxq8ObYOWWJdpZCKdHQqYvggV9pOhkHE9GZBykBD5spD',
                'category' => 'School',
                'picture_url' => 'https://scontent.xx.fbcdn.net/v/t39.30808-1/604725998_4106171119638236_3320325505485021366_n.jpg?stp=cp0_dst-jpg_s50x50_tt6&_nc_cat=111&ccb=1-7&_nc_sid=f907e8&_nc_eui2=AeHdfOlT9zHuNo86DsuokQ2BuJUN0fH4GHW4lQ3R8fgYdQzoovwvPhd5uuqoAh9fGVHSbWCXa8G5LPpEWMtWLwIK&_nc_ohc=0QQi5YRK9AIQ7kNvwHaDwxG&_nc_oc=AdmmPMafyHbai8wpZCJolY3XbCenB9aiLfcBrCBEGJzHCNgcevIywELZXM-9e9ZdQt0&_nc_zt=24&_nc_ht=scontent.xx&edm=AGaHXAAEAAAA&_nc_gid=mY5OxAdzkv3VtoEOtd39zw&_nc_tpa=Q5bMBQEOklwzHaWHrrQSeimbDPJ2Jh1En60otgkyk4Nwsbuv0LITTfVvGEbKUj5IuG2qsUFbIQNxn097JA&oh=00_AfmME_cxJ-GUci3wLtCy6FUB-ZlX1h1sOJ-G8ikH8CmQkA&oe=695577CC',
                'created_at' => '2025-12-27 10:28:11',
                'updated_at' => '2025-12-27 10:28:11',
            ),
        ));


    }
}
