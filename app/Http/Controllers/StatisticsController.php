<?php

namespace App\Http\Controllers;

use App\Models\Story;
use App\Models\YoutubeToken;
use App\Models\FacebookPage;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class StatisticsController extends Controller
{
    public function index(Request $request)
    {
        $days = $request->get('days', 30);
        
        $youtubeUploads = Story::whereNotNull('youtube_token_id')
            ->where('is_uploaded_to_youtube', true)
            ->where('created_at', '>=', now()->subDays($days))
            ->select(
                DB::raw('DATE(created_at) as date'),
                'youtube_token_id',
                DB::raw('COUNT(*) as count')
            )
            ->groupBy('date', 'youtube_token_id')
            ->orderBy('date', 'desc')
            ->get()
            ->map(function ($item) {
                $channel = YoutubeToken::find($item->youtube_token_id);
                return [
                    'date' => $item->date,
                    'channel_id' => $item->youtube_token_id,
                    'channel_name' => $channel?->channel_title ?? 'Unknown Channel',
                    'channel_thumbnail' => $channel?->channel_thumbnail,
                    'count' => $item->count,
                ];
            });

        $facebookUploads = Story::whereNotNull('facebook_page_id')
            ->where('is_uploaded_to_facebook', true)
            ->where('created_at', '>=', now()->subDays($days))
            ->select(
                DB::raw('DATE(created_at) as date'),
                'facebook_page_id',
                DB::raw('COUNT(*) as count')
            )
            ->groupBy('date', 'facebook_page_id')
            ->orderBy('date', 'desc')
            ->get()
            ->map(function ($item) {
                $page = FacebookPage::find($item->facebook_page_id);
                return [
                    'date' => $item->date,
                    'page_id' => $item->facebook_page_id,
                    'page_name' => $page?->name ?? 'Unknown Page',
                    'page_picture' => $page?->picture_url,
                    'count' => $item->count,
                ];
            });

        $dailyStats = [];
        for ($i = 0; $i < $days; $i++) {
            $date = now()->subDays($i)->format('Y-m-d');
            
            $dayYoutubeUploads = $youtubeUploads->where('date', $date);
            $dayFacebookUploads = $facebookUploads->where('date', $date);
            
            $channels = [];
            foreach ($dayYoutubeUploads as $upload) {
                $channels[] = [
                    'type' => 'youtube',
                    'name' => $upload['channel_name'],
                    'thumbnail' => $upload['channel_thumbnail'],
                    'count' => $upload['count'],
                ];
            }
            
            foreach ($dayFacebookUploads as $upload) {
                $channels[] = [
                    'type' => 'facebook',
                    'name' => $upload['page_name'],
                    'thumbnail' => $upload['page_picture'],
                    'count' => $upload['count'],
                ];
            }
            
            $dailyStats[] = [
                'date' => $date,
                'total' => array_sum(array_column($channels, 'count')),
                'channels' => array_values($channels),
            ];
        }

        $totalVideos = Story::count();
        $youtubeVideos = Story::where('is_uploaded_to_youtube', true)->count();
        $facebookVideos = Story::where('is_uploaded_to_facebook', true)->count();
        $totalChannels = YoutubeToken::count();
        $totalPages = FacebookPage::count();

        return response()->json([
            'daily_stats' => $dailyStats,
            'summary' => [
                'total_videos' => $totalVideos,
                'youtube_videos' => $youtubeVideos,
                'facebook_videos' => $facebookVideos,
                'total_channels' => $totalChannels,
                'total_pages' => $totalPages,
            ],
        ]);
    }
}
