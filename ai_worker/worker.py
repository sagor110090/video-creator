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
import asyncio
import edge_tts
import cv2
import numpy as np
from PIL import Image
from dotenv import load_dotenv
import torch
from chatterbox.tts import ChatterboxTTS
from chatterbox.vc import ChatterboxVC
from scipy.io import wavfile

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

import random

# Detection for paths for ffmpeg and ffprobe
FFMPEG_PATH = get_executable_path('ffmpeg', '/opt/homebrew/bin/ffmpeg')
FFPROBE_PATH = get_executable_path('ffprobe', '/opt/homebrew/bin/ffprobe')

# Logo Path for watermarking
LOGO_PATH = os.path.join(project_root, 'public', 'logo.png')

# Target Voice Path for voice cloning
TARGET_VOICE_PATH = os.path.join(project_root, 'public', 'audio', 'sample.m4a')

# Initialize Chatterbox models
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Initializing Chatterbox models on {DEVICE}...", file=sys.stderr)
tts_model = ChatterboxTTS.from_pretrained(DEVICE)
vc_model = ChatterboxVC.from_pretrained(DEVICE)
print("Chatterbox models initialized successfully!", file=sys.stderr)

def download_web_image(query, output_path):
    """Downloads a high-quality, watermark-free image from the web with multiple fallbacks."""

    # 1. Try Pexels first if API key is available (Best for watermark-free images)
    pexels_key = os.getenv('PEXELS_API_KEY')
    if pexels_key:
        try:
            url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page=1&orientation=landscape"
            headers = {"Authorization": pexels_key}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('photos'):
                    img_url = data['photos'][0]['src']['large2x']
                    img_res = requests.get(img_url, timeout=10)
                    if img_res.status_code == 200:
                        with open(output_path, 'wb') as f:
                            f.write(img_res.content)
                        return True
        except Exception as e:
            print(f"DEBUG: Pexels fallback: {e}", file=sys.stderr)

    # 2. Refine Yahoo search query to exclude watermarked sites
    search_query = query.replace('"', '').strip()
    ai_keywords = ['highly detailed', '8k', '4k', 'photorealistic', 'masterpiece', 'stock photo', 'premium']
    for word in ai_keywords:
        search_query = re.sub(f'\\b{word}\\b', '', search_query, flags=re.IGNORECASE)

    # Aggressive exclusion of common stock photo sites that use heavy watermarks
    exclude_terms = (
        " -stock -watermark -logo -text -premium -shutterstock -gettyimages -alamy -adobe -depositphotos "
        "-vectorstock -123rf -dreamstime -canstockphoto -istockphoto -pond5 -bigstock -agefotostock"
    )
    search_query = search_query.strip() + exclude_terms

    # Simplify query for search engine
    words = search_query.split()
    if len(words) > 8:
        search_query = ' '.join(words[:8])

    print(f"DEBUG: Searching for clean web image. Query: {search_query}", file=sys.stderr)
    encoded_query = urllib.parse.quote(search_query)

    try:
        # Use filters for large images and creative commons/free types if possible
        yahoo_url = f"https://images.search.yahoo.com/search/images?p={encoded_query}&imgsz=large&imgtype=photo"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}

        response = requests.get(yahoo_url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Extract image URLs
            matches = re.findall(r'"murl":"(http[^"]+)"', response.text)
            if not matches:
                matches = re.findall(r'"iurl":"(http[^"]+)"', response.text)

            # List of domains to strictly avoid (known for heavy watermarking)
            forbidden_domains = [
                'shutterstock.com', 'gettyimages.com', 'alamy.com', 'adobe.com',
                'depositphotos.com', '123rf.com', 'dreamstime.com', 'istockphoto.com',
                'vectorstock.com', 'canstockphoto.com', 'pond5.com', 'bigstockphoto.com'
            ]

            if matches:
                for img_url in matches[:10]: # Check more candidates
                    img_url = img_url.replace('\\/', '/')

                    # Skip if URL contains forbidden domains
                    if any(domain in img_url.lower() for domain in forbidden_domains):
                        continue

                    try:
                        img_response = requests.get(img_url, headers=headers, timeout=8)
                        if img_response.status_code == 200:
                            # Basic image validation
                            content = img_response.content
                            if content.startswith(b'\xff\xd8') or content.startswith(b'\x89PNG'):
                                with open(output_path, 'wb') as f:
                                    f.write(content)
                                print(f"DEBUG: Downloaded clean image from: {img_url}", file=sys.stderr)
                                return True
                    except:
                        continue

        # 3. Final fallback: LoremFlickr (High quality, no watermarks, but random-ish)
        print("DEBUG: Using LoremFlickr fallback", file=sys.stderr)
        clean_q = urllib.parse.quote(query.split(',')[0].strip())
        fallback_url = f"https://loremflickr.com/1920/1080/{clean_q}"
        fb_res = requests.get(fallback_url, timeout=10)
        if fb_res.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(fb_res.content)
            return True

    except Exception as e:
        print(f"Warning: Image search failed: {e}", file=sys.stderr)

    return False

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

def process_text_for_naturalness(text):
    """Cleans text and adds natural punctuation for better cadence without using SSML tags."""
    # Remove any existing SSML-like tags
    text = re.sub(r'<[^>]*>', '', text)

    # Add natural pauses using punctuation that the neural engine understands
    text = text.replace('... ', '... ')
    text = text.replace('. ', '... ') # Pause between sentences
    text = text.replace(', ', ', ')   # Natural breath pause

    return text.strip()

async def generate_tts_audio(output_path, text, style='story', scene_index=0):
    """Generates 100% human-like audio using official parameters for natural cadence."""
    # Voice mapping
    voices = {
        'science_short': 'en-US-SteffanNeural',
        'hollywood_hype': 'en-US-AvaNeural',
        'trade_wave': 'en-GB-RyanNeural',
        'story': 'en-US-AndrewNeural'
    }
    voice = voices.get(style, voices['story'])

    # Clean and enhance text punctuation for better flow
    clean_text = process_text_for_naturalness(text)

    # Personality-based prosody settings
    personalities = {
        'science_short': {'rate': '-15%', 'pitch': '-1Hz'},
        'hollywood_hype': {'rate': '-5%', 'pitch': '+2Hz'},
        'trade_wave': {'rate': '-15%', 'pitch': '-2Hz'},
        'story': {'rate': '-25%', 'pitch': '+1Hz'}
    }
    config = personalities.get(style, personalities['story'])

    # Add "Human Variation" based on scene index to break robotic repetition
    scene_pitch_mod = (scene_index % 3 - 1) * 2 # -2Hz, 0Hz, or +2Hz
    scene_rate_mod = (scene_index % 2) * 2 # 0% or +2%

    base_rate = int(config['rate'].replace('%', ''))
    base_pitch = int(config['pitch'].replace('Hz', ''))

    final_rate = f"{base_rate + scene_rate_mod:+d}%"
    final_pitch = f"{base_pitch + scene_pitch_mod:+d}Hz"

    temp_audio = output_path.replace('.mp3', '_temp.mp3')

    print(f"DEBUG: Generating ultra-realistic human voice: {voice} (Rate: {final_rate}, Pitch: {final_pitch}, Scene {scene_index})", file=sys.stderr)

    success = False
    try:
        communicate = edge_tts.Communicate(clean_text, voice, rate=final_rate, pitch=final_pitch)
        await communicate.save(temp_audio)
        if os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 0:
            success = True
    except Exception as e:
        print(f"Warning: TTS generation failed: {e}. Falling back to plain text.", file=sys.stderr)
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_audio)
            if os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 0:
                success = True
        except Exception as e2:
            print(f"Error: Fallback TTS failed: {e2}", file=sys.stderr)

    if success and os.path.exists(temp_audio):
        # STUDIO QUALITY POST-PROCESSING
        convert_cmd = [
            FFMPEG_PATH, '-y', '-i', temp_audio,
            '-af', (
                'dynaudnorm=p=0.9:s=5,'   # Professional dynamic normalization
                'aecho=0.8:0.88:6:0.4,'   # Subtle room presence
                'highpass=f=80,'          # Remove low-end rumble
                'lowpass=f=15000'         # Remove harsh high-end hiss
            ),
            '-ar', '48000',
            '-ac', '2',
            '-q:a', '0',
            output_path
        ]
        if not run_command(convert_cmd):
            os.replace(temp_audio, output_path)
            success = True

    # Cleanup
    if os.path.exists(temp_audio): os.remove(temp_audio)

    if success: return

    # Fallback to macOS 'say'
    if sys.platform == 'darwin':
        print(f"Warning: Falling back to macOS 'say'.", file=sys.stderr)
        temp_aiff = output_path.replace('.mp3', '.aiff')
        if run_command(['say', text, '-o', temp_aiff]):
            run_command([FFMPEG_PATH, '-y', '-i', temp_aiff, '-ar', '48000', '-ac', '2', '-codec:a', 'libmp3lame', '-qscale:a', '2', output_path])
            if os.path.exists(temp_aiff): os.remove(temp_aiff)
            return

    # Final fallback to silence
    print(f"Warning: Falling back to silence.", file=sys.stderr)
    run_command([FFMPEG_PATH, '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-t', '5', output_path])

