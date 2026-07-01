import json
import os
import sqlite3
from typing import Any, Optional


def get_db_path() -> str:
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./local_notebook.db")
    if "///" in db_url:
        return db_url.split("///")[-1]
    return "local_notebook.db"


def _int_or_none(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_pdf_image_location(file_id: str, image_index: int) -> dict[str, Any]:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(
            "SELECT block_id, page, extra FROM blocks WHERE file_id = ? ORDER BY block_index",
            (file_id,),
        ).fetchall()
    finally:
        conn.close()

    for row in rows:
        try:
            extra = json.loads(row["extra"]) if row["extra"] else None
        except (json.JSONDecodeError, TypeError):
            extra = None

        if not isinstance(extra, dict) or not extra.get("is_image"):
            continue

        current_index = _int_or_none(extra.get("image_index"))
        if current_index != image_index:
            continue

        location: dict[str, Any] = {
            "block_id": row["block_id"],
            "page": row["page"] or 0,
        }
        image_name = extra.get("image_name") or extra.get("img_name")
        if image_name:
            location["image_name"] = str(image_name)
        bbox = extra.get("bbox")
        if isinstance(bbox, list):
            location["bbox"] = bbox
        return location

    return {}
