import os
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./local_notebook.db",
)

_connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=_connect_args,
)

if "sqlite" in DATABASE_URL:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        journal_mode = os.getenv("SQLITE_JOURNAL_MODE", "DELETE").upper()
        cursor.execute(f"PRAGMA journal_mode={journal_mode}")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


RUNTIME_SCHEMA_COLUMNS = [
    ("projects", "summary", "TEXT"),
    ("projects", "color", "VARCHAR(20)"),
    ("sessions", "last_total_tokens", "INTEGER"),
    ("sessions", "compact_summary", "TEXT"),
    ("sessions", "compact_citations_json", "TEXT"),
    ("sessions", "compact_message_id", "VARCHAR(36)"),
    ("messages", "deleted_at", "TIMESTAMP"),
]


async def ensure_runtime_schema(conn, logger=None) -> None:
    for table, col, col_type in RUNTIME_SCHEMA_COLUMNS:
        try:
            await conn.execute(
                text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            )
            if logger:
                logger.info(f"Migration: added {table}.{col}")
        except Exception:
            pass
