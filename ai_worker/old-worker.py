import sys
import json
import os
import subprocess
import urllib.request
import urllib.parse
import time
import re
import shutil
import requests
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load .env from project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

def get_executable_path(name, default_path=None):
    """Finds an executable in the system PATH or returns a default."""
    path = shutil.which(name)
    if path:
        return path
    if default_path and os.path.exists(default_path):
        return default_path
    return name

# Detect paths for ffmpeg and ffprobe
FFMPEG_PATH = get_executable_path('ffmpeg', '/usr/bin/ffmpeg')
FFPROBE_PATH = get_executable_path('ffprobe', '/usr/bin/ffprobe')

# Logo Path for watermarking
LOGO_PATH = os.path.join(project_root, 'public', 'logo.png')

def run_command(command):
    try:
        # Replace 'ffmpeg' with the absolute path
        if command[0] == 'ffmpeg':
            command[0] = FFMPEG_PATH
        elif command[0] == 'ffprobe':
            command[0] = FFPROBE_PATH

        print(f"Running: {' '.join(command)}", file=sys.stderr)
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            return False
        return True
    except FileNotFoundError:
        print(f"Warning: Command '{command[0]}' not found. Mocking output...", file=sys.stderr)
        return False

def fetch_stock_image(output_path, query, aspect_ratio='16:9'):
    """Fetches a high-quality stock image from Pexels."""
    pexels_key = os.getenv('PEXELS_API_KEY')
    if not pexels_key:
        print("Warning: PEXELS_API_KEY not found. Falling back to AI image.", file=sys.stderr)
        return False

    try:
        print(f"DEBUG: Fetching stock image from Pexels for query: {query}", file=sys.stderr)
        orientation = 'landscape' if aspect_ratio == '16:9' else 'portrait'
        if aspect_ratio == '1:1': orientation = 'square'

        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page=1&orientation={orientation}"
        headers = {"Authorization": pexels_key}

        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('photos'):
                image_url = data['photos'][0]['src']['large2x']
                img_response = requests.get(image_url, timeout=15)
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                return True
            else:
                print(f"Warning: No stock photos found for query: {query}", file=sys.stderr)
        else:
            print(f"Warning: Pexels API failed with status {response.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Pexels error: {e}", file=sys.stderr)

    return False

def fetch_web_image_via_search(output_path, query, aspect_ratio='16:9'):
    """Finds real images on the web with multiple fallbacks and query simplification."""
    # List of providers to try
    providers = [
        "https://loremflickr.com/{w}/{h}/{q}",
        "https://api.api-ninjas.com/v1/randomimage?category={c}", # Needs key, but we'll stick to free ones
        "https://picsum.photos/{w}/{h}?sig={s}" # Last resort random but high quality
    ]

    # Set dimensions based on aspect ratio
    width, height = (1920, 1080) if aspect_ratio == '16:9' else (1080, 1920)

    try:
        # 1. Clean and simplify the query
        search_query = query
        if "illustrating:" in query:
            search_query = query.split("illustrating:")[1].split(".")[0].strip()

        # Remove fluff words
        fluff_words = [
            "8k", "4k", "hyper-realistic", "cinematic", "lighting", "highly detailed",
            "vibrant colors", "composition", "visualization", "resolution", "rendering",
            "unreal engine", "octane render", "masterpiece", "trending on artstation",
            "did you know", "it is", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with"
        ]

        # Initial cleaning
        clean_query = re.sub(r'[^\w\s]', '', search_query.lower())
        words = [w for w in clean_query.split() if w not in fluff_words]

        # We'll try 3 versions of the query:
        # 1. First 5 important words
        # 2. First 2 important words (very broad)
        # 3. A totally random high-quality nature/tech tag based on style

        query_variants = [
            " ".join(words[:5]),
            " ".join(words[:2]),
            "nature,landscape" if "story" in query.lower() else "technology,science"
        ]

        for q_variant in query_variants:
            if not q_variant.strip(): continue

            # Try LoremFlickr first with this variant
            final_url = f"https://loremflickr.com/{width}/{height}/{urllib.parse.quote(q_variant)}"
            print(f"DEBUG: Trying LoremFlickr for variant: {q_variant}", file=sys.stderr)

            try:
                response = requests.get(final_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }, timeout=15, allow_redirects=True)

                if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    print(f"DEBUG: Successfully downloaded image for: {q_variant}", file=sys.stderr)
                    return True
            except Exception as e:
                print(f"Warning: LoremFlickr variant {q_variant} failed: {e}", file=sys.stderr)

        # 2. Final Fallback: Picsum (Random but guaranteed high quality real photo)
        print(f"DEBUG: Trying Picsum as last web resort", file=sys.stderr)
        picsum_url = f"https://picsum.photos/{width}/{height}?sig={int(time.time())}"
        response = requests.get(picsum_url, timeout=10)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True

    except Exception as e:
        print(f"Warning: Web search error: {e}", file=sys.stderr)

    return False

