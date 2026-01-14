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

STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
    'when', 'where', 'how', 'who', 'why', 'which', 'this', 'that', 'these',
    'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
    'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
    'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves',
    'imagine', 'picture', 'think', 'consider', 'suppose', 'visualize',
    'look', 'see', 'watch', 'notice', 'observe', 'video', 'scene', 'clip',
    'image', 'photo', 'picture', 'shot', 'frame', 'screen', 'camera',
    'did', 'know', 'can', 'could', 'would', 'should', 'will', 'shall',
    'just', 'only', 'very', 'really', 'too', 'quite', 'rather', 'much',
    'so', 'here', 'heres', 'question', 'answer', 'ask', 'asking'
}

def extract_keywords(text, limit=6):
    """Extracts the most relevant keywords from a sentence."""
    # Remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.lower().split()

    # Filter out stopwords and short words
    keywords = [w for w in words if w not in STOPWORDS and len(w) > 2]

    # Deduplicate while preserving order
    seen = set()
    unique_keywords = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            unique_keywords.append(w)

    return " ".join(unique_keywords[:limit])

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
        'story': {'rate': '-35%', 'pitch': '+1Hz'}
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
                'volume=4.5,'             # Boost volume significantly
                'dynaudnorm=p=0.95:s=5,'  # Professional dynamic normalization (increased peak)
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
                'volume=4.5,'             # Boost volume significantly
                'dynaudnorm=p=0.95:s=5,'  # Professional dynamic normalization (increased peak)
                'aecho=0.8:0.88:6:0.4,'   # Subtle room presence
                'highpass=f=80,'          # Remove low-end rumble
                'lowpass=f=15000,'        # Remove harsh high-end hiss
                'atempo=0.80'             # Slower speed (80%) for ChatterboxTTS naturalness
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
    """Attempts to remove watermarks from an image with improved detection."""
    try:
        img = cv2.imread(image_path)
        if img is None: return False

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Create combined mask for watermark detection
        final_mask = np.zeros(gray.shape, dtype=np.uint8)

        # === METHOD 1: Bright text detection (white/light watermarks) ===
        _, bright_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        # === METHOD 2: Semi-transparent gray text (Adobe Stock style) ===
        # These watermarks are often gray (not bright white)
        lower_gray = np.array([180, 180, 180])
        upper_gray = np.array([240, 240, 240])
        gray_mask = cv2.inRange(img, lower_gray, upper_gray)

        # === METHOD 3: Edge-based text detection ===
        edges = cv2.Canny(gray, 50, 150)

        # Combine detection methods
        combined = cv2.bitwise_or(bright_mask, gray_mask)
        combined = cv2.bitwise_or(combined, edges)

        # === LOCATION FILTER: Only target watermark-prone areas ===
        location_mask = np.zeros(gray.shape, dtype=np.uint8)

        # Bottom strip (full width, bottom 15% of image) - most common watermark location
        cv2.rectangle(location_mask, (0, int(h*0.85)), (w, h), 255, -1)

        # Bottom-left corner (extended area)
        cv2.rectangle(location_mask, (0, int(h*0.75)), (int(w*0.35), h), 255, -1)

        # Bottom-right corner (extended area)
        cv2.rectangle(location_mask, (int(w*0.65), int(h*0.75)), (w, h), 255, -1)

        # Top corners (for logos)
        cv2.rectangle(location_mask, (0, 0), (int(w*0.25), int(h*0.12)), 255, -1)
        cv2.rectangle(location_mask, (int(w*0.75), 0), (w, int(h*0.12)), 255, -1)

        # Apply location filter
        detected = cv2.bitwise_and(combined, location_mask)

        # === MORPHOLOGICAL OPERATIONS: Connect text characters ===
        # Dilate to connect letters in watermark text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
        detected = cv2.dilate(detected, kernel, iterations=2)

        # Close gaps in text
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 5))
        detected = cv2.morphologyEx(detected, cv2.MORPH_CLOSE, kernel_close)

        # === CONTOUR FILTERING: Keep only watermark-sized regions ===
        contours, _ = cv2.findContours(detected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, cw, ch = cv2.boundingRect(contour)

            # Filter: watermarks are typically small-medium sized, wide, and near edges
            min_area = 100
            max_area = (h * w) * 0.08  # Max 8% of image
            aspect_ratio = cw / max(ch, 1)

            # Watermark text is usually wider than tall (aspect ratio > 1.5)
            # Or could be a logo (more square-ish)
            if min_area < area < max_area and (aspect_ratio > 1.2 or area < 5000):
                # Check if it's in the edge regions
                is_bottom = y > h * 0.7
                is_top_corner = y < h * 0.15 and (x < w * 0.3 or x > w * 0.7)

                if is_bottom or is_top_corner:
                    cv2.drawContours(final_mask, [contour], -1, 255, -1)

        # Dilate the final mask slightly to cover text edges
        kernel_final = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        final_mask = cv2.dilate(final_mask, kernel_final, iterations=2)

        # Safety Check: Don't process if mask is empty or too large
        mask_pixels = cv2.countNonZero(final_mask)
        total_pixels = h * w

        if mask_pixels == 0:
            print(f"DEBUG: No watermark detected in image", file=sys.stderr)
            return False

        if mask_pixels > (total_pixels * 0.10):
            print(f"DEBUG: Mask too large ({mask_pixels}/{total_pixels}), skipping to avoid damage", file=sys.stderr)
            return False

        # === INPAINTING: Remove the watermark ===
        # Use larger radius for better blending
        result = cv2.inpaint(img, final_mask, 5, cv2.INPAINT_NS)

        # Save the cleaned image
        cv2.imwrite(image_path, result)
        print(f"DEBUG: Successfully cleaned watermark from image ({mask_pixels} pixels)", file=sys.stderr)
        return True

    except Exception as e:
        print(f"Warning: Watermark cleaning failed: {e}", file=sys.stderr)
        return False

def create_scene_video(image_path, audio_path, output_path, narration, scene_index=0, aspect_ratio='16:9'):
    """Creates cinema-quality video with dynamic Ken Burns effects and modern subtitles."""
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

    # === DYNAMIC KEN BURNS EFFECTS ===
    # 6 different motion patterns for variety
    motion_patterns = [
        # Pattern 0: Slow zoom in from center
        {"zoom": "min(zoom+0.0008,1.25)", "x": "iw/2-(iw/zoom/2)", "y": "ih/2-(ih/zoom/2)"},
        # Pattern 1: Slow zoom out from center
        {"zoom": "max(1.25-0.0008*on,1.0)", "x": "iw/2-(iw/zoom/2)", "y": "ih/2-(ih/zoom/2)"},
        # Pattern 2: Pan left to right with slight zoom
        {"zoom": "min(zoom+0.0003,1.15)", "x": "on/({})*iw/4".format(total_frames), "y": "ih/2-(ih/zoom/2)"},
        # Pattern 3: Pan right to left with slight zoom
        {"zoom": "min(zoom+0.0003,1.15)", "x": "iw/4-on/({})*iw/4".format(total_frames), "y": "ih/2-(ih/zoom/2)"},
        # Pattern 4: Zoom in on upper third (good for faces)
        {"zoom": "min(zoom+0.0006,1.2)", "x": "iw/2-(iw/zoom/2)", "y": "ih/4-(ih/zoom/2)"},
        # Pattern 5: Zoom in on lower third
        {"zoom": "min(zoom+0.0006,1.2)", "x": "iw/2-(iw/zoom/2)", "y": "ih*3/4-(ih/zoom/2)"},
    ]

    pattern = motion_patterns[scene_index % len(motion_patterns)]
    zoom_expr = pattern["zoom"]
    x_expr = pattern["x"]
    y_expr = pattern["y"]

    # === MODERN SUBTITLE STYLING (TikTok/YouTube Shorts style) ===
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
        subtitles_filter = ""
    else:
        # Calculate duration per word
        duration_per_word = duration / total_words

        # Show 3 words at a time for better readability
        chunks = []
        chunk_size = 3
        for i in range(0, total_words, chunk_size):
            chunk_words = words[i:i + chunk_size]
            start_time = i * duration_per_word
            end_time = min((i + chunk_size) * duration_per_word, duration)
            chunks.append({
                'text': " ".join(chunk_words),
                'start': start_time,
                'end': end_time
            })

        # Modern subtitle styling with white text, black outline, and shadow
        font_size = 64 if aspect_ratio == '16:9' else 80
        # Center-bottom for 16:9, center for 9:16 (TikTok style)
        y_pos = "h-150" if aspect_ratio == '16:9' else "(h-text_h)/2+300"

        drawtext_filters = []
        for chunk in chunks:
            safe_txt = chunk['text'].replace("'", "'\\\\\\''").replace(":", "\\:").replace(",", "\\,")
            safe_txt = safe_txt.replace("\n", " ").replace("\r", "")
            # Modern style: White text with thick black border and subtle shadow
            dt = (
                f"drawtext=text='{safe_txt}':fontfile='{font_path}':"
                f"fontcolor=white:fontsize={font_size}:"
                f"borderw=4:bordercolor=black:"
                f"shadowcolor=black@0.8:shadowx=2:shadowy=2:"
                f"x=(w-text_w)/2:y={y_pos}:"
                f"enable='between(t,{chunk['start']:.3f},{chunk['end']:.3f})'"
            )
            drawtext_filters.append(dt)

        subtitles_filter = ",".join(drawtext_filters)

    # === HIGH QUALITY BASE RESOLUTION ===
    if aspect_ratio == '16:9':
        base_w, base_h = 3840, 2160  # 4K base
    else:
        base_w, base_h = 2160, 3840  # 4K vertical base

    # === CINEMATIC COLOR GRADING ===
    # Slight contrast boost, saturation enhancement, and film-like curves
    color_grading = (
        "eq=contrast=1.08:saturation=1.15:brightness=0.01,"
        "curves=preset=lighter,"
        "unsharp=5:5:0.8:5:5:0.4"  # Subtle sharpening
    )

    # Build video filter chain
    vf_parts = [
        f"scale=w={base_w}:h={base_h}:force_original_aspect_ratio=increase",
        f"crop={base_w}:{base_h}",
        color_grading,
        f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s={width}x{height}:fps={fps}",
        f"fade=t=in:st=0:d=0.4",
        f"fade=t=out:st={max(0, duration-0.4)}:d=0.4",
    ]

    if subtitles_filter:
        vf_parts.append(subtitles_filter)

    vf_parts.extend([
        f"fps={fps}",
        "format=yuv420p"
    ])

    # === HIGH QUALITY ENCODING ===
    command = [
        FFMPEG_PATH, '-y', '-loop', '1', '-i', image_path, '-i', audio_path,
        '-vf', ",".join(vf_parts),
        '-c:v', 'libx264',
        '-preset', 'slow',        # Better compression quality
        '-crf', '17',             # Higher quality (lower = better, 17-18 is near lossless)
        '-profile:v', 'high',     # H.264 High Profile
        '-level', '4.1',          # Compatibility level
        '-tune', 'film',          # Optimize for film content
        '-movflags', '+faststart', # Web optimization
        '-t', str(duration),
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '256k',           # Higher audio bitrate
        '-ar', '48000',
        '-shortest',
        output_path
    ]
    if not run_command(command):
        with open(output_path, 'w') as f: f.write("mock")

def step4_automatic_assembly(output_dir, scene_videos, background_music=None, aspect_ratio='16:9'):
    """Stitches all scenes with crossfade transitions and professional audio mixing."""
    final_video_path = os.path.join(output_dir, "final_video.mp4")
    concat_file_path = os.path.join(output_dir, "concat.txt")
    temp_merged_path = os.path.join(output_dir, "temp_merged.mp4")
    temp_watermarked_path = os.path.join(output_dir, "temp_watermarked.mp4")

    # If only one scene, skip complex assembly
    if len(scene_videos) == 1:
        shutil.copy(scene_videos[0], temp_merged_path)
    elif len(scene_videos) > 1:
        # Use xfade for smooth crossfade transitions between scenes
        # Build complex filter for crossfades
        crossfade_duration = 0.3  # 300ms crossfade

        # Get durations of each video
        durations = []
        for vid in scene_videos:
            try:
                result = subprocess.run([FFPROBE_PATH, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', vid], capture_output=True, text=True)
                durations.append(float(result.stdout.strip()))
            except:
                durations.append(5.0)

        # Build input arguments
        input_args = []
        for vid in scene_videos:
            input_args.extend(['-i', vid])

        # Build xfade filter chain
        if len(scene_videos) == 2:
            # Simple case: 2 videos
            offset = durations[0] - crossfade_duration
            filter_complex = f"[0:v][1:v]xfade=transition=fade:duration={crossfade_duration}:offset={offset}[v];[0:a][1:a]acrossfade=d={crossfade_duration}[a]"
            map_args = ['-map', '[v]', '-map', '[a]']
        else:
            # Multiple videos: chain xfades
            filter_parts = []
            current_offset = 0

            # First xfade
            current_offset = durations[0] - crossfade_duration
            filter_parts.append(f"[0:v][1:v]xfade=transition=fade:duration={crossfade_duration}:offset={current_offset}[v1]")
            filter_parts.append(f"[0:a][1:a]acrossfade=d={crossfade_duration}[a1]")

            # Chain remaining videos
            for i in range(2, len(scene_videos)):
                prev_v = f"v{i-1}"
                prev_a = f"a{i-1}"
                curr_v = f"v{i}" if i < len(scene_videos) - 1 else "v"
                curr_a = f"a{i}" if i < len(scene_videos) - 1 else "a"

                # Calculate offset (previous accumulated duration minus crossfades)
                current_offset += durations[i-1] - crossfade_duration

                filter_parts.append(f"[{prev_v}][{i}:v]xfade=transition=fade:duration={crossfade_duration}:offset={current_offset}[{curr_v}]")
                filter_parts.append(f"[{prev_a}][{i}:a]acrossfade=d={crossfade_duration}[{curr_a}]")

            filter_complex = ";".join(filter_parts)
            map_args = ['-map', '[v]', '-map', '[a]']

        xfade_cmd = [FFMPEG_PATH, '-y'] + input_args + [
            '-filter_complex', filter_complex
        ] + map_args + [
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-c:a', 'aac', '-b:a', '256k',
            temp_merged_path
        ]

        if not run_command(xfade_cmd):
            # Fallback to simple concat if xfade fails
            print("DEBUG: Crossfade failed, using simple concat", file=sys.stderr)
            with open(concat_file_path, 'w') as f:
                for vid in scene_videos:
                    f.write(f"file '{os.path.abspath(vid)}'\n")
            run_command([FFMPEG_PATH, '-y', '-f', 'concat', '-safe', '0', '-i', concat_file_path, '-c', 'copy', temp_merged_path])
    else:
        return None

    if not os.path.exists(temp_merged_path):
        return None

    video_to_process = temp_merged_path

    # Add logo watermark
    if os.path.exists(LOGO_PATH):
        width = 1920 if aspect_ratio == '16:9' else 1080
        logo_w = int(width * 0.08)  # Slightly smaller logo
        logo_filter = f"[1:v]scale={logo_w}:-1,format=rgba,colorchannelmixer=aa=0.7[logo]"
        if run_command([FFMPEG_PATH, '-y', '-i', temp_merged_path, '-i', LOGO_PATH,
                       '-filter_complex', f"{logo_filter};[0:v][logo]overlay=W-w-25:H-h-25",
                       '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-c:a', 'copy', temp_watermarked_path]):
            video_to_process = temp_watermarked_path

    # Mix background music with improved audio levels
    print(f"DEBUG: Background music check - path: {background_music}, exists: {background_music and os.path.exists(background_music)}", file=sys.stderr)
    if background_music and os.path.exists(background_music):
        print(f"DEBUG: Adding background music from: {background_music}", file=sys.stderr)

        # Get video duration for accurate fade-out timing
        video_duration = 0
        try:
            result = subprocess.run([FFPROBE_PATH, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_to_process], capture_output=True, text=True)
            video_duration = float(result.stdout.strip())
            print(f"DEBUG: Video duration: {video_duration} seconds", file=sys.stderr)
        except:
            video_duration = 60.0  # Default fallback
            print(f"DEBUG: Could not get video duration, using default: {video_duration} seconds", file=sys.stderr)

        # Calculate fade-out start time (3 seconds before end)
        fade_out_start = max(0, video_duration - 3)

        music_mix_command = [
            FFMPEG_PATH, '-y', '-i', video_to_process, '-stream_loop', '-1', '-i', background_music,
            '-filter_complex',
            f"[1:a]volume=0.08,afade=t=in:d=2,afade=t=out:st={fade_out_start}:d=3[bg];"  # Lower music, fade in/out
            "[0:a]volume=1.8,dynaudnorm=p=0.9[narr];"  # Boost narration with normalization
            "[narr][bg]amix=inputs=2:duration=first:dropout_transition=2[a]",
            '-map', '0:v', '-map', '[a]',
            '-c:v', 'copy',
            '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
            '-shortest', final_video_path
        ]
        if run_command(music_mix_command):
            print(f"DEBUG: Background music mixed successfully", file=sys.stderr)
            for p in [temp_merged_path, temp_watermarked_path]:
                if os.path.exists(p): os.remove(p)
            return final_video_path
        else:
            print(f"DEBUG: Background music mixing failed, continuing without background music", file=sys.stderr)
    else:
        if background_music:
            print(f"DEBUG: Background music file not found: {background_music}", file=sys.stderr)
        else:
            print(f"DEBUG: No background music path provided", file=sys.stderr)

    # No background music - just rename
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
    last_successful_image = None # For fallback continuity

    for i, scene in enumerate(scenes):
        img_path = os.path.join(output_dir, f"scene_{i}_img.jpg")
        aud_path = os.path.join(output_dir, f"scene_{i}_aud.mp3")
        vid_path = os.path.join(output_dir, f"scene_{i}_vid.mp4")

        # Try to download image from web
        # Retry Logic:
        # 1. Full Query
        # 2. Simplified Query (Keywords)
        # 3. Super Broad Query ("abstract background")

        success = download_web_image(scene['image_prompt'], img_path)

        if not success:
            print(f"DEBUG: Primary search failed for scene {i}. Retrying with simplified keywords...", file=sys.stderr)
            simple_query = extract_keywords(scene['image_prompt'], limit=3)
            success = download_web_image(simple_query, img_path)

        if not success:
            print(f"DEBUG: Secondary search failed. Retrying with broad fallback...", file=sys.stderr)
            success = download_web_image("cinematic background", img_path)

        if not success:
            if last_successful_image and os.path.exists(last_successful_image):
                 # Fallback: Use previous scene's image ("like scene 1")
                 print(f"DEBUG: All searches failed. reusing previous image for scene {i}", file=sys.stderr)
                 shutil.copy(last_successful_image, img_path)
                 success = True
            else:
                # Final Fallback: Generate a random placeholder image from Picsum
                print(f"DEBUG: Falling back to Picsum image for scene {i}", file=sys.stderr)
                width = 1920 if aspect_ratio == "16:9" else 1080
                height = 1080 if aspect_ratio == "16:9" else 1920

                try:
                    url = f"https://picsum.photos/{width}/{height}?sig={int(time.time())}"
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=10) as response:
                        with open(img_path, 'wb') as f:
                            f.write(response.read())
                    success = True
                except Exception as e:
                    print(f"DEBUG: Picsum fallback failed: {e}. Using black image.", file=sys.stderr)
                    dimensions = f"{width}x{height}"
                    run_command([FFMPEG_PATH, '-y', '-f', 'lavfi', '-i', f'color=c=black:s={dimensions}', '-frames:v', '1', img_path])
        else:
            # Clean the downloaded image from watermarks before using it
            clean_watermark(img_path)
            last_successful_image = img_path # Update success tracker

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
