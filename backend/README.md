# backend

[中文](./README.zh.md)

FastAPI service that exposes REST + SSE APIs and runs an embedded ARQ background worker for file parsing.

## Directory

| Path | Responsibility |
|---|---|
| [routes/](./routes) | API route layer: `auth` / `project` / `file` / `session` / `chat` / `settings` |
| [agent/](./agent) | Chat core: `chat_agent` as the main agent, `citation_parser` for block-level citations, prompts, and callable agent tools |
| [services/](./services) | Domain services: `embedding_service` / `vector_service` for standalone Milvus / `mineru_client` for PDFs / `segment_service` / `summary_service` / `vlm_client` / `export_service` |
| [models/](./models) | SQLAlchemy ORM models: `project` / `file` / `segment` / `block` / `session` / `message` / `image` / `settings` |
| [workers/](./workers) | ARQ background tasks for async file parsing, chunking, and vectorization after upload |
| [packages/kosong/](./packages/kosong) | Built-in agent reasoning framework for LLM providers, tool calling, and streaming |
| [dependencies/](./dependencies) | FastAPI dependencies such as `auth` for JWT |
| [schemas/](./schemas) | Pydantic request and response schemas |
| `main.py` | Entry point: the lifespan hook initializes the DB, Redis, and embedded ARQ worker |
| `config.py` | Configuration loading: database first, then environment fallback |
| `database.py` | SQLAlchemy engine and session setup |

## Configuration Strategy

- Runtime settings such as LLM keys, base URLs, and Embedding mode are stored in the SQLite `settings` table.
- `config.load_settings(db)` loads settings into memory at startup, and frontend Settings changes refresh them immediately.
- `.env` is only used as the initial default source. Priority: **DB > env > hardcoded default**.

## Key Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LOCAL_NOTEBOOK_DATA_DIR` | `./local-notebook-data` injected by docker-compose | Data directory in Docker mode |
| `DATABASE_URL` | `sqlite+aiosqlite:///./local_notebook.db` | SQLAlchemy DSN, replaceable with PostgreSQL |
| `MILVUS_URI` | `http://localhost:19530` | Standalone Milvus gRPC endpoint |
| `UPLOAD_DIR` | `./uploads` | Uploaded file directory |
| `REDIS_URL` | `redis://localhost:6379` | Required by the ARQ worker |
| `SECRET_KEY` | `change-me-in-production` | JWT signing secret, must be changed in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` (7 days) | JWT lifetime |
| `WORKER_MAX_JOBS` | `4` | ARQ concurrency |
| `PORT` | `8000` | uvicorn listen port |

Milvus collection names and IVF_PQ index parameters are data-layout constants in `services/vector_service.py`, not environment variables. Changing them requires a vector-store migration or a full re-index.

## Local Development Without Docker Backend

Requires **Python 3.12+** plus two external services: **Redis** and **Standalone Milvus**. Standalone Milvus depends on etcd and minio, so it uses three containers in total.

The simplest setup is to let docker-compose start only the dependencies, then run the Python backend directly on the host:

```bash
# 1. Start Redis and the Milvus stack from the project root
docker compose up -d redis etcd minio milvus

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Configure environment variables
export LOCAL_NOTEBOOK_DATA_DIR="$(cd .. && pwd)/local-notebook-data"
export REDIS_URL=redis://localhost:6379
export MILVUS_URI=http://localhost:19530
export DATABASE_URL=sqlite+aiosqlite:///${LOCAL_NOTEBOOK_DATA_DIR}/local_notebook.db
export UPLOAD_DIR=${LOCAL_NOTEBOOK_DATA_DIR}/uploads
export SECRET_KEY=$(openssl rand -hex 32)
mkdir -p "${UPLOAD_DIR}"

# 4. Run the backend
python main.py     # default: http://localhost:8000
```

The Redis container exposes `6379`, and the Milvus container exposes `19530`, so the same docker-compose infra can be used by either the Docker backend or the host Python backend.

If you do not want to use Docker at all, you must install and run all services manually:

- **Redis**: `brew install redis && redis-server` on macOS, or install it for your OS.
- **Standalone Milvus + etcd + minio**: these are more complex to run as separate processes. Using `docker compose up -d redis etcd minio milvus` is recommended.

Health checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/redis
```

## Data Flow

1. **File upload** -> `routes/file_routes.py` writes to `UPLOAD_DIR` -> job is queued in ARQ.
2. **Background parsing** -> `workers/parsers/` calls MinerU for PDFs or FunASR for audio -> chunks with `segment_service` -> vectorizes with `embedding_service` -> writes vectors into shared Milvus collections with `vector_service`.
3. **Chat** -> `routes/chat_routes.py` streams SSE -> `agent/chat_agent.py` reasons -> `agent/citation_parser.py` parses citations -> the frontend receives streamed output.
