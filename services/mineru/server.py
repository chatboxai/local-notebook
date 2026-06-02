"""
local-Notebook MinerU Proxy Service
=====================================
Queue-managed proxy in front of the stock MinerU HTTP service.

Architecture:
    Client (mineru_client.py)  →  this proxy (:8002)  →  MinerU (:8899)

Features:
    - Semaphore(1): only 1 PDF parsed at a time (GPU/memory bound)
    - Bounded queue: up to MAX_QUEUE_SIZE waiting requests; beyond → 503
    - Auto-start: optionally launches MinerU subprocess on startup

Usage:
    python server.py --gpu 0                    # auto-start MinerU on GPU 0
    python server.py --gpu 1 --port 8003        # GPU 1, proxy on port 8003
    python server.py --no-auto-start --mineru-url http://gpu-box:8899

Endpoints:
    POST /file_parse   Proxy to MinerU /file_parse (with queue control)
    GET  /health       Service + queue status
"""
import argparse
import asyncio
import logging
import os
import signal
import subprocess
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
logger = logging.getLogger("mineru-proxy")


# ── CLI args ─────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="MinerU Proxy — queue-managed PDF parsing")
    parser.add_argument("--port", type=int, default=8002, help="Proxy listen port (default: 8002)")
    parser.add_argument("--gpu", type=str, default="0", help="GPU id for MinerU, e.g. 0 or 0,1 (default: 0)")
    parser.add_argument("--mineru-port", type=int, default=8899, help="MinerU upstream port (default: 8899)")
    parser.add_argument("--mineru-url", type=str, default=None, help="Full MinerU upstream URL (overrides --mineru-port)")
    parser.add_argument("--max-queue", type=int, default=3, help="Max waiting requests in queue (default: 3)")
    parser.add_argument("--no-auto-start", action="store_true", help="Don't auto-start MinerU, assume it's already running")
    return parser.parse_args()


_args = parse_args()

PORT = _args.port
MINERU_URL = (_args.mineru_url or f"http://127.0.0.1:{_args.mineru_port}").rstrip("/")
MAX_QUEUE_SIZE = _args.max_queue
GPU = _args.gpu
AUTO_START = not _args.no_auto_start

# ── Concurrency control ─────────────────────────────────────────────────────
_parse_semaphore: asyncio.Semaphore | None = None
_queue_count = 0
_mineru_process: subprocess.Popen | None = None


# ── MinerU subprocess management ─────────────────────────────────────────────

