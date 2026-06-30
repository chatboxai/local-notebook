import json
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from agent.tools.query_knowledge_base import CitationState
from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnValue


class CreateWorkflowGenerationParams(BaseModel):
    prompt: str = Field(description="The user's report requirements.")
    title: Optional[str] = Field(default=None, description="Optional report title.")
    file_names: Optional[list[str]] = Field(
        default=None,
        description=(
            "Optional file names to use. If omitted, use files selected in the current "
            "conversation; if none are selected, use all ready files in the project."
        ),
    )

    @field_validator("file_names", mode="before")
    @classmethod
    def parse_file_names(cls, value):
        if value is None or isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            return [value]
        return value


class GetWorkflowGenerationParams(BaseModel):
    workflow_id: Optional[str] = Field(
        default=None,
        description=(
            "Workflow id returned by create_workflow_generation. If omitted, list "
            "workflow ids and expand only when there are 10 or fewer workflows."
        ),
    )
    include_content: bool = Field(
        default=True,
        description="Whether to include generated section content when available.",
    )
    max_chars_per_step: int = Field(
        default=2000,
        description="Maximum characters of generated content to return per step.",
    )


class CreateWorkflowGenerationTool(CallableTool2[CreateWorkflowGenerationParams]):
    name: str = "create_workflow_generation"
    description: str = (
        "Start an asynchronous report workflow in the right-side report panel. "
        "Report generation can take a long time; do not wait for completion or poll "
        "repeatedly. After this tool succeeds, tell the user generation has started."
    )
    params: type[CreateWorkflowGenerationParams] = CreateWorkflowGenerationParams

    def __init__(
        self,
        citation_state: Optional[CitationState] = None,
        redis=None,
        output_language: str | None = None,
    ):
        super().__init__()
        self.state = citation_state or CitationState()
        self.redis = redis
        self.output_language = (output_language or "English").strip()

    async def __call__(self, params: CreateWorkflowGenerationParams) -> ToolReturnValue:
        prompt = (params.prompt or "").strip()
        if not prompt:
            return ToolError(message="prompt must not be empty")
        if not self.state.project_id:
            return ToolError(message="Project context is not available.")
        if self.redis is None:
            return ToolError(message="Background task service is unavailable.")

        output_language = self.output_language or "English"

        try:
            file_ids = await _resolve_workflow_file_ids(
                project_id=self.state.project_id,
                selected_file_ids=self.state.file_ids,
                file_names=params.file_names,
            )
        except ValueError as exc:
            return ToolError(message=str(exc))

        if not file_ids:
            return ToolError(message="No ready files are available for workflow generation.")

        from database import AsyncSessionLocal
        from models.workflow import Workflow
        from services.workflow_titles import ensure_unique_workflow_title

        title = (params.title or "").strip()

        async with AsyncSessionLocal() as db:
            workflow_title = (
                await ensure_unique_workflow_title(db, self.state.project_id, title)
                if title
                else None
            )
            wf = Workflow(
                project_id=self.state.project_id,
                workflow_type="custom",
                title=workflow_title,
                status="pending",
                custom_prompt=prompt,
                file_ids_json=json.dumps(file_ids, ensure_ascii=False),
            )
            db.add(wf)
            await db.commit()
            await db.refresh(wf)

            try:
                await self.redis.enqueue_job(
                    "generate_workflow_task",
                    wf.id,
                    output_language,
                )
            except Exception as exc:
                wf.status = "failed"
                wf.error_message = f"Background task failed to start: {exc}"
                await db.commit()
                return ToolError(message=f"Failed to start workflow generation: {exc}")

            result = {
                "workflow_id": wf.id,
                "title": wf.title or "Workflow",
                "status": wf.status,
                "message": (
                    "Workflow generation has started. It is asynchronous and may take "
                    "a long time; do not wait for it to finish in this chat turn."
                ),
            }

        ret = ToolOk(output=json.dumps(result, ensure_ascii=False))
        ret.extras = {
            "workflow_started": {
                "workflow_id": result["workflow_id"],
                "status": result["status"],
                "display_name": result["title"],
            }
        }
        return ret


