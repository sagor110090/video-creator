<?php

namespace App\Http\Controllers;

use App\Models\Story;
use App\Models\YoutubeToken;
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

        $dailyStats = [];
        for ($i = 0; $i < $days; $i++) {
            $date = now()->subDays($i)->format('Y-m-d');

            $dayYoutubeUploads = $youtubeUploads->where('date', $date);

            $channels = [];
            foreach ($dayYoutubeUploads as $upload) {
                $channels[] = [
                    'type' => 'youtube',
                    'name' => $upload['channel_name'],
                    'thumbnail' => $upload['channel_thumbnail'],
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
        $totalChannels = YoutubeToken::count();

        return response()->json([
            'daily_stats' => $dailyStats,
            'summary' => [
                'total_videos' => $totalVideos,
                'youtube_videos' => $youtubeVideos,
                'total_channels' => $totalChannels,
            ]
        ]);
    }
}
