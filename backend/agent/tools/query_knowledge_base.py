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
        self.workflow_id: str = ""
        self.current_step_id: str = ""
        self.current_feature_id: str = ""
        self.depends_on: list[str] = []
        self.workflow_citation_to_local: dict[str, str] = {}



class QueryKBParams(BaseModel):
    query: str = Field(description="Search query describing the information you want to find.")
    num: int = Field(default=8, description="Number of results to return. Default is 8.")
    file_names: Optional[list[str]] = Field(
        default=None,
        description=(
            "Optional list of file names to restrict the search to. "
            "If omitted, search all files available in the current scope."
        ),
    )
    include_images: bool = Field(
        default=True,
        description="Whether to search images as well. Default is True.",
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
        "Run semantic search over the knowledge base and return relevant text "
        "summaries, image summaries, and citation markers. All factual content "
        "must be grounded in this tool's results and cited with `[citation_X]`."
    )
    params: type[QueryKBParams] = QueryKBParams

    def __init__(self, citation_state: Optional[CitationState] = None):
        super().__init__()
        self.state = citation_state or CitationState()

    async def __call__(self, params: QueryKBParams) -> ToolReturnValue:
        query = params.query.strip()
        if not query:
            return ToolError(message="query must not be empty")

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
                return ToolError(message=f"Files not found: {', '.join(file_names)}")
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
            return ToolError(message=f"Embedding service is unavailable: {e}")

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
            return ToolOk(output=json.dumps([{"message": "No relevant content found"}], ensure_ascii=False))

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
            "_hint": (
                "These results contain summaries only. To retrieve complete original "
                "text, call read_segments with citation_ids. For deeper image "
                "analysis, call ask_image with image_id. All citations must use the "
                "full `[citation_X]` format, and unsupported content must not be fabricated."
            )
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
                    "summary": f"[Image] {summary}",
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
                "summary": f"[Image] {summary}",
                "type": "image",
            })

        return results