class GetWorkflowGenerationTool(CallableTool2[GetWorkflowGenerationParams]):
    name: str = "get_workflow_generation"
    description: str = (
        "Get status and available content for a report workflow. If it is still "
        "pending, processing, or cancelling, report the current progress and do not "
        "poll repeatedly waiting for completion. Results list workflow ids first; "
        "when more than 10 workflows exist, call again with a specific workflow_id."
    )
    params: type[GetWorkflowGenerationParams] = GetWorkflowGenerationParams

    def __init__(self, citation_state: Optional[CitationState] = None):
        super().__init__()
        self.state = citation_state or CitationState()

    async def __call__(self, params: GetWorkflowGenerationParams) -> ToolReturnValue:
        if not self.state.project_id:
            return ToolError(message="Project context is not available.")

        from database import AsyncSessionLocal
        from models.workflow import Workflow

        async with AsyncSessionLocal() as db:
            all_result = await db.execute(
                select(Workflow)
                .options(selectinload(Workflow.features))
                .where(Workflow.project_id == self.state.project_id)
                .order_by(Workflow.created_at.desc())
            )
            workflows = list(all_result.scalars().unique().all())
            if not workflows:
                return ToolError(message="Workflow not found.")

            workflow_ids = [wf.id for wf in workflows]

            target_workflows = workflows
            if params.workflow_id:
                target_workflows = [wf for wf in workflows if wf.id == params.workflow_id]
                if not target_workflows:
                    return ToolError(message="Workflow not found.")

            response: dict[str, Any] = {
                "workflow_ids": workflow_ids,
            }

            if not params.workflow_id and len(workflows) > 10:
                response["omitted"] = (
                    "More than 10 workflows exist. Use get_workflow_generation with "
                    "a specific workflow_id from workflow_ids to inspect one workflow."
                )
                return ToolOk(output=json.dumps(response, ensure_ascii=False))

            max_chars = max(300, min(params.max_chars_per_step or 2000, 8000))
            response["expanded"] = [
                _build_workflow_detail(
                    wf,
                    include_content=params.include_content,
                    max_chars_per_step=max_chars,
                    citation_state=self.state,
                )
                for wf in target_workflows
            ]

        return ToolOk(output=json.dumps(response, ensure_ascii=False))


def _build_workflow_detail(
    workflow,
    *,
    include_content: bool,
    max_chars_per_step: int,
    citation_state: CitationState,
) -> dict[str, Any]:
    citations = _collect_workflow_citations(workflow)
    citation_id_map = _build_workflow_citation_id_map(workflow.id, citations)
    _register_workflow_citations(citations, citation_state, citation_id_map)

    item: dict[str, Any] = {
        "id": workflow.id,
        "title": workflow.title or "Workflow",
        "status": workflow.status,
        "progress": _workflow_progress_text(workflow),
    }
    if workflow.error_message:
        item["error"] = workflow.error_message

    steps = [
        {
            "index": feature.step_index,
            "name": feature.step_name,
            "status": feature.status,
        }
        for feature in (workflow.features or [])
    ]
    if steps:
        item["steps"] = steps

    if include_content:
        content = [
            {
                "index": feature.step_index,
                "name": feature.step_name,
                "text": _blocks_to_text(
                    feature.get_blocks(),
                    max_chars_per_step,
                    citation_id_map,
                ),
            }
            for feature in (workflow.features or [])
            if feature.status == "completed" and feature.get_blocks()
        ]
        if content:
            item["content"] = content

    return item


def _collect_workflow_citations(workflow) -> dict[str, Any]:
    citations: dict[str, Any] = {}
    citations.update(workflow.get_citations())
    for feature in (workflow.features or []):
        citations.update(feature.get_citations())
    return citations


def _build_workflow_citation_id_map(
    workflow_id: str,
    citations: dict[str, Any],
) -> dict[str, str]:
    suffix = "".join(ch for ch in (workflow_id or "").lower() if ch.isalnum())
    prefix = f"citation_wf_{suffix}" if suffix else "citation_wf"
    mapped: dict[str, str] = {}
    for citation_id in citations.keys():
        if citation_id.startswith("citation_"):
            mapped[citation_id] = f"{prefix}_{citation_id.removeprefix('citation_')}"
    return mapped


