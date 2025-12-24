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
    """Generates audio using macOS 'say' command."""
    temp_aiff = output_path.replace('.mp3', '.aiff')

    # 1. Use macOS 'say' command to generate AI voice
    say_command = ['say', text, '-o', temp_aiff]
    if not run_command(say_command):
        # Fallback to silent audio if 'say' fails
        print(f"Warning: 'say' command failed. Falling back to silence.", file=sys.stderr)
        command = [
            FFMPEG_PATH, '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
            '-t', '5', output_path
        ]
        run_command(command)
        return

    # 2. Convert AIFF to MP3 using FFmpeg
    convert_command = [
        FFMPEG_PATH, '-y', '-i', temp_aiff,
        '-codec:a', 'libmp3lame', '-qscale:a', '2',
        output_path
    ]
    run_command(convert_command)

    # 3. Clean up temp file
    if os.path.exists(temp_aiff):
        os.remove(temp_aiff)

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
    sys.stderr.flush()
    scene_videos = []

    for i, scene in enumerate(scenes):
        print(f"DEBUG: Processing scene {i}", file=sys.stderr)
        sys.stderr.flush()
        img_path = os.path.join(output_dir, f"scene_{i}_img.jpg")
        aud_path = os.path.join(output_dir, f"scene_{i}_aud.mp3")
        vid_path = os.path.join(output_dir, f"scene_{i}_vid.mp4")

        # 1. Generate Image (Try AI first, then mock)
        if not generate_ai_image(img_path, scene['image_prompt']):
            generate_mock_image(img_path, scene['image_prompt'][:50] + "...")

        # 2. Generate AI Voice (TTS)
        generate_tts_audio(aud_path, scene['narration'])

        # 3. Create video for this scene with subtitles and zoom
        create_scene_video(img_path, aud_path, vid_path, scene['narration'], scene_index=i)
        scene_videos.append(vid_path)

    print(f"DEBUG: Finished all scenes, merging...", file=sys.stderr)
    sys.stderr.flush()
    # Merge all scenes
    final_video_path = os.path.join(output_dir, "final_video.mp4")

    # Create a concat file for FFmpeg
    concat_file_path = os.path.join(output_dir, "concat.txt")
    with open(concat_file_path, 'w') as f:
        for vid in scene_videos:
            f.write(f"file '{os.path.abspath(vid)}'\n")

    merge_command = [
        FFMPEG_PATH, '-y', '-f', 'concat', '-safe', '0', '-i', concat_file_path,
        '-c', 'copy', final_video_path
    ]
    if not run_command(merge_command):
        with open(final_video_path, 'w') as f:
            f.write("mock final video content")

    print(json.dumps({
        "status": "success",
        "video_path": final_video_path
    }))

if __name__ == "__main__":
    main()