async def generate_cloned_voice(output_path, text, target_voice_path=None, scene_index=0):
    """Generates audio using ChatterboxTTS and ChatterboxVC for voice cloning."""
    try:
        print(f"DEBUG: Generating cloned voice with target: {target_voice_path}", file=sys.stderr)

        # First, generate TTS from text
        tts_wav = tts_model.generate(text)

        # Save TTS output to temporary WAV file
        temp_tts_path = output_path.replace('.mp3', '_tts.wav')
        tts_numpy = tts_wav.squeeze(0).numpy()
        wavfile.write(temp_tts_path, tts_model.sr, tts_numpy.astype(np.float32))

        # Convert target voice to WAV if it's not already
        target_wav_path = None
        if target_voice_path and os.path.exists(target_voice_path):
            target_wav_path = output_path.replace('.mp3', '_target.wav')
            if target_voice_path.endswith('.m4a'):
                convert_cmd = [
                    FFMPEG_PATH, '-y', '-i', target_voice_path,
                    '-ar', str(tts_model.sr), '-ac', '1',
                    target_wav_path
                ]
                if not run_command(convert_cmd):
                    print(f"Warning: Failed to convert target voice to WAV", file=sys.stderr)
                    target_wav_path = None
            else:
                target_wav_path = target_voice_path

        # Apply voice cloning to TTS output
        wav = vc_model.generate(temp_tts_path, target_voice_path=target_wav_path)

        # Save final output as WAV first
        temp_output_wav = output_path.replace('.mp3', '_output.wav')
        wav_numpy = wav.squeeze(0).numpy()
        wavfile.write(temp_output_wav, vc_model.sr, wav_numpy.astype(np.float32))

        # Convert to MP3 with quality settings
        convert_cmd = [
            FFMPEG_PATH, '-y', '-i', temp_output_wav,
            '-af', (
                'dynaudnorm=p=0.9:s=5,'   # Professional dynamic normalization
                'aecho=0.8:0.88:6:0.4,'   # Subtle room presence
                'highpass=f=80,'          # Remove low-end rumble
                'lowpass=f=15000,'        # Remove harsh high-end hiss
                'atempo=0.85'             # Slower speed (85%) for ChatterboxTTS naturalness
            ),
            '-ar', '48000',
            '-ac', '2',
            '-q:a', '0',
            output_path
        ]

        success = run_command(convert_cmd)

        # Cleanup temporary files
        for temp_file in [temp_tts_path, temp_output_wav]:
            if target_wav_path and temp_file != target_wav_path and os.path.exists(temp_file):
                os.remove(temp_file)
        if target_wav_path and target_wav_path != target_voice_path and os.path.exists(target_wav_path):
            os.remove(target_wav_path)

        if success and os.path.exists(output_path):
            print(f"DEBUG: Successfully generated cloned voice at {output_path}", file=sys.stderr)
            return

    except Exception as e:
        print(f"Error: Voice cloning failed: {e}", file=sys.stderr)

    # Fallback to edge_tts if voice cloning fails
    print(f"Warning: Falling back to edge_tts for scene {scene_index}", file=sys.stderr)
    await generate_tts_audio(output_path, text, 'story', scene_index)

