# local-Notebook — 本地模型服务

每个服务独立运行，暴露 HTTP 接口。主 backend 通过 Settings 页配置各服务地址，两种模式可随时切换：

| 服务 | 默认端口 | 模式 |
|------|---------|------|
| Embedding | 8001 | local（此目录）或 API（OpenAI/Ollama） |
| MinerU | 8002 | local（此目录）或 API（mineru.net） |
| FunASR | 8003 | local（此目录） |

---

## Embedding 服务

```bash
cd services/embedding
pip install -r requirements.txt
# Mac:   pip install torch          （自动启用 MPS）
# Linux CPU: pip install torch --index-url https://download.pytorch.org/whl/cpu
# Linux GPU: pip install torch --index-url https://download.pytorch.org/whl/cu121

MODEL=BAAI/bge-small-zh-v1.5 python server.py
```

接口：`POST http://localhost:8001/embeddings`（OpenAI-compatible）

---

## MinerU 服务

```bash
cd services/mineru
pip install -r requirements.txt

python server.py
```

接口：`POST http://localhost:8002/parse`（multipart/form-data，field=file）

---

## FunASR 服务

```bash
cd services/funasr
pip install -r requirements.txt

python server.py
```

首次启动会自动下载模型（paraformer-zh + VAD + 说话人分离）。

接口：`POST http://localhost:8003/transcribe`（multipart/form-data，field=file）

---

## Settings 页配置

启动服务后，在 local-Notebook 前端 **Settings → Embedding / MinerU / FunASR** 填入对应地址即可生效，无需重启主服务。