def generate_ai_image(output_path, prompt, aspect_ratio='16:9'):
    """Generates high-quality AI image using OpenAI, Pollinations.ai or a fallback."""
    width, height = (1920, 1080) if aspect_ratio == '16:9' else (1080, 1920)

    # 1. Try OpenAI (if API key is available)
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        try:
            print(f"DEBUG: Fetching AI image from OpenAI for prompt: {prompt[:50]}...", file=sys.stderr)
            client = OpenAI(api_key=openai_key)
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024", # DALL-E 3 default
                quality="standard"
            )
            image_url = response.data[0].url
            if image_url:
                img_response = requests.get(image_url, timeout=15)
                if img_response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(img_response.content)
                    return True
        except Exception as e:
            print(f"Warning: OpenAI image generation failed: {e}", file=sys.stderr)

    # 2. Try Pollinations.ai (Free, no key needed)
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={int(time.time())}"
        print(f"DEBUG: Fetching AI image from Pollinations.ai: {url}", file=sys.stderr)

        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"Warning: Pollinations.ai failed: {e}", file=sys.stderr)

    return False

def apply_watermark(image_path, aspect_ratio='16:9'):
    """Overlays the logo watermark on the image using FFmpeg."""
    if not os.path.exists(LOGO_PATH):
        print(f"Warning: Logo not found at {LOGO_PATH}, skipping watermark.", file=sys.stderr)
        return False

    temp_output = image_path.replace('.jpg', '_watermarked.jpg')

    # Calculate logo size: about 12% of the width
    width, height = (1920, 1080) if aspect_ratio == '16:9' else (1080, 1920)
    logo_w = int(width * 0.12)

    # Overlay in bottom-right with 30px padding
    # [1:v]scale={logo_w}:-1 scales the logo while maintaining aspect ratio
    # overlay=W-w-30:H-h-30 positions it
    command = [
        FFMPEG_PATH, '-y',
        '-i', image_path,
        '-i', LOGO_PATH,
        '-filter_complex', f"[1:v]scale={logo_w}:-1[logo];[0:v][logo]overlay=W-w-30:H-h-30",
        '-q:v', '2', # High quality
        temp_output
    ]

    print(f"DEBUG: Applying watermark to {image_path}", file=sys.stderr)
    if run_command(command):
        if os.path.exists(temp_output):
            os.replace(temp_output, image_path)
            return True
    return False

def process_text_for_naturalness(text):
    """Adds natural pauses and breathing room to the text for a more human feel."""
    # Add slightly longer pauses after sentences and commas
    text = text.replace('. ', '... ')
    text = text.replace(', ', ', ... ')
    # Ensure it's not too long for the TTS engine in one go
    return text