def clean_watermark(image_path):
    """Attempts to remove watermarks from an image with high precision to avoid blurriness."""
    try:
        img = cv2.imread(image_path)
        if img is None: return False

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # 1. Precise Edge Detection (Canny)
        # Higher thresholds to pick up only strong edges like text/logos
        edges = cv2.Canny(gray, 100, 200)

        # 2. Brightness Mask
        # Watermarks are typically light-colored/white
        _, bright_mask = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)

        # 3. Combine: only keep edges that are also bright
        combined = cv2.bitwise_and(edges, bright_mask)

        # 4. Location-based filtering
        # We only target the bottom-right and bottom-left corners where most watermarks reside.
        # We EXCLUDE the center to prevent blurring the main subject.
        mask = np.zeros(gray.shape, dtype=np.uint8)

        # Bottom-right corner (30% width, 20% height)
        cv2.rectangle(mask, (int(w*0.7), int(h*0.8)), (w, h), 255, -1)
        # Bottom-left corner (30% width, 20% height)
        cv2.rectangle(mask, (0, int(h*0.8)), (int(w*0.3), h), 255, -1)
        # Top-right corner (sometimes used)
        cv2.rectangle(mask, (int(w*0.8), 0), (w, int(h*0.15)), 255, -1)

        # Final mask: detected features inside our hot zones
        final_mask = cv2.bitwise_and(combined, mask)

        # 5. Dilate slightly to cover the thickness of the text strokes
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
        final_mask = cv2.dilate(final_mask, kernel, iterations=1)

        # Safety Check: If the mask is too large, it's likely a false positive
        # Watermarks should not cover more than 5% of the total image area
        total_pixels = h * w
        mask_pixels = cv2.countNonZero(final_mask)
        if mask_pixels == 0 or mask_pixels > (total_pixels * 0.05):
            return False

        # 6. Inpaint using NS (Navier-Stokes) which is often better for preservation than Telea
        # Radius 3 is small enough to avoid significant blur
        result = cv2.inpaint(img, final_mask, 3, cv2.INPAINT_NS)

        # Overwrite the original image
        cv2.imwrite(image_path, result)
        return True
    except Exception as e:
        print(f"Warning: Watermark cleaning failed: {e}", file=sys.stderr)
        return False

