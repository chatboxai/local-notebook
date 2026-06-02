"""
local-Notebook FunASR Service
==============================
Wraps the funasr Python package and exposes a clean HTTP API.
Supports speaker diarization and long-form audio.

Startup:
    python server.py
    uvicorn server:app --port 8003

Endpoints:
    POST /transcribe    Upload audio, get transcript with speaker labels
    GET  /health        Service health check

Response format (POST /transcribe):
    {
        "success": true,
        "duration": 180000,        # ms
        "speaker_count": 2,
        "full_text": "完整文本...",
        "segments": [
            {
                "speaker": 0,
                "text": "你好",
                "start": 0,        # ms
                "end": 1200        # ms
            }, ...
        ]
    }
"""
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
logger = logging.getLogger("funasr-server")

PORT = int(os.getenv("PORT", "8003"))
MODEL_DIR = os.getenv("MODEL_DIR", None)   # optional custom model path


# ── Schemas ───────────────────────────────────────────────────────────────────

class Segment(BaseModel):
    speaker: int
    text: str
    start: int    # ms
    end: int      # ms


class TranscribeResponse(BaseModel):
    success: bool
    duration: int = 0           # ms
    speaker_count: int = 0
    full_text: str = ""
    segments: list[Segment] = []
    error: Optional[str] = None


# ── App ───────────────────────────────────────────────────────────────────────

asr_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global asr_model
    try:
        from funasr import AutoModel
        logger.info("Loading FunASR model (paraformer-zh + VAD + punc + spk) ...")
        asr_model = AutoModel(
            model="paraformer-zh",
            vad_model="fsmn-vad",
            punc_model="ct-punc",
            spk_model="cam++",
            **({"model_path": MODEL_DIR} if MODEL_DIR else {}),
        )
        logger.info("FunASR model loaded")
    except ImportError:
        logger.error("funasr not installed. Run: pip install funasr")
    except Exception as e:
        logger.error(f"Failed to load FunASR model: {e}")
    yield
    asr_model = None


app = FastAPI(
    title="local-Notebook FunASR Service",
    description="Audio transcription with speaker diarization using FunASR",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Transcribe logic ──────────────────────────────────────────────────────────

def _transcribe(audio_path: str, hotword: Optional[str]) -> TranscribeResponse:
    if asr_model is None:
        return TranscribeResponse(success=False, error="FunASR model not loaded")

    try:
        kwargs: dict = {"input": audio_path, "batch_size_s": 300}
        if hotword:
            kwargs["hotword"] = hotword

        result = asr_model.generate(**kwargs)
    except Exception as e:
        return TranscribeResponse(success=False, error=f"Transcription failed: {e}")

    if not result:
        return TranscribeResponse(success=False, error="Empty result from model")

    # result is a list of dicts per audio file (we send one file)
    item = result[0] if isinstance(result, list) else result

    segments: list[Segment] = []
    full_text_parts: list[str] = []
    max_end_ms: int = 0
    speakers: set[int] = set()

    # FunASR returns sentence_info list when speaker model is enabled
    for sent in item.get("sentence_info", []):
        spk  = int(sent.get("spk", 0))
        text = sent.get("text", "").strip()
        # timestamps are in ms
        start = int(sent.get("start", 0))
        end   = int(sent.get("end", 0))

        if not text:
            continue
        segments.append(Segment(speaker=spk, text=text, start=start, end=end))
        full_text_parts.append(text)
        speakers.add(spk)
        max_end_ms = max(max_end_ms, end)

    # Fallback: no sentence_info → use raw text
    if not segments:
        raw = item.get("text", "")
        segments = [Segment(speaker=0, text=raw, start=0, end=0)]
        full_text_parts = [raw]

    logger.info(f"Transcribed {max_end_ms}ms, {len(speakers)} speakers, {len(segments)} segments")
    return TranscribeResponse(
        success=True,
        duration=max_end_ms,
        speaker_count=len(speakers) or 1,
        full_text=" ".join(full_text_parts),
        segments=segments,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

SUPPORTED_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".mp4"}


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok" if asr_model is not None else "degraded",
        "model_loaded": asr_model is not None,
    }


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(...),
    hotword: Optional[str] = Form(None),   # space-separated hot words
) -> TranscribeResponse:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in SUPPORTED_EXTS:
        raise HTTPException(status_code=422, detail=f"Unsupported format: {ext}")

    if asr_model is None:
        raise HTTPException(status_code=503, detail="FunASR model not loaded")

    import asyncio
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _transcribe, tmp_path, hotword)
        return result
    finally:
        os.unlink(tmp_path)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=False)
