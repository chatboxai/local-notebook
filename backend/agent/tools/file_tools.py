import asyncio
import glob
import json
import logging
import os
import sqlite3
from typing import Optional

from pydantic import BaseModel, Field

from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnValue

from agent.tools.query_knowledge_base import CitationState

logger = logging.getLogger("tool.file_tools")

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "bmp"}
AUDIO_EXTENSIONS = {"wav", "mp3", "m4a", "wma"}


def _get_db_path() -> str:
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./local_notebook.db")
    if "///" in db_url:
        return db_url.split("///")[-1]
    return "local_notebook.db"


def _db_query(sql: str, params: tuple) -> list[dict]:
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _get_file_by_name(project_id: str, file_name: str, file_ids: Optional[list[str]]) -> Optional[dict]:
    rows = _db_query(
        "SELECT id, file_name, file_path, file_type, file_size, status FROM files "
        "WHERE project_id = ? AND file_name = ? LIMIT 1",
        (project_id, file_name),
    )
    if not rows:
        return None
    row = rows[0]
    if file_ids and row["id"] not in file_ids:
        return None
    return row


def _get_pdf_image_path(file_path: str, image_index: int) -> Optional[str]:
    img_dir = os.path.join(os.path.dirname(file_path), "images")
    if not os.path.isdir(img_dir):
        return None
    image_files = sorted([
        f for f in glob.glob(os.path.join(img_dir, "*"))
        if os.path.isfile(f) and f.lower().rsplit(".", 1)[-1] in IMAGE_EXTENSIONS
    ])
    if image_index < len(image_files):
        return image_files[image_index]
    return None


class ListFilesParams(BaseModel):
    pass


class ListFilesTool(CallableTool2[ListFilesParams]):
    name: str = "list_files"
    description: str = "列出当前对话可用的文件。如需文件详细信息，请使用 get_file_meta。"
    params: type[ListFilesParams] = ListFilesParams

    def __init__(self, citation_state: Optional[CitationState] = None):
        super().__init__()
        self.state = citation_state or CitationState()

    async def __call__(self, params: ListFilesParams) -> ToolReturnValue:
        state = self.state

        rows = await asyncio.to_thread(
            _db_query,
            "SELECT id, file_name, file_type, file_size, status, summary FROM files WHERE project_id = ?",
            (state.project_id,),
        )

        if state.file_ids:
            allowed = set(state.file_ids)
            rows = [r for r in rows if r["id"] in allowed]

        result = []
        for r in rows:
            ft = (r["file_type"] or "").lower()
            item = {
                "file_name": r["file_name"],
                "file_type": ft,
                "is_image": ft in IMAGE_EXTENSIONS,
                "is_audio": ft in AUDIO_EXTENSIONS,
                "status": r["status"],
            }
            if r.get("summary"):
                item["summary"] = r["summary"]
            result.append(item)

        logger.info(f"[list_files] project={state.project_id} count={len(result)}")
        return ToolOk(output=json.dumps(result, ensure_ascii=False))


class GetFileMetaParams(BaseModel):
    file_name: str = Field(description="文件名")


