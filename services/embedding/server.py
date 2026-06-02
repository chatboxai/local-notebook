"""
local-Notebook Embedding Service
=================================
OpenAI-compatible embedding server backed by sentence-transformers.

Startup:
    python server.py                        # auto-detect device
    MODEL=BAAI/bge-small-zh-v1.5 python server.py
    uvicorn server:app --port 8001

Device priority: CUDA > MPS (Apple Silicon) > CPU
"""
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Union

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
logger = logging.getLogger("embedding-server")

# ── Config ────────────────────────────────────────────────────────────────────

MODEL_NAME = os.getenv("MODEL", "BAAI/bge-small-zh-v1.5")
PORT = int(os.getenv("PORT", "8001"))
MAX_BATCH = int(os.getenv("MAX_BATCH", "64"))


def _detect_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


# ── App state ─────────────────────────────────────────────────────────────────

model: SentenceTransformer | None = None
device: str = "cpu"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, device
    device = _detect_device()
    logger.info(f"Loading model '{MODEL_NAME}' on device '{device}' ...")
    t0 = time.time()
    model = SentenceTransformer(MODEL_NAME, device=device)
    logger.info(f"Model loaded in {time.time() - t0:.1f}s  |  dim={model.get_sentence_embedding_dimension()}")
    yield
    model = None


app = FastAPI(
    title="local-Notebook Embedding Service",
    description="OpenAI-compatible /embeddings endpoint backed by sentence-transformers",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Schemas (OpenAI compatible) ───────────────────────────────────────────────

class EmbeddingRequest(BaseModel):
    input: Union[str, list[str]]
    model: str | None = None     # accepted but ignored — server uses MODEL_NAME


class EmbeddingObject(BaseModel):
    object: str = "embedding"
    index: int
    embedding: list[float]


class UsageInfo(BaseModel):
    prompt_tokens: int
    total_tokens: int


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[EmbeddingObject]
    model: str
    usage: UsageInfo


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "device": device,
        "dim": model.get_sentence_embedding_dimension() if model else None,
    }


@app.post("/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(req: EmbeddingRequest) -> EmbeddingResponse:
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Normalise to list
    texts: list[str] = [req.input] if isinstance(req.input, str) else req.input

    if not texts:
        raise HTTPException(status_code=422, detail="input must not be empty")

    # Batch encode — run in sync (sentence-transformers releases the GIL)
    import asyncio
    loop = asyncio.get_event_loop()
    vectors = await loop.run_in_executor(
        None,
        lambda: model.encode(
            texts,
            batch_size=MAX_BATCH,
            show_progress_bar=False,
            normalize_embeddings=True,
        ).tolist(),
    )

    token_count = sum(len(t.split()) for t in texts)   # rough estimate

    return EmbeddingResponse(
        model=MODEL_NAME,
        data=[EmbeddingObject(index=i, embedding=v) for i, v in enumerate(vectors)],
        usage=UsageInfo(prompt_tokens=token_count, total_tokens=token_count),
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=False)
