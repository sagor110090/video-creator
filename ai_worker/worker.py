import sys
import json
import os
import subprocess
import urllib.request
import urllib.parse
import time

# Set the absolute path to ffmpeg
FFMPEG_PATH = '/opt/homebrew/bin/ffmpeg'

def run_command(command):
    try:
        # Replace 'ffmpeg' with the absolute path
        if command[0] == 'ffmpeg':
            command[0] = FFMPEG_PATH

        print(f"Running: {' '.join(command)}", file=sys.stderr)
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            return False
        return True
    except FileNotFoundError:
        print(f"Warning: Command '{command[0]}' not found. Mocking output...", file=sys.stderr)
        return False

def generate_ai_image(output_path, prompt):
    """Generates an AI image using Pollinations.ai or a fallback."""
    # 1. Try Pollinations.ai
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={int(time.time())}"
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
        url = f"https://picsum.photos/1280/720?sig={int(time.time())}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"Warning: Picsum failed: {e}. Falling back to mock.", file=sys.stderr)
        return False

def generate_mock_image(output_path, text):
    # Sanitize text for FFmpeg drawtext filter
    safe_text = text.replace("'", "").replace(":", "").replace("\\", "")
    command = [
        FFMPEG_PATH, '-y', '-f', 'lavfi', '-i', 'color=c=blue:s=1280x720:d=1',
        '-vf', f"drawtext=text='{safe_text}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2",
        '-frames:v', '1', output_path
    ]
    if not run_command(command):
        # Fallback: Create an empty file if ffmpeg is missing
        with open(output_path, 'w') as f:
            f.write("mock image content")

def generate_tts_audio(output_path, text):
    """Generates human-like audio using Microsoft Edge TTS."""
    # Path to the edge-tts executable in our venv
    edge_tts_path = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'edge-tts')

    # We'll use a high-quality neural voice
    # en-US-AndrewNeural is a very natural male voice
    # en-US-AvaNeural is also great
    voice = "en-US-AndrewNeural"

    command = [
        edge_tts_path,
        '--text', text,
        '--write-media', output_path,
        '--voice', voice
    ]

    print(f"DEBUG: Generating human-like voice with edge-tts: {voice}", file=sys.stderr)

    if not run_command(command):
        # Fallback to macOS 'say' if edge-tts fails
        print(f"Warning: edge-tts failed. Falling back to macOS 'say'.", file=sys.stderr)
        temp_aiff = output_path.replace('.mp3', '.aiff')
        say_command = ['say', text, '-o', temp_aiff]
        if run_command(say_command):
            convert_command = [
                FFMPEG_PATH, '-y', '-i', temp_aiff,
                '-codec:a', 'libmp3lame', '-qscale:a', '2',
                output_path
            ]
            run_command(convert_command)
            if os.path.exists(temp_aiff):
                os.remove(temp_aiff)
        else:
            # Final fallback to silence
            command_silence = [
                FFMPEG_PATH, '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                '-t', '5', output_path
            ]
            run_command(command_silence)

def create_scene_video(image_path, audio_path, output_path, narration, scene_index=0):
    # Get audio duration to match video length
    command_duration = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
    ]
    # Replace 'ffprobe' with absolute path if needed
    if command_duration[0] == 'ffprobe':
        command_duration[0] = FFMPEG_PATH.replace('ffmpeg', 'ffprobe')

    try:
        result = subprocess.run(command_duration, capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.returncode == 0 else 5.0
    except:
        duration = 5.0

    # Ensure duration is at least 1 second
    duration = max(duration, 1.0)

    # Calculate frames (25 fps)
    total_frames = int(duration * 25)

    # Alternate zoom effects based on scene index
    if scene_index % 2 == 0:
        # Zoom in
        zoom_expr = "min(zoom+0.0015,1.5)"
    else:
        # Zoom out (start at 1.5 and go down)
        zoom_expr = "max(1.5-0.0015*on,1.0)"

    # Subtitles logic: split long text into lines
    words = narration.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 40:
            lines.append(" ".join(current_line))
            current_line = []
    if current_line:
        lines.append(" ".join(current_line))

    safe_narration = "\\\n".join(lines).replace("'", "").replace(":", "")

    # Drawtext filter for subtitles: white text with black border at bottom
    subtitles_filter = f"drawtext=text='{safe_narration}':fontcolor=white:fontsize=36:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-80"

    command = [
        FFMPEG_PATH, '-y', '-loop', '1', '-i', image_path, '-i', audio_path,
        '-vf', f"zoompan=z='{zoom_expr}':d={total_frames}:s=1280x720,{subtitles_filter},format=yuv420p",
        '-c:v', 'libx264', '-t', str(duration), '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', output_path
    ]
    if not run_command(command):
        with open(output_path, 'w') as f:
            f.write("mock video content")

def step2_voice_generation(output_path, text):
    """Generates AI voice for the scene."""
    return generate_tts_audio(output_path, text)

def step3_video_generation(img_path, aud_path, vid_path, narration, scene_index):
    """Generates visual content and creates the scene video."""
    return create_scene_video(img_path, aud_path, vid_path, narration, scene_index)

def step4_automatic_assembly(output_dir, scene_videos, background_music=None):
    """Stitches all scenes into one final .mp4 and adds background music."""
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
        # -stream_loop -1 loops the background music
        # -filter_complex mixes audio: [1:a]volume=0.2 lowers background music, [0:a] is narration
        music_mix_command = [
            FFMPEG_PATH, '-y', '-i', temp_video_path, '-stream_loop', '-1', '-i', background_music,
            '-filter_complex', "[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first[a]",
            '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-shortest', final_video_path
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
    scenes = data['scenes']
    output_dir = data['output_dir']

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"DEBUG: Processing story {story_id} with {len(scenes)} scenes", file=sys.stderr)
    scene_videos = []

    for i, scene in enumerate(scenes):
        print(f"DEBUG: Processing scene {i}", file=sys.stderr)
        img_path = os.path.join(output_dir, f"scene_{i}_img.jpg")
        aud_path = os.path.join(output_dir, f"scene_{i}_aud.mp3")
        vid_path = os.path.join(output_dir, f"scene_{i}_vid.mp4")

        # 1. Generate Image (Part of Step 3 Visuals)
        if not generate_ai_image(img_path, scene['image_prompt']):
            generate_mock_image(img_path, scene['image_prompt'][:50] + "...")

        # 2. Step 2: Voice Generation
        step2_voice_generation(aud_path, scene['narration'])

        # 3. Step 3: Video Generation (Scene creation)
        step3_video_generation(img_path, aud_path, vid_path, scene['narration'], i)
        scene_videos.append(vid_path)

    # 4. Step 4: Automatic Assembly
    print(f"DEBUG: Assembling final video...", file=sys.stderr)

    # Check for background music in public/audio/background.mp3
    # We assume the script is run from the project root
    bg_music_path = os.path.join(os.getcwd(), 'public', 'audio', 'background.mp3')

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