def generate_tts_audio(output_path, text, style='story'):
    """Generates 100% human-like 'cloned' audio using high-fidelity neural voices and studio processing."""
    # Try to find edge-tts in PATH, then fallback to local venv
    local_venv_edge = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'edge-tts')
    edge_tts_path = get_executable_path('edge-tts', local_venv_edge)

    # Process text for more natural human-like pauses
    natural_text = process_text_for_naturalness(text)

    # Personality mapping for "Cloned Voice" quality
    # We use the most expressive neural voices available
    personalities = {
        'science_short': {
            'voice': 'en-US-SteffanNeural', # Very natural, scholarly male
            'rate': '+2%',
            'pitch': '-1Hz'
        },
        'hollywood_hype': {
            'voice': 'en-US-AvaNeural',     # Extremely expressive, modern female
            'rate': '+8%',
            'pitch': '+1Hz'
        },
        'trade_wave': {
            'voice': 'en-GB-RyanNeural',    # Sophisticated British male
            'rate': '+0%',
            'pitch': '-1Hz'
        },
        'story': {
            'voice': 'en-US-AndrewNeural',  # Warm, rich storytelling male
            'rate': '-3%',
            'pitch': '+0Hz'
        }
    }

    config = personalities.get(style, personalities['story'])
    voice = config['voice']
    rate = config['rate']
    pitch = config['pitch']

    # Generate high-quality audio with custom rate and pitch
    temp_audio = output_path.replace('.mp3', '_temp.mp3')
    command = [
        edge_tts_path,
        '--text', natural_text,
        '--write-media', temp_audio,
        '--voice', voice,
        '--rate=' + rate,
        '--pitch=' + pitch
    ]

    print(f"DEBUG: Generating ultra-realistic human voice: {voice} for style {style}", file=sys.stderr)

    if run_command(command):
        # STUDIO QUALITY POST-PROCESSING
        # We add 'dynaudnorm' (dynamic normalization) and a slight 'highpass/lowpass'
        # to mimic high-end studio microphones and remove robotic tinny frequencies.
        convert_cmd = [
            FFMPEG_PATH, '-y', '-i', temp_audio,
            '-af', (
                'dynaudnorm=p=0.9:s=5,'   # Professional dynamic normalization
                'aecho=0.8:0.88:6:0.4,'   # Subtle room presence (not an echo)
                'highpass=f=80,'          # Remove low-end rumble
                'lowpass=f=15000'         # Remove harsh high-end digital hiss
            ),
            '-ar', '48000',
            '-ac', '2',
            '-q:a', '0',               # Best possible VBR quality
            output_path
        ]
        if run_command(convert_cmd):
            os.remove(temp_audio)
            return

    # Fallback to macOS 'say' if edge-tts fails (only on macOS)
    if sys.platform == 'darwin':
        print(f"Warning: edge-tts failed. Falling back to macOS 'say'.", file=sys.stderr)
        temp_aiff = output_path.replace('.mp3', '.aiff')
        say_command = ['say', text, '-o', temp_aiff]
        if run_command(say_command):
            convert_command = [
                FFMPEG_PATH, '-y', '-i', temp_aiff,
                '-ar', '48000',
                '-ac', '2',
                '-codec:a', 'libmp3lame', '-qscale:a', '2',
                output_path
            ]
            run_command(convert_command)
            if os.path.exists(temp_aiff):
                os.remove(temp_aiff)
            return

    # Final fallback to silence for both Linux and macOS if everything else fails
    print(f"Warning: TTS failed. Falling back to silence.", file=sys.stderr)
    command_silence = [
        FFMPEG_PATH, '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
        '-t', '5', output_path
    ]
    run_command(command_silence)

