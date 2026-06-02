import asyncio
import json
import logging
import os
import sqlite3
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnValue

logger = logging.getLogger("tool.query_kb")


class CitationState:

    def __init__(self):
        self.project_id: str = ""
        self.file_ids: Optional[list[str]] = None
        self.citation_counter: int = 0
        self.citations_map: dict = {}
        self.segment_to_citation: dict[str, str] = {}
        self.image_to_citation: dict[str, str] = {}



class QueryKBParams(BaseModel):
    query: str = Field(description="查询文本，描述你想找到的信息")
    num: int = Field(default=8, description="返回结果数量（默认 8）")
    file_names: Optional[list[str]] = Field(
        default=None,
        description="限定检索的文件名列表（可选）。不指定则检索当前范围内所有文件。",
    )
    include_images: bool = Field(
        default=True,
        description="是否同时检索图片（默认 True）",
    )

    @field_validator("file_names", mode="before")
    @classmethod
    def parse_file_names(cls, v):
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            return [v]
        return v


class QueryKnowledgeBaseTool(CallableTool2[QueryKBParams]):
    name: str = "query_knowledge_base"
    description: str = (
        "在知识库中进行语义搜索，返回相关文本片段和图片的摘要及引用标记。"
        "所有事实性内容必须基于此工具的返回结果，并在回答中使用 [citation_X] 标注来源。"
    )
    params: type[QueryKBParams] = QueryKBParams

    def __init__(self, citation_state: Optional[CitationState] = None):
        super().__init__()
        self.state = citation_state or CitationState()

    async def __call__(self, params: QueryKBParams) -> ToolReturnValue:
        query = params.query.strip()
        if not query:
            return ToolError(message="query 不能为空")

        num = params.num
        file_names = params.file_names
        include_images = params.include_images
        state = self.state

        file_ids = state.file_ids
        if file_names:
            resolved_ids = await asyncio.to_thread(
                self._resolve_file_ids_by_name, state.project_id, file_names
            )
            if not resolved_ids:
                return ToolError(message=f"未找到文件：{', '.join(file_names)}")
            if file_ids:
                allowed = set(file_ids)
                file_ids = [fid for fid in resolved_ids if fid in allowed] or resolved_ids
            else:
                file_ids = resolved_ids

        from services.embedding_service import embed_single
        from services.vector_service import search, search_images

        try:
            q_vector = await embed_single(query)
        except RuntimeError as e:
            return ToolError(message=f"Embedding 服务不可用：{e}")

        text_hits = await asyncio.to_thread(
            search,
            project_id=state.project_id,
            query_vector=q_vector,
            file_ids=file_ids or None,
            top_k=num,
        )

        image_hits = []
        if include_images:
            image_hits = await asyncio.to_thread(
                search_images,
                project_id=state.project_id,
                query_vector=q_vector,
                file_ids=file_ids or None,
                top_k=max(3, num // 2),
            )

        if not text_hits and not image_hits:
            return ToolOk(output=json.dumps([{"message": "未找到相关内容"}], ensure_ascii=False))

        results = []

        if text_hits:
            results.append({"_type": "text_results", "count": len(text_hits)})
            text_results = self._add_text_citations(text_hits, state)
            results.extend(text_results)
        
        if image_hits:
            results.append({"_type": "image_results", "count": len(image_hits)})
            image_results = self._add_image_citations(image_hits, state)
            results.extend(image_results)

        callable_params = {}
        text_citation_ids = [r["citation_id"] for r in results if r.get("type") == "text" and "citation_id" in r]
        if text_citation_ids:
            callable_params["read_segments(citation_ids)"] = text_citation_ids
        image_ids = [r["image_id"] for r in results if r.get("type") == "image" and "image_id" in r]
        if image_ids:
            callable_params["ask_image(image_id)"] = image_ids
        if callable_params:
            results.append({"_callable_params": callable_params})

        results.append({
            "_hint": "以上仅返回片段摘要。如需完整原文请调用 read_segments 并传入 citation_ids；如需深入分析图片请调用 ask_image 并传入 image_id。所有引用必须使用完整的 [citation_X] 格式标注，禁止编造未经检索的内容。"
        })

        output = json.dumps(results, ensure_ascii=False)
        logger.info(f"[query_kb] query={query!r} text_hits={len(text_hits)} image_hits={len(image_hits)} citations_total={state.citation_counter}")
        return ToolOk(output=output)

    @staticmethod
    def _resolve_file_ids_by_name(project_id: str, file_names: list[str]) -> list[str]:
        db_path = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./local_notebook.db")
        if db_path.startswith("sqlite"):
            db_path = db_path.split("///")[-1]
        try:
            conn = sqlite3.connect(db_path)
            placeholders = ",".join("?" * len(file_names))
            rows = conn.execute(
                f"SELECT id FROM files WHERE project_id = ? AND file_name IN ({placeholders})",
                [project_id] + file_names,
            ).fetchall()
            conn.close()
            return [row[0] for row in rows]
        except Exception:
            return []

    @staticmethod
    def _add_text_citations(hits: list[dict], state: CitationState) -> list[dict]:
        results = []
        for hit in hits:
            segment_id = hit["segment_id"]
            file_name = hit.get("file_name", "")
            content = hit.get("content", "")
            summary = hit.get("summary") or (content[:150] + "..." if len(content) > 150 else content)

            if segment_id in state.segment_to_citation:
                existing_id = state.segment_to_citation[segment_id]
                results.append({
                    "citation_id": f"[{existing_id}]",
                    "file_name": file_name,
                    "summary": summary,
                    "type": "text",
                    "_reused": True,
                })
                continue

            citation_id = f"citation_{state.citation_counter}"
            state.citations_map[citation_id] = {
                "type": "segment",
                "segment_id": segment_id,
                "file_id": hit["file_id"],
                "file_name": file_name,
                "segment_index": hit["segment_index"],
                "content": content[:300] + "..." if len(content) > 300 else content,
                "summary": summary,
            }
            state.segment_to_citation[segment_id] = citation_id
            state.citation_counter += 1

            results.append({
                "citation_id": f"[{citation_id}]",
                "file_name": file_name,
                "summary": summary,
                "type": "text",
            })

        return results

    @staticmethod
    def _add_image_citations(hits: list[dict], state: CitationState) -> list[dict]:
        results = []
        for hit in hits:
            image_id = hit["image_id"]
            file_name = hit.get("file_name", "")
            description = hit.get("description", "")
            summary = description[:150] + "..." if len(description) > 150 else description

            if image_id in state.image_to_citation:
                existing_id = state.image_to_citation[image_id]
                results.append({
                    "citation_id": f"[{existing_id}]",
                    "file_name": file_name,
                    "summary": f"[图片] {summary}",
                    "type": "image",
                    "_reused": True,
                })
                continue

            citation_id = f"citation_{state.citation_counter}"
            state.citations_map[citation_id] = {
                "type": "image",
                "image_id": image_id,
                "file_id": hit["file_id"],
                "file_name": file_name,
                "image_index": hit["image_index"],
                "description": description[:300] + "..." if len(description) > 300 else description,
                "summary": summary,
            }
            state.image_to_citation[image_id] = citation_id
            state.citation_counter += 1

            results.append({
                "citation_id": f"[{citation_id}]",
                "image_id": image_id,
                "file_name": file_name,
                "summary": f"[图片] {summary}",
                "type": "image",
            })

        return results
