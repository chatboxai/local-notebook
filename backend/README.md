# backend

FastAPI 主服务:对外提供 REST + SSE 接口,内置 ARQ 后台 worker 处理文件解析。

## 目录

| 子目录 | 职责 |
|---|---|
| [routes/](./routes) | API 路由层:`auth` / `project` / `file` / `session` / `chat` / `settings` |
| [agent/](./agent) | 对话核心:`chat_agent`(主 Agent)、`citation_parser`(Block 级引用解析)、`prompts`、`tools/`(Agent 可调用工具) |
| [services/](./services) | 业务服务:`embedding_service` / `vector_service`(连 standalone Milvus)/ `mineru_client`(PDF)/ `segment_service`(切块)/ `summary_service` / `vlm_client` / `export_service` |
| [models/](./models) | SQLAlchemy ORM:`project` / `file` / `segment` / `block` / `session` / `message` / `image` / `settings` |
| [workers/](./workers) | ARQ 后台任务:文件上传后异步解析、切块、向量化 |
| [packages/kosong/](./packages/kosong) | 内置 Agent 推理框架(LLM provider / tool calling / streaming) |
| [dependencies/](./dependencies) | FastAPI 依赖项:`auth`(JWT)等 |
| [schemas/](./schemas) | Pydantic 请求 / 响应 schema |
| `main.py` | 入口:lifespan 内启动 DB、Redis、嵌入式 ARQ worker |
| `config.py` | 配置加载:DB 优先 + env fallback |
| `database.py` | SQLAlchemy engine / session |

## 配置策略

- 所有运行时配置(LLM key、base_url、Embedding mode 等)存 SQLite `settings` 表
- 启动时 `config.load_settings(db)` 读入内存缓存,前端 Settings 页修改后实时刷新
- `.env` 仅作为首次启动默认值,优先级:**DB > env > hardcoded default**

## 关键环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `LOCAL_NOTEBOOK_DATA_DIR` | `./local-notebook-data`(由 docker-compose 注入) | Docker 模式下数据目录 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./local_notebook.db` | SQLAlchemy DSN,可换 PostgreSQL |
| `MILVUS_URI` | `http://localhost:19530` | Standalone Milvus gRPC 地址 |
| `UPLOAD_DIR` | `./uploads` | 上传文件目录 |
| `REDIS_URL` | `redis://localhost:6379` | ARQ worker 必需 |
| `SECRET_KEY` | `change-me-in-production` ⚠ | JWT 签名密钥,**生产必改** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080`(7 天) | JWT 有效期 |
| `WORKER_MAX_JOBS` | `4` | ARQ 并发 |
| `PORT` | `8000` | uvicorn 监听端口 |

## 本地开发(不用 Docker 跑 backend)

需要 **Python 3.12+**,以及两个外部服务:**Redis** 和 **Standalone Milvus**(后者依赖 etcd + minio,共 3 个容器)。

最方便的做法是**让 docker-compose 帮你起依赖**(只起 redis/milvus 三件套,不起 backend),然后你在本机裸跑 Python:

```bash
# 1. 启动 redis + milvus 三件套(在项目根)
docker compose up -d redis etcd minio milvus

# 2. 装 backend 依赖
cd backend
pip install -r requirements.txt

# 3. 设置 env
export REDIS_URL=redis://localhost:6379
export MILVUS_URI=http://localhost:19530
export DATABASE_URL=sqlite+aiosqlite:///./local-notebook-data/local_notebook.db
export UPLOAD_DIR=./local-notebook-data/uploads
export SECRET_KEY=$(openssl rand -hex 32)
mkdir -p ./local-notebook-data/uploads

# 4. 跑 backend
python main.py     # 默认 http://localhost:8000
```

> 注:redis 容器我们对外暴露了 `6379`,milvus 容器暴露了 `19530`。所以 docker compose 起的 infra 可以同时被"docker 内的 backend"和"宿主机的 backend"使用。

如果你完全不想用 docker,需要手动装/起 3 个服务:
- **Redis**:`brew install redis && redis-server`(macOS) 或自行安装
- **Milvus standalone + etcd + minio**:三个独立进程,配置较复杂,**不推荐**,直接 `docker compose up -d redis etcd minio milvus` 简单得多

健康检查:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/redis
```

## 数据流

1. **文件上传** → `routes/file_routes.py` 写入 `UPLOAD_DIR` → 投递到 ARQ
2. **后台解析** → `workers/parsers/` 调用 MinerU(PDF)/ FunASR(音频)→ 切块 (`segment_service`) → 向量化 (`embedding_service`) → 入库 (`vector_service`)
3. **对话** → `routes/chat_routes.py` (SSE) → `agent/chat_agent.py` 推理 → `agent/citation_parser.py` 解析引用 → 流式返回到前端