class GetFileMetaTool(CallableTool2[GetFileMetaParams]):
    name: str = "get_file_meta"
    description: str = (
        "获取文件的元信息。文档返回段落数量和摘要；"
        "图片文件返回 VLM 生成的描述；音频文件返回段落数。"
    )
    params: type[GetFileMetaParams] = GetFileMetaParams

    def __init__(self, citation_state: Optional[CitationState] = None):
        super().__init__()
        self.state = citation_state or CitationState()

    async def __call__(self, params: GetFileMetaParams) -> ToolReturnValue:
        state = self.state
        file_name = params.file_name.strip()
        if not file_name:
            return ToolError(message="file_name 不能为空")

        file_row = await asyncio.to_thread(
            _get_file_by_name, state.project_id, file_name, state.file_ids
        )
        if not file_row:
            return ToolOk(output=json.dumps(
                {"error": f"未找到文件 '{file_name}'，请使用 list_files 查看可用文件"},
                ensure_ascii=False,
            ))

        file_id = file_row["id"]
        ft = (file_row["file_type"] or "").lower()
        is_image = ft in IMAGE_EXTENSIONS
        is_audio = ft in AUDIO_EXTENSIONS

        if is_image:
            img_rows = await asyncio.to_thread(
                _db_query,
                "SELECT description, vlm_model FROM images WHERE file_id = ? ORDER BY image_index LIMIT 1",
                (file_id,),
            )
            description = img_rows[0]["description"] if img_rows else "（暂无描述）"
            return ToolOk(output=json.dumps({
                "file_name": file_row["file_name"],
                "file_type": ft,
                "is_image": True,
                "description": description,
            }, ensure_ascii=False))

        if is_audio:
            seg_count_rows = await asyncio.to_thread(
                _db_query,
                "SELECT COUNT(*) AS cnt FROM segments WHERE file_id = ?",
                (file_id,),
            )
            seg_count = seg_count_rows[0]["cnt"] if seg_count_rows else 0
            return ToolOk(output=json.dumps({
                "file_name": file_row["file_name"],
                "file_type": ft,
                "is_audio": True,
                "segment_count": seg_count,
            }, ensure_ascii=False))

        seg_count_rows = await asyncio.to_thread(
            _db_query,
            "SELECT COUNT(*) AS cnt FROM segments WHERE file_id = ?",
            (file_id,),
        )
        seg_count = seg_count_rows[0]["cnt"] if seg_count_rows else 0

        logger.info(f"[get_file_meta] file={file_name} type={ft} segments={seg_count}")
        return ToolOk(output=json.dumps({
            "file_name": file_row["file_name"],
            "file_type": ft,
            "is_image": False,
            "is_audio": False,
            "file_size_bytes": file_row.get("file_size"),
            "segment_count": seg_count,
            "status": file_row["status"],
        }, ensure_ascii=False))


class AskImageParams(BaseModel):
    file_name: str = Field(
        description="文件名。对于直接图片文件，传入图片文件名；对于 PDF 内嵌图片，传入 PDF 文件名。"
    )
    question: str = Field(
        description="要问的问题，如：这张图片的主要内容是什么？图中有哪些文字？"
    )
    image_id: Optional[str] = Field(
        default=None,
        description=(
            "PDF 内嵌图片的标识符（可选）。仅当查询 PDF 中的图片时需要，"
            "来自 query_knowledge_base 搜索图片结果中的 image_id 字段，"
            "格式为 {file_id}_img_{image_index}。"
        ),
    )