def create_scene_video(image_path, audio_path, output_path, narration, scene_index=0, aspect_ratio='16:9'):
    """Creates high-quality video with smooth zoom animation and enhanced subtitles."""
    width, height = (1920, 1080) if aspect_ratio == '16:9' else (1080, 1920)

    # Get audio duration
    try:
        result = subprocess.run([FFPROBE_PATH, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path], capture_output=True, text=True)
        duration = float(result.stdout.strip())
    except:
        duration = 5.0
    duration = max(duration, 1.0)

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
                'text': " ".join(chunk_words),
                'start': start_time,
                'end': end_time
            })

        # Enhanced subtitle styling: Larger and more central
        font_size = 70 if aspect_ratio == '16:9' else 90
        # Position slightly below center for 9:16, or bottom for 16:9
        y_pos = "(h-text_h)/2 + 200" if aspect_ratio == '9:16' else "h-120"

        drawtext_filters = []
        for chunk in chunks:
            safe_txt = chunk['text'].replace("'", "'\\\\\\''").replace(":", "\\:").replace(",", "\\,")
            safe_txt = safe_txt.replace("\n", " ").replace("\r", "")
            dt = (
                f"drawtext=text='{safe_txt}':fontfile='{font_path}':"
                f"fontcolor=#FFFF00:fontsize={font_size}:borderw=5:bordercolor=black:"
                f"shadowcolor=black@0.6:shadowx=3:shadowy=3:"
                f"x=(w-text_w)/2:y={y_pos}:enable='between(t,{chunk['start']:.2f},{chunk['end']:.2f})'"
            )
            drawtext_filters.append(dt)

        subtitles_filter = ",".join(drawtext_filters)

    # To prevent stretching, we first scale and crop the image to the target aspect ratio
    # at a high resolution before applying zoompan.
    if aspect_ratio == '16:9':
        base_w, base_h = 3840, 2160  # 4K base
    else:
        base_w, base_h = 2160, 3840  # 4K vertical base

    # Enhancement filters for a more professional/cinematic look
    # eq: contrast=1.1, saturation=1.2, brightness=0.02
    # unsharp: sharpening for better detail
    enhancements = "eq=contrast=1.1:saturation=1.2:brightness=0.02,unsharp=3:3:1.5:3:3:0.5"

    vf_filters = [
        f"scale=w={base_w}:h={base_h}:force_original_aspect_ratio=increase",
        f"crop={base_w}:{base_h}",
        enhancements,
        f"zoompan=z='{zoom_expr}':d={total_frames}:s={width}x{height}",
        "vignette=PI/4", # Subtle dark edges for focus, applied after zoom to stay fixed
        f"fade=t=in:st=0:d=0.5",
        f"fade=t=out:st={max(0, duration-0.5)}:d=0.5",
        f"{subtitles_filter}",
        f"fps={fps}",
        "format=yuv420p"
    ]

    command = [
        FFMPEG_PATH, '-y', '-loop', '1', '-i', image_path, '-i', audio_path,
        '-vf', ",".join(vf_filters), '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
        '-t', str(duration), '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', output_path
    ]
    if not run_command(command):
        with open(output_path, 'w') as f: f.write("mock")

