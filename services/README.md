# local-Notebook - Local Model Services

[中文](./README.zh.md)

Each service runs independently and exposes an HTTP endpoint. The main backend connects to these services through the frontend Settings page, and the deployment mode can be switched at any time:

| Service | Default Port | Mode |
|------|---------|------|
| Embedding | 8001 | local service in this directory or API mode with OpenAI/Ollama-compatible services |
| MinerU | 8002 | local service in this directory or API mode with mineru.net |
| FunASR | 8003 | local service in this directory |

---

## Embedding Service

```bash
cd services/embedding
pip install -r requirements.txt
# Mac:       pip install torch          (MPS is enabled automatically)
# Linux CPU: pip install torch --index-url https://download.pytorch.org/whl/cpu
# Linux GPU: pip install torch --index-url https://download.pytorch.org/whl/cu121

MODEL=BAAI/bge-small-zh-v1.5 python server.py
```

Endpoint: `POST http://localhost:8001/embeddings` (OpenAI-compatible)

---

## MinerU Service

```bash
cd services/mineru
pip install -r requirements.txt

python server.py
```

Endpoint: `POST http://localhost:8002/parse` (multipart/form-data, field=`file`)

---

## FunASR Service

```bash
# 1) Install the system audio decoder first. mp3/m4a transcription uses ffmpeg.
# macOS:
brew install ffmpeg
# Ubuntu/Debian:
# sudo apt install ffmpeg

# 2) Install Python dependencies.
cd services/funasr
python -m pip install -U pip setuptools wheel
python -m pip install torch torchaudio
python -m pip install -r requirements.txt

# 3) Start the service.
python server.py
```

The first startup downloads the required models automatically: paraformer-zh, VAD, and speaker diarization.
If transcription fails with `[Errno 2] No such file or directory: 'ffmpeg'`, install `ffmpeg` with the system command above and restart the service.

Endpoint: `POST http://localhost:8003/transcribe` (multipart/form-data, field=`file`)

---

## Settings Page

After starting a service, enter its URL in local-Notebook frontend **Settings -> Embedding / MinerU / FunASR**. Changes take effect without restarting the main backend service.