def create_scene_video(image_path, audio_path, output_path, narration, scene_index=0, aspect_ratio='16:9'):
    """Creates high-quality video with smooth zoom animation and enhanced subtitles."""
    # Use higher resolution for better quality
    width, height = (1920, 1080) if aspect_ratio == '16:9' else (1080, 1920)

    command_duration = [
        FFPROBE_PATH, '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
    ]

    try:
        result = subprocess.run(command_duration, capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.returncode == 0 else 5.0
    except:
        duration = 5.0

    # Ensure duration is at least 1 second
    duration = max(duration, 1.0)

    # Use higher fps for smoother animation (30 fps instead of 25)
    fps = 30
    total_frames = int(duration * fps)

    # Alternate zoom effects based on scene index (slower, smoother zoom)
    if scene_index % 2 == 0:
        # Slower zoom in for smoother effect
        zoom_expr = "min(zoom+0.001,1.3)"
    else:
        # Slower zoom out for smoother effect
        zoom_expr = "max(1.3-0.001*on,1.0)"

    # Professional Subtitles: Word-by-word / Small chunks centered
    narration = re.sub(r'\s+', ' ', narration).strip()
    words = narration.split()
    total_words = len(words)

    # Cross-platform font detection - prefer bold fonts
    possible_fonts = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "Arial",
    ]

    font_path = "Arial"
    for path in possible_fonts:
        if os.path.exists(path):
            font_path = path
            break

    if total_words == 0:
        subtitles_filter = "identity" # No text
    else:
        # Calculate duration per word
        duration_per_word = duration / total_words

        # Group words into small chunks (1-2 words) for a professional "pop" look
        chunks = []
        chunk_size = 2 # Show 2 words at a time
        for i in range(0, total_words, chunk_size):
            chunk_words = words[i:i + chunk_size]
            start_time = i * duration_per_word
            # End time is when the next chunk starts, or end of video
            end_time = min((i + chunk_size) * duration_per_word, duration)
            chunks.append({
                'text': " ".join(chunk_words), # Removed .upper() to keep punctuation and case as intended
                'start': start_time,
                'end': end_time
            })

        # Enhanced subtitle styling: Larger and more central
        font_size = 70 if aspect_ratio == '16:9' else 90
        # Position slightly below center for 9:16, or bottom for 16:9
        y_pos = "(h-text_h)/2 + 200" if aspect_ratio == '9:16' else "h-120"

        drawtext_filters = []
        for chunk in chunks:
            # For the text parameter in drawtext, we need to be extremely careful with single quotes.
            # In FFmpeg's filter syntax, to get a literal ' inside a '...' string,
            # you must use '\'' which actually means: end string, escaped quote, start string.
            # However, when passed via Python's subprocess.run, additional layers of escaping are involved.

            # The most reliable way to handle 't, 's, etc. in drawtext is to:
            # use a very specific triple-backslash escaping for the single quote
            # so that it survives both the Python string and the FFmpeg filter parsing.
            safe_txt = chunk['text'].replace("'", "'\\\\\\''").replace(":", "\\:").replace(",", "\\,")
            # Also need to handle potential newlines or other weirdness in the chunk
            safe_txt = safe_txt.replace("\n", " ").replace("\r", "")

            # Each chunk is a separate drawtext filter enabled only during its timeframe
            dt = (
                f"drawtext=text='{safe_txt}':fontfile='{font_path}':"
                f"fontcolor=#FFFF00:fontsize={font_size}:borderw=5:bordercolor=black:"
                f"shadowcolor=black@0.6:shadowx=3:shadowy=3:"
                f"x=(w-text_w)/2:y={y_pos}:enable='between(t,{chunk['start']:.2f},{chunk['end']:.2f})'"
            )
            drawtext_filters.append(dt)

        subtitles_filter = ",".join(drawtext_filters)

    # High-quality video encoding settings:
    command = [
        FFMPEG_PATH, '-y',
        '-loop', '1', '-i', image_path,
        '-i', audio_path,
        '-vf', f"scale={width}:{height}:flags=lanczos,zoompan=z='{zoom_expr}':d={total_frames}:s={width}x{height}:fps={fps},fps={fps},{subtitles_filter},format=yuv420p",
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '18',
        '-tune', 'film',
        '-t', str(duration),
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-ar', '48000',
        '-shortest',
        output_path
    ]
    if not run_command(command):
        with open(output_path, 'w') as f:
            f.write("mock video content")

def step4_automatic_assembly(output_dir, scene_videos, background_music=None):
    """Stitches all scenes into one final .mp4 with high-quality audio and adds background music."""
    final_video_path = os.path.join(output_dir, "final_video.mp4")
    concat_file_path = os.path.join(output_dir, "concat.txt")
    temp_video_path = os.path.join(output_dir, "temp_merged.mp4")

    with open(concat_file_path, 'w') as f:
        for vid in scene_videos:
            f.write(f"file '{os.path.abspath(vid)}'\n")

    # Step 4.1: Merge all scene videos
    merge_command = [
        FFMPEG_PATH, '-y', '-f', 'concat', '-safe', '0', '-i', concat_file_path,
        '-c', 'copy', temp_video_path
    ]
    if not run_command(merge_command):
        return None

    # Step 4.2: Add background music if provided
    if background_music and os.path.exists(background_music):
        # Mix audio with high-quality settings
        # -stream_loop -1 loops the background music
        # -filter_complex mixes audio: [1:a]volume=0.10 lowers background music, [0:a]volume=1.5 boosts narration
        music_mix_command = [
            FFMPEG_PATH, '-y',
            '-i', temp_video_path,
            '-stream_loop', '-1', '-i', background_music,
            '-filter_complex', "[1:a]volume=0.10[bg];[0:a]volume=1.5[narr];[narr][bg]amix=inputs=2:duration=first[a]",
            '-map', '0:v',
            '-map', '[a]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '48000',
            '-shortest',
            final_video_path
        ]
        if run_command(music_mix_command):
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            return final_video_path

    # Fallback to just the merged video if no music or command fails
    os.rename(temp_video_path, final_video_path)
    return final_video_path