def _workflow_progress_text(workflow) -> str:
    progress = workflow.progress()
    total = progress.get("total") or 0
    completed = progress.get("completed") or 0
    failed = progress.get("failed") or 0
    cancelled = progress.get("cancelled") or 0
    current = progress.get("current_step")

    parts = [f"{completed}/{total} completed"]
    if failed:
        parts.append(f"{failed} failed")
    if cancelled:
        parts.append(f"{cancelled} cancelled")
    if current:
        parts.append(f"current: {current}")
    return "; ".join(parts)


async def _resolve_workflow_file_ids(
    *,
    project_id: str,
    selected_file_ids: Optional[list[str]],
    file_names: Optional[list[str]],
) -> list[str]:
    from database import AsyncSessionLocal
    from models.file import File

    selected = set(selected_file_ids or [])
    names = [name.strip() for name in (file_names or []) if name and name.strip()]

    async with AsyncSessionLocal() as db:
        query = select(File).where(File.project_id == project_id)
        if names:
            query = query.where(File.file_name.in_(names))
        elif selected:
            query = query.where(File.id.in_(selected))
        else:
            query = query.where(File.status == "ready")

        result = await db.execute(query)
        files = list(result.scalars().all())

    if names:
        found_names = {file.file_name for file in files}
        missing = [name for name in names if name not in found_names]
        if missing:
            raise ValueError(f"Files not found: {', '.join(missing)}")
        if selected:
            outside_scope = [file.file_name for file in files if file.id not in selected]
            if outside_scope:
                raise ValueError(
                    "These files are not selected in the current conversation: "
                    + ", ".join(outside_scope)
                )

    not_ready = [file.file_name for file in files if file.status != "ready"]
    if not_ready:
        raise ValueError("These files are not ready yet: " + ", ".join(not_ready))

    return [file.id for file in files]


def _register_workflow_citations(
    citations: dict[str, Any],
    state: CitationState,
    citation_id_map: Optional[dict[str, str]] = None,
) -> None:
    for citation_id, meta in (citations or {}).items():
        if not isinstance(meta, dict):
            continue
        state_citation_id = (citation_id_map or {}).get(citation_id, citation_id)
        copied = {key: value for key, value in meta.items() if key != "display_num"}
        state.citations_map[state_citation_id] = copied

        citation_type = copied.get("type")
        segment_id = copied.get("segment_id")
        image_id = copied.get("image_id")
        if citation_type == "segment" and segment_id:
            state.segment_to_citation[segment_id] = state_citation_id
        elif citation_type in {"image", "pdf_image"} and image_id:
            state.image_to_citation[image_id] = state_citation_id


def _blocks_to_text(
    blocks: list[dict[str, Any]],
    max_chars: int,
    citation_id_map: Optional[dict[str, str]] = None,
) -> str:
    lines: list[str] = []
    for block in blocks or []:
        text = _parts_to_text(block.get("content_parts") or [], citation_id_map)
        if not text and block.get("content"):
            text = str(block["content"])
            text = _replace_citation_markers(text, citation_id_map)
        if not text.strip():
            continue

        block_type = block.get("block_type")
        if block_type == "heading":
            level = int(block.get("level") or 3)
            lines.append(f"{'#' * min(max(level, 2), 6)} {text}")
        elif block_type == "list":
            lines.append(f"- {text}")
        elif block_type == "quote":
            lines.append(f"> {text}")
        else:
            lines.append(text)

    content = "\n\n".join(lines).strip()
    if len(content) > max_chars:
        return content[:max_chars].rstrip() + "\n...[truncated]"
    return content


def _parts_to_text(
    parts: list[dict[str, Any]],
    citation_id_map: Optional[dict[str, str]] = None,
) -> str:
    chunks: list[str] = []
    for part in parts:
        if part.get("type") == "text":
            chunks.append(str(part.get("content") or ""))
        elif part.get("type") == "citation_ref":
            citation_id = str(part.get("citation_id") or "")
            if citation_id:
                citation_id = (citation_id_map or {}).get(citation_id, citation_id)
                chunks.append(f"[{citation_id}]")
    return "".join(chunks)


def _replace_citation_markers(
    text: str,
    citation_id_map: Optional[dict[str, str]] = None,
) -> str:
    if not citation_id_map:
        return text
    for old_id, new_id in citation_id_map.items():
        text = text.replace(f"[{old_id}]", f"[{new_id}]")
    return text
