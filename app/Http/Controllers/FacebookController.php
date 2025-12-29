<?php

namespace App\Http\Controllers;

use Facebook\Facebook;
use Facebook\PersistentData\PersistentDataInterface;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use App\Models\FacebookPage;

class LaravelPersistentDataHandler implements PersistentDataInterface
{
    public function get($key)
    {
        return session()->get($key);
    }

    public function set($key, $value)
    {
        session()->put($key, $value);
    }
}

class FacebookController extends Controller
{
    protected $fb;

    public function __construct()
    {
        $this->fb = new Facebook([
            'app_id' => env('FACEBOOK_CLIENT_ID'),
            'app_secret' => env('FACEBOOK_CLIENT_SECRET'),
            'default_graph_version' => 'v18.0',
            'persistent_data_handler' => new LaravelPersistentDataHandler(),
        ]);
    }

    public function auth()
    {
        session()->start();
        $helper = $this->fb->getRedirectLoginHelper();
        
        $permissions = ['pages_manage_posts', 'pages_read_engagement', 'pages_show_list', 'publish_video'];
        $loginUrl = $helper->getLoginUrl(env('FACEBOOK_REDIRECT_URI'), $permissions);
        
        Log::info('Generated Facebook Auth URL: ' . $loginUrl);
        Log::info('Session ID: ' . session()->getId());
        
        return redirect($loginUrl);
    }

    public function callback(Request $request)
    {
        session()->start();
        $helper = $this->fb->getRedirectLoginHelper();
        
        Log::info('Callback Session ID: ' . session()->getId());
        Log::info('Callback URL state: ' . $request->query->get('state'));
        
        try {
            $accessToken = $helper->getAccessToken();
        } catch (\Facebook\Exceptions\FacebookResponseException $e) {
            Log::error('Graph returned an error: ' . $e->getMessage());
            return redirect('/')->with('error', 'Graph returned an error: ' . $e->getMessage());
        } catch (\Facebook\Exceptions\FacebookSDKException $e) {
            Log::error('Facebook SDK error: ' . $e->getMessage());
            return redirect()->route('facebook.auth')->with('error', 'Could not connect to Facebook. Please try again.');
        }

        if (!$accessToken) {
            Log::error('No access token returned');
            return redirect()->route('facebook.auth')->with('error', 'Could not connect to Facebook. Please try again.');
        }

        $oAuth2Client = $this->fb->getOAuth2Client();
        $longLivedAccessToken = $oAuth2Client->getLongLivedAccessToken($accessToken);
        
        try {
            $response = $this->fb->get('/me/accounts?fields=id,name,access_token,category,picture', $longLivedAccessToken->getValue());
            $pages = $response->getGraphEdge();
            
            foreach ($pages as $page) {
                $pageData = $page->asArray();
                $pictureUrl = $pageData['picture']['url'] ?? null;
                
                FacebookPage::updateOrCreate(
                    [
                        'user_id' => Auth::id(),
                        'page_id' => $pageData['id'],
                    ],
                    [
                        'name' => $pageData['name'],
                        'access_token' => $pageData['access_token'],
                        'category' => $pageData['category'] ?? null,
                        'picture_url' => $pictureUrl,
                    ]
                );
            }
            
            Log::info('Facebook pages imported successfully for user: ' . Auth::id());
            
        } catch (\Facebook\Exceptions\FacebookResponseException $e) {
            Log::error('Graph returned an error: ' . $e->getMessage());
            return redirect('/')->with('error', 'Could not fetch pages: ' . $e->getMessage());
        }

        return redirect('/')->with('success', 'Facebook pages connected successfully!');
    }

    public function pages()
    {
        $pages = Auth::user()->facebookPages;
        return response()->json($pages);
    }

    public function disconnect($id)
    {
        $page = FacebookPage::where('user_id', Auth::id())->where('page_id', $id)->first();
        
        if ($page) {
            $page->delete();
            return response()->json(['message' => 'Facebook page disconnected successfully']);
        }
        
        return response()->json(['message' => 'Page not found'], 404);
    }
}