def main():
    if len(sys.argv) < 2:
        print("Usage: python worker.py <json_input>")
        sys.exit(1)

    data = json.loads(sys.argv[1])
    story_id = data['story_id']
    style = data.get('style', 'story')
    scenes = data['scenes']
    output_dir = data['output_dir']
    aspect_ratio = data.get('aspect_ratio', '16:9')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"DEBUG: Processing story {story_id} (style: {style}) with {len(scenes)} scenes in {aspect_ratio}", file=sys.stderr)
    scene_videos = []

    for i, scene in enumerate(scenes):
        print(f"DEBUG: Processing scene {i}", file=sys.stderr)
        img_path = os.path.join(output_dir, f"scene_{i}_img.jpg")
        aud_path = os.path.join(output_dir, f"scene_{i}_aud.mp3")
        vid_path = os.path.join(output_dir, f"scene_{i}_vid.mp4")

        # 1. Generate/Fetch Visuals
        media_type = scene.get('media_type', 'ai')
        visual_success = False

        # Priority 1: AI Web Search using the detailed image_prompt
        if scene.get('image_prompt'):
            print(f"DEBUG: Trying AI WEB SEARCH for scene {i} using image_prompt", file=sys.stderr)
            visual_success = fetch_web_image_via_search(img_path, scene['image_prompt'], aspect_ratio)

        # Priority 2: Pexels Stock Search
        if not visual_success:
            query = scene.get('stock_query') or scene.get('narration')
            if query:
                print(f"DEBUG: Trying STOCK SEARCH for scene {i}", file=sys.stderr)
                visual_success = fetch_stock_image(img_path, query, aspect_ratio)

        # Priority 3: AI Image Generation
        if not visual_success:
            if scene.get('image_prompt'):
                print(f"DEBUG: Trying AI GENERATION for scene {i}", file=sys.stderr)
                visual_success = generate_ai_image(img_path, scene['image_prompt'], aspect_ratio)

        # Priority 4: Final Retry with broad keywords if everything failed
        if not visual_success:
            print(f"DEBUG: Everything failed for scene {i}, trying one last broad web search", file=sys.stderr)
            visual_success = fetch_web_image_via_search(img_path, "nature background", aspect_ratio)

        if not visual_success:
            # If we STILL don't have an image, we MUST at least have a valid file to avoid FFmpeg crashing
            # but we won't use the blue mock boxes. We'll use a solid black background which is more professional.
            print(f"DEBUG: Final fallback to black frame for scene {i}", file=sys.stderr)
            width, height = (1920, 1080) if aspect_ratio == '16:9' else (1080, 1920)
            command = [
                FFMPEG_PATH, '-y', '-f', 'lavfi', '-i', f'color=c=black:s={width}x{height}:d=1',
                '-frames:v', '1', img_path
            ]
            run_command(command)

        # Apply watermark to the final image
        apply_watermark(img_path, aspect_ratio)

        # 2. Voice Generation
        generate_tts_audio(aud_path, scene['narration'], style)

        # 3. Create Scene Video
        create_scene_video(img_path, aud_path, vid_path, scene['narration'], i, aspect_ratio)
        scene_videos.append(vid_path)

    # 4. Step 4: Automatic Assembly
    print(f"DEBUG: Assembling final video...", file=sys.stderr)

    # Check for background music in public/audio/background.mp3
    # Use absolute path based on script location
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bg_music_path = os.path.join(script_dir, 'public', 'audio', 'background.mp3')

    final_video = step4_automatic_assembly(output_dir, scene_videos, bg_music_path)

    if final_video:
        print(json.dumps({
            "status": "success",
            "video_path": final_video
        }))
    else:
        print(json.dumps({
            "status": "error",
            "message": "Assembly failed"
        }))

if __name__ == "__main__":
    main()