def _is_port_in_use(port: int) -> bool:
    """Check if a TCP port is already in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def _start_mineru() -> subprocess.Popen | None:
    """Start the MinerU service as a subprocess with specified GPU."""
    mineru_port = _args.mineru_port

    if _is_port_in_use(mineru_port):
        logger.error(
            f"Port {mineru_port} is already in use. "
            f"Another MinerU instance may be running. "
            f"Please stop it first or use --mineru-port to specify a different port."
        )
        raise SystemExit(1)

    cmd = ["mineru-api", "--host", "127.0.0.1", "--port", str(mineru_port)]
    env = {
        **os.environ,
        "CUDA_VISIBLE_DEVICES": GPU,
        "MINERU_MODEL_SOURCE": "modelscope",
        "FLASHINFER_DISABLE_VERSION_CHECK": "1",
    }
    try:
        logger.info(f"Starting MinerU: CUDA_VISIBLE_DEVICES={GPU} {' '.join(cmd)}")
        proc = subprocess.Popen(
            cmd,
            env=env,
        )
        logger.info(f"MinerU started (PID={proc.pid}, GPU={GPU})")
        return proc
    except FileNotFoundError:
        logger.error(
            "Command 'mineru-api' not found. "
            "Install MinerU: pip install magic-pdf[full]"
        )
        return None


def _make_minimal_pdf() -> bytes:
    """Generate a minimal valid single-page PDF (~200 bytes) for health check."""
    return (
        b"%PDF-1.0\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 72 72]/Parent 2 0 R/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 22>>stream\nBT /F1 12 Tf (hi) Tj ET\nendstream\nendobj\n"
        b"xref\n0 5\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000210 00000 n \n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n282\n%%EOF\n"
    )


async def _wait_for_mineru(timeout: int = 300) -> bool:
    """Wait until MinerU can actually parse a PDF (model fully loaded)."""
    logger.info(f"Waiting for MinerU at {MINERU_URL} (timeout={timeout}s, using real PDF probe)...")
    pdf_bytes = _make_minimal_pdf()
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{MINERU_URL}/file_parse",
                    files={"files": ("probe.pdf", pdf_bytes, "application/pdf")},
                    data={"parse_method": "auto", "return_md": "true"},
                )
                if resp.status_code == 200:
                    logger.info("MinerU is ready (probe PDF parsed successfully)")
                    return True
                logger.info(f"MinerU probe returned {resp.status_code}, retrying...")
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        except Exception as e:
            logger.debug(f"MinerU probe error: {e}")
        await asyncio.sleep(5)

    logger.error(f"MinerU did not become ready within {timeout}s")
    return False


def _stop_mineru():
    """Gracefully stop the MinerU subprocess."""
    global _mineru_process
    if _mineru_process and _mineru_process.poll() is None:
        logger.info(f"Stopping MinerU (PID={_mineru_process.pid})...")
        _mineru_process.send_signal(signal.SIGTERM)
        try:
            _mineru_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _mineru_process.kill()
        logger.info("MinerU stopped")
    _mineru_process = None


# ── App lifecycle ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _parse_semaphore, _mineru_process

    _parse_semaphore = asyncio.Semaphore(1)

    if AUTO_START:
        _mineru_process = _start_mineru()
        if _mineru_process:
            ready = await _wait_for_mineru()
            if not ready:
                logger.warning("Continuing anyway — MinerU may still be loading")
    else:
        logger.info(f"Auto-start disabled, expecting MinerU at {MINERU_URL}")

    logger.info(
        f"Proxy ready — upstream={MINERU_URL}, "
        f"max_concurrency=1, max_queue={MAX_QUEUE_SIZE}"
    )
    yield

    _stop_mineru()


app = FastAPI(
    title="local-Notebook MinerU Proxy",
    description="Queue-managed proxy for MinerU PDF parsing service",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    """Check proxy and upstream MinerU status with a real PDF probe."""
    upstream_ok = False
    try:
        pdf_bytes = _make_minimal_pdf()
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{MINERU_URL}/file_parse",
                files={"files": ("probe.pdf", pdf_bytes, "application/pdf")},
                data={"parse_method": "auto", "return_md": "true"},
            )
            upstream_ok = resp.status_code == 200
    except Exception:
        pass

    return {
        "status": "ok" if upstream_ok else "degraded",
        "upstream": MINERU_URL,
        "upstream_ok": upstream_ok,
        "queue": _queue_count,
        "max_queue": MAX_QUEUE_SIZE + 1,
    }


@app.post("/file_parse")
async def file_parse(request: Request) -> Response:
    """
    Proxy /file_parse to upstream MinerU with queue control.
    Transparently forwards the multipart request and returns the raw response.
    """
    global _queue_count

    # ── Queue depth check ────────────────────────────────────────────────
    if _queue_count >= MAX_QUEUE_SIZE + 1:  # +1 for the one currently running
        logger.warning(f"Queue full ({_queue_count}/{MAX_QUEUE_SIZE+1}), rejecting")
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "服务繁忙，请稍后重试"},
            headers={"Retry-After": "30"},
        )

    _queue_count += 1
    logger.info(f"Queued request (queue={_queue_count}/{MAX_QUEUE_SIZE+1})")

    try:
        # Read the raw request body to forward as-is
        body = await request.body()
        content_type = request.headers.get("content-type", "")

        async with _parse_semaphore:
            logger.info("Forwarding to MinerU...")
            try:
                async with httpx.AsyncClient(timeout=600) as client:
                    resp = await client.post(
                        f"{MINERU_URL}/file_parse",
                        content=body,
                        headers={"content-type": content_type},
                    )
            except httpx.ConnectError:
                return JSONResponse(
                    status_code=502,
                    content={"success": False, "error": f"无法连接 MinerU 服务: {MINERU_URL}"},
                )
            except httpx.TimeoutException:
                return JSONResponse(
                    status_code=504,
                    content={"success": False, "error": "MinerU 解析超时 (600s)"},
                )

            logger.info(f"MinerU responded: {resp.status_code}")
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                media_type=resp.headers.get("content-type", "application/json"),
            )
    finally:
        _queue_count -= 1


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=False)
