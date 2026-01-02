from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import torch
import shutil
import os
import uuid
import tempfile
from chatterbox.tts import ChatterboxTTS
from chatterbox.vc import ChatterboxVC

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
tts_model = ChatterboxTTS.from_pretrained(DEVICE)
vc_model = ChatterboxVC.from_pretrained(DEVICE)

# Create directories
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.get("/")
async def root():
    return FileResponse("index.html")


@app.post("/generate")
async def generate_voice(
    text: str = Form(...),
    target_voice: UploadFile = File(None)
):
    try:
        # Generate unique filenames
        audio_id = str(uuid.uuid4())
        tts_path = f"{UPLOAD_DIR}/{audio_id}_tts.wav"
        output_path = f"{OUTPUT_DIR}/{audio_id}_output.wav"

        # First, generate TTS from text
        tts_wav = tts_model.generate(text)

        # Save TTS output
        import numpy as np
        from scipy.io import wavfile

        tts_numpy = tts_wav.squeeze(0).numpy()
        wavfile.write(tts_path, tts_model.sr, tts_numpy.astype(np.float32))

        # Save target voice if provided
        target_path = None
        if target_voice:
            target_path = f"{UPLOAD_DIR}/{audio_id}_target.wav"
            with open(target_path, "wb") as f:
                shutil.copyfileobj(target_voice.file, f)

        # Apply voice cloning to TTS output
        wav = vc_model.generate(tts_path, target_voice_path=target_path)

        # Save final output
        wav_numpy = wav.squeeze(0).numpy()
        wavfile.write(output_path, vc_model.sr, wav_numpy.astype(np.float32))

        return JSONResponse({
            "success": True,
            "output_path": output_path,
            "sample_rate": vc_model.sr
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/outputs/{filename}")
async def get_output(filename: str):
    path = f"{OUTPUT_DIR}/{filename}"
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="File not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