class AskImageTool(CallableTool2[AskImageParams]):
    name: str = "ask_image"
    description: str = (
        "对指定图片提问，使用视觉语言模型分析图片并回答问题。"
        "支持两种场景：直接图片文件（传 file_name）；PDF 内嵌图片（传 file_name + image_id）。"
    )
    params: type[AskImageParams] = AskImageParams

    def __init__(self, citation_state: Optional[CitationState] = None):
        super().__init__()
        self.state = citation_state or CitationState()

    async def __call__(self, params: AskImageParams) -> ToolReturnValue:
        state = self.state
        file_name = params.file_name.strip()
        question = params.question.strip()
        image_id = (params.image_id or "").strip()

        if not file_name:
            return ToolError(message="file_name 不能为空")
        if not question:
            return ToolError(message="question 不能为空")

        file_row = await asyncio.to_thread(
            _get_file_by_name, state.project_id, file_name, state.file_ids
        )
        if not file_row:
            return ToolOk(output=json.dumps(
                {"error": f"未找到文件 '{file_name}'，请使用 list_files 查看可用文件"},
                ensure_ascii=False,
            ))

        file_id = file_row["id"]
        ft = (file_row["file_type"] or "").lower()
        file_path = file_row["file_path"]

        if image_id:
            return await self._ask_pdf_image(
                file_id=file_id,
                file_name=file_name,
                file_path=file_path,
                image_id=image_id,
                question=question,
                state=state,
            )

        if ft not in IMAGE_EXTENSIONS:
            return ToolOk(output=json.dumps(
                {"error": f"'{file_name}' 不是图片文件。如需查询 PDF 中的图片，请提供 image_id 参数。"},
                ensure_ascii=False,
            ))

        if not os.path.exists(file_path):
            return ToolOk(output=json.dumps(
                {"error": f"图片文件不存在: {file_path}"},
                ensure_ascii=False,
            ))

        answer = await self._call_vlm(file_path, question)
        if answer is None:
            return ToolOk(output=json.dumps(
                {"error": "VLM 调用失败，请检查 VLM 配置"},
                ensure_ascii=False,
            ))

        citation_id = f"citation_{state.citation_counter}"
        state.citations_map[citation_id] = {
            "type": "image",
            "file_id": file_id,
            "file_name": file_name,
            "question": question,
            "answer": answer[:200] + "..." if len(answer) > 200 else answer,
        }
        state.citation_counter += 1

        logger.info(f"[ask_image] direct image file={file_name} citation={citation_id}")
        return ToolOk(output=json.dumps({
            "citation_id": f"[{citation_id}]",
            "file_name": file_name,
            "question": question,
            "answer": answer,
        }, ensure_ascii=False))

    async def _ask_pdf_image(
        self,
        file_id: str,
        file_name: str,
        file_path: str,
        image_id: str,
        question: str,
        state: CitationState,
    ) -> ToolReturnValue:
        img_sep = image_id.rfind("_img_")
        if img_sep == -1:
            return ToolOk(output=json.dumps(
                {"error": f"image_id 格式不正确: {image_id}，应为 {{file_id}}_img_{{index}}"},
                ensure_ascii=False,
            ))
        try:
            image_index = int(image_id[img_sep + 5:])
        except ValueError:
            return ToolOk(output=json.dumps(
                {"error": f"无法从 image_id 解析 image_index: {image_id}"},
                ensure_ascii=False,
            ))

        img_path = await asyncio.to_thread(_get_pdf_image_path, file_path, image_index)
        if not img_path:
            return ToolOk(output=json.dumps({
                "error": f"未找到 image_index={image_index} 对应的图片文件",
                "hint": "图片可能在 PDF 解析时未被提取，请确认 MinerU 已正确解析该 PDF",
            }, ensure_ascii=False))

        answer = await self._call_vlm(img_path, question)
        if answer is None:
            return ToolOk(output=json.dumps(
                {"error": "VLM 调用失败，请检查 VLM 配置"},
                ensure_ascii=False,
            ))

        citation_id = f"citation_{state.citation_counter}"
        state.citations_map[citation_id] = {
            "type": "pdf_image",
            "file_id": file_id,
            "file_name": file_name,
            "image_id": image_id,
            "image_index": image_index,
            "question": question,
            "answer": answer[:200] + "..." if len(answer) > 200 else answer,
        }
        state.citation_counter += 1

        logger.info(f"[ask_image] PDF image file={file_name} image_index={image_index} citation={citation_id}")
        return ToolOk(output=json.dumps({
            "citation_id": f"[{citation_id}]",
            "file_name": file_name,
            "image_id": image_id,
            "question": question,
            "answer": answer,
        }, ensure_ascii=False))

    @staticmethod
    async def _call_vlm(image_path: str, question: str) -> Optional[str]:
        from services.vlm_client import describe_image
        try:
            answer, _ = await describe_image(image_path, prompt=question)
            return answer
        except Exception as e:
            logger.warning(f"[ask_image] VLM 调用失败: {e}")
            return None
