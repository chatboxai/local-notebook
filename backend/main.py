import os
import sys
os.environ.setdefault("GRPC_DNS_RESOLVER", "native")
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "packages"))

import asyncio
import logging
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from arq.worker import Worker
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("local_notebook")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from database import engine, Base
    import models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        migrate_columns = [
            ("sessions", "last_total_tokens", "INTEGER"),
            ("sessions", "compact_summary", "TEXT"),
            ("sessions", "compact_citations_json", "TEXT"),
            ("sessions", "compact_message_id", "VARCHAR(36)"),
            ("messages", "deleted_at", "TIMESTAMP"),
        ]
        for table, col, col_type in migrate_columns:
            try:
                await conn.execute(
                    __import__("sqlalchemy").text(
                        f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                    )
                )
                logger.info(f"Migration: added {table}.{col}")
            except Exception:
                pass
    logger.info("Database tables verified")

    from database import AsyncSessionLocal
    import config
    async with AsyncSessionLocal() as db:
        await config.load_settings(db)
    logger.info("Settings cache loaded")

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        app.state.redis = await create_pool(RedisSettings.from_dsn(redis_url))
        logger.info(f"Redis connected: {redis_url}")
    except Exception as exc:
        logger.warning(f"Redis unavailable ({exc}) — file parsing will be disabled")
        app.state.redis = None

    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)

    worker = None
    worker_task = None
    if app.state.redis:
        from workers.tasks import WorkerSettings
        worker = Worker(
            functions=WorkerSettings.functions,
            on_startup=WorkerSettings.on_startup,
            on_shutdown=WorkerSettings.on_shutdown,
            redis_settings=RedisSettings.from_dsn(redis_url),
            max_jobs=WorkerSettings.max_jobs,
            job_timeout=WorkerSettings.job_timeout,
            max_tries=WorkerSettings.max_tries,
            retry_jobs=WorkerSettings.retry_jobs,
            handle_signals=False,
        )
        worker_task = asyncio.create_task(worker.async_run())
        logger.info("Embedded ARQ worker started")
    else:
        logger.warning("Redis unavailable — ARQ worker not started, file parsing disabled")

    yield

    if worker and worker_task and not worker_task.done():
        if worker.main_task and not worker.main_task.done():
            worker.main_task.cancel()
        try:
            await asyncio.wait_for(worker_task, timeout=5.0)
        except (asyncio.TimeoutError, asyncio.CancelledError, Exception):
            worker_task.cancel()
        logger.info("Embedded ARQ worker stopped")
    if app.state.redis:
        await app.state.redis.aclose()
    await engine.dispose()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="local-Notebook",
        description="Local-first knowledge base and chat for paper reading",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from routes import (
        auth_router,
        chat_router,
        direct_file_router,
        file_router,
        project_router,
        session_router,
        settings_router,
        workflow_router,
    )

    app.include_router(auth_router,        prefix="/api")
    app.include_router(settings_router,    prefix="/api")
    app.include_router(project_router,     prefix="/api")
    app.include_router(file_router,        prefix="/api")
    app.include_router(direct_file_router, prefix="/api")
    app.include_router(session_router,     prefix="/api")
    app.include_router(chat_router,        prefix="/api")
    app.include_router(workflow_router,    prefix="/api")

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/health/redis", tags=["health"])
    async def health_redis() -> dict:
        if app.state.redis is None:
            return {"status": "unavailable"}
        try:
            await app.state.redis.ping()
            return {"status": "ok"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
