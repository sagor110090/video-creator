import sys
import json
import os
import subprocess
import urllib.request
import urllib.parse
import time
import re
import shutil

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

def generate_ai_image(output_path, prompt, aspect_ratio='16:9'):
    """Generates high-quality AI image using Pollinations.ai or a fallback."""
    # Use higher resolution for better video quality
    width, height = (1920, 1080) if aspect_ratio == '16:9' else (1080, 1920)

    # 1. Try Pollinations.ai
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={int(time.time())}"
        print(f"DEBUG: Fetching AI image from {url}", file=sys.stderr)

        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=15) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"Warning: Pollinations.ai failed: {e}. Trying Picsum...", file=sys.stderr)

    # 2. Try Picsum as a generic fallback
    try:
        url = f"https://picsum.photos/{width}/{height}?sig={int(time.time())}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"Warning: Picsum failed: {e}. Falling back to mock.", file=sys.stderr)
        return False

def generate_mock_image(output_path, text, aspect_ratio='16:9'):
    # Sanitize text for FFmpeg drawtext filter
    width, height = (1920, 1080) if aspect_ratio == '16:9' else (1080, 1920)
    safe_text = text.replace("'", "").replace(":", "").replace("\\", "")
    command = [
        FFMPEG_PATH, '-y', '-f', 'lavfi', '-i', f'color=c=blue:s={width}x{height}:d=1',
        '-vf', f"drawtext=text='{safe_text}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2",
        '-frames:v', '1', output_path
    ]
    if not run_command(command):
        # Fallback: Create an empty file if ffmpeg is missing
        with open(output_path, 'w') as f:
            f.write("mock image content")

def generate_tts_audio(output_path, text, style='story'):
    """Generates high-quality human-like audio using Microsoft Edge TTS."""
    # Try to find edge-tts in PATH, then fallback to local venv
    local_venv_edge = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'edge-tts')
    edge_tts_path = get_executable_path('edge-tts', local_venv_edge)

    # We'll use a high-quality neural voice
    # Default: en-US-AndrewNeural (natural male)
    # Science: en-US-BrianNeural (authoritative)
    # Entertainment: en-US-EmmaNeural (energetic female)
    # Trade: en-US-ChristopherNeural (professional male)

    voice = "en-US-AndrewNeural"
    if style == 'science_short':
        voice = "en-US-BrianNeural"
    elif style == 'hollywood_hype':
        voice = "en-US-EmmaNeural"
    elif style == 'trade_wave':
        voice = "en-US-ChristopherNeural"

    # Generate high-quality audio (48kHz stereo for better sound)
    temp_audio = output_path.replace('.mp3', '_temp.mp3')
    command = [
        edge_tts_path,
        '--text', text,
        '--write-media', temp_audio,
        '--voice', voice
    ]

    print(f"DEBUG: Generating high-quality voice with edge-tts: {voice} for style {style}", file=sys.stderr)

    if run_command(command):
        # Convert to high-quality MP3 with better settings
        # -ar 48000: 48kHz sample rate (DVD/YouTube quality)
        # -b:a 192k: 192kbps bitrate (high quality)
        # -q:a 2: VBR quality 0-9, where 0 is best (approx 190-250kbps)
        convert_cmd = [
            FFMPEG_PATH, '-y', '-i', temp_audio,
            '-ar', '48000',  # Higher sample rate for better audio quality
            '-ac', '2',      # Stereo
            '-q:a', '2',     # High quality VBR (approx 190-250 kbps)
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

def step2_voice_generation(output_path, text, style='story'):
    """Generates AI voice for the scene."""
    return generate_tts_audio(output_path, text, style)

def step3_video_generation(img_path, aud_path, vid_path, narration, scene_index, aspect_ratio='16:9'):
    """Generates visual content and creates the scene video."""
    return create_scene_video(img_path, aud_path, vid_path, narration, scene_index, aspect_ratio)

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

        # 1. Generate Image (Part of Step 3 Visuals)
        if not generate_ai_image(img_path, scene['image_prompt'], aspect_ratio):
            generate_mock_image(img_path, scene['image_prompt'][:50] + "...", aspect_ratio)

        # 2. Step 2: Voice Generation
        step2_voice_generation(aud_path, scene['narration'], style)

        # 3. Step 3: Video Generation (Scene creation)
        step3_video_generation(img_path, aud_path, vid_path, scene['narration'], i, aspect_ratio)
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