def step4_automatic_assembly(output_dir, scene_videos, background_music=None, aspect_ratio='16:9'):
    """Stitches all scenes into one final .mp4 with high-quality audio and adds background music."""
    final_video_path = os.path.join(output_dir, "final_video.mp4")
    concat_file_path = os.path.join(output_dir, "concat.txt")
    temp_merged_path = os.path.join(output_dir, "temp_merged.mp4")
    temp_watermarked_path = os.path.join(output_dir, "temp_watermarked.mp4")

    with open(concat_file_path, 'w') as f:
        for vid in scene_videos:
            f.write(f"file '{os.path.abspath(vid)}'\n")

    if not run_command([FFMPEG_PATH, '-y', '-f', 'concat', '-safe', '0', '-i', concat_file_path, '-c', 'copy', temp_merged_path]):
        return None

    video_to_process = temp_merged_path
    if os.path.exists(LOGO_PATH):
        width = 1920 if aspect_ratio == '16:9' else 1080
        logo_w = int(width * 0.10)
        # Position bottom-right: W-w-30:H-h-30
        # Added filter: format=rgba,colorchannelmixer=aa=0.8 (80% opacity for better blending)
        logo_filter = f"[1:v]scale={logo_w}:-1,format=rgba,colorchannelmixer=aa=0.8[logo]"
        if run_command([FFMPEG_PATH, '-y', '-i', temp_merged_path, '-i', LOGO_PATH, '-filter_complex', f"{logo_filter};[0:v][logo]overlay=W-w-30:H-h-30", '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-c:a', 'copy', temp_watermarked_path]):
            video_to_process = temp_watermarked_path

    if background_music and os.path.exists(background_music):
        music_mix_command = [
            FFMPEG_PATH, '-y', '-i', video_to_process, '-stream_loop', '-1', '-i', background_music,
            '-filter_complex', "[1:a]volume=0.10[bg];[0:a]volume=1.5[narr];[narr][bg]amix=inputs=2:duration=first[a]",
            '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', final_video_path
        ]
        if run_command(music_mix_command):
            for p in [temp_merged_path, temp_watermarked_path]:
                if os.path.exists(p): os.remove(p)
            return final_video_path

    if video_to_process == temp_watermarked_path:
        os.rename(temp_watermarked_path, final_video_path)
        if os.path.exists(temp_merged_path): os.remove(temp_merged_path)
    else:
        os.rename(temp_merged_path, final_video_path)

    return final_video_path

async def main():
    if len(sys.argv) < 2:
        print("Error: No input provided", file=sys.stderr)
        return
    try:
        if os.path.exists(sys.argv[1]):
            with open(sys.argv[1], 'r') as f: data = json.load(f)
        else:
            data = json.loads(sys.argv[1])
    except Exception as e:
        print(f"Error parsing input: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return

    output_dir = data['output_dir']
    scenes = data['scenes']
    style = data.get('style', 'story')
    aspect_ratio = data.get('aspect_ratio', '16:9')
    bg_music = data.get('background_music')
    if not bg_music or not os.path.exists(bg_music):
        bg_music = os.path.join(project_root, 'public', 'audio', 'background.mp3')

    if not os.path.exists(output_dir): os.makedirs(output_dir)

    scene_videos = []
    for i, scene in enumerate(scenes):
        img_path = os.path.join(output_dir, f"scene_{i}_img.jpg")
        aud_path = os.path.join(output_dir, f"scene_{i}_aud.mp3")
        vid_path = os.path.join(output_dir, f"scene_{i}_vid.mp4")

        # Try to download image from web
        success = download_web_image(scene['image_prompt'], img_path)

        if not success:
            # Fallback: Generate a black image if download fails
            print(f"DEBUG: Falling back to black image for scene {i}", file=sys.stderr)
            dimensions = "1920x1080" if aspect_ratio == "16:9" else "1080x1920"
            run_command([FFMPEG_PATH, '-y', '-f', 'lavfi', '-i', f'color=c=black:s={dimensions}', '-frames:v', '1', img_path])
        else:
            # Clean the downloaded image from watermarks before using it
            clean_watermark(img_path)

        await generate_cloned_voice(aud_path, scene['narration'], TARGET_VOICE_PATH, i)
        create_scene_video(img_path, aud_path, vid_path, scene['narration'], i, aspect_ratio)
        if os.path.exists(vid_path): scene_videos.append(vid_path)

    if scene_videos:
        final_video = step4_automatic_assembly(output_dir, scene_videos, bg_music, aspect_ratio)
        if final_video:
            print(json.dumps({"video_path": os.path.abspath(final_video)}))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
