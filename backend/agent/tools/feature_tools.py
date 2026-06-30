import json
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from agent.tools.query_knowledge_base import CitationState
from agent.tools.workflow_tools import (
    _blocks_to_text,
    _register_workflow_citations,
    _resolve_workflow_file_ids,
)
from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnValue


class CreateFeatureGenerationParams(BaseModel):
    prompt: str = Field(description="The focused output requirements for this quick-tool result.")
    title: Optional[str] = Field(default=None, description="Optional result title.")
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


class GetFeatureGenerationParams(BaseModel):
    feature_id: Optional[str] = Field(
        default=None,
        description=(
            "Feature id returned by create_feature_generation. If omitted, list "
            "quick-tool feature ids and expand only when there are 10 or fewer results."
        ),
    )
    include_content: bool = Field(
        default=True,
        description="Whether to include generated quick-tool content when available.",
    )
    max_chars: int = Field(
        default=4000,
        description="Maximum characters of generated content to return per quick-tool result.",
    )


class CreateFeatureGenerationTool(CallableTool2[CreateFeatureGenerationParams]):
    name: str = "create_feature_generation"
    description: str = (
        "Start one focused generation in the right-side panel's 'Quick tools' "
        "(`快捷工具`) tab. "
        "Use this for a single reusable output that should be easier to find than a chat reply, "
        "such as a positioning analysis, audience profile, summary, comparison, title ideas, "
        "or communication copy. Do not use this for the 'Comprehensive reports' (`综合报告`) tab. "
        "It is asynchronous; after it starts, do not wait for completion."
    )
    params: type[CreateFeatureGenerationParams] = CreateFeatureGenerationParams

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

    async def __call__(self, params: CreateFeatureGenerationParams) -> ToolReturnValue:
        prompt = (params.prompt or "").strip()
        if not prompt:
            return ToolError(message="prompt must not be empty")
        if not self.state.project_id:
            return ToolError(message="Project context is not available.")
        if self.redis is None:
            return ToolError(message="Background task service is unavailable.")

        try:
            file_ids = await _resolve_workflow_file_ids(
                project_id=self.state.project_id,
                selected_file_ids=self.state.file_ids,
                file_names=params.file_names,
            )
        except ValueError as exc:
            return ToolError(message=str(exc))

        if not file_ids:
            return ToolError(message="No ready files are available for quick-tool generation.")

        from database import AsyncSessionLocal
        from models.feature import Feature

        title = (params.title or "").strip() or "Quick tool"
        output_language = self.output_language or "English"

        async with AsyncSessionLocal() as db:
            feature = Feature(
                project_id=self.state.project_id,
                workflow_id=None,
                feature_type="custom_feature",
                step_index=0,
                step_name=title,
                title=title,
                status="pending",
            )
            feature.set_custom_config({
                "prompt": prompt,
                "file_ids": file_ids,
                "output_language": output_language,
            })
            db.add(feature)
            await db.commit()
            await db.refresh(feature)

            try:
                await self.redis.enqueue_job(
                    "generate_feature_task",
                    feature.id,
                    output_language,
                )
            except Exception as exc:
                feature.status = "failed"
                feature.error_message = f"Background task failed to start: {exc}"
                await db.commit()
                return ToolError(message=f"Failed to start quick-tool generation: {exc}")

            result = {
                "feature_id": feature.id,
                "title": feature.title or title,
                "status": feature.status,
                "message": (
                    "Quick-tool generation has started. It is asynchronous; do not "
                    "wait for it to finish in this chat turn."
                ),
            }

        ret = ToolOk(output=json.dumps(result, ensure_ascii=False))
        ret.extras = {
            "feature_started": {
                "feature_id": result["feature_id"],
                "status": result["status"],
                "display_name": result["title"],
            }
        }
        return ret


class GetFeatureGenerationTool(CallableTool2[GetFeatureGenerationParams]):
    name: str = "get_feature_generation"
    description: str = (
        "Get status and available content for results in the right-side panel's "
        "'Quick tools' (`快捷工具`) tab. Use this when the user asks about a quick-tool result, not "
        "a 'Comprehensive reports' (`综合报告`) workflow. If a quick-tool result is still "
        "pending or processing, report the current status and do not poll repeatedly."
    )
    params: type[GetFeatureGenerationParams] = GetFeatureGenerationParams

    def __init__(self, citation_state: Optional[CitationState] = None):
        super().__init__()
        self.state = citation_state or CitationState()

    async def __call__(self, params: GetFeatureGenerationParams) -> ToolReturnValue:
        if not self.state.project_id:
            return ToolError(message="Project context is not available.")

        from database import AsyncSessionLocal
        from models.feature import Feature

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Feature)
                .where(
                    Feature.project_id == self.state.project_id,
                    Feature.workflow_id.is_(None),
                )
                .order_by(Feature.created_at.desc())
            )
            features = list(result.scalars().all())

        if not features:
            return ToolError(message="Quick-tool result not found.")

        feature_ids = [feature.id for feature in features]
        target_features = features
        if params.feature_id:
            target_features = [feature for feature in features if feature.id == params.feature_id]
            if not target_features:
                return ToolError(message="Quick-tool result not found.")

        response: dict[str, Any] = {
            "feature_ids": feature_ids,
        }

        if not params.feature_id and len(features) > 10:
            response["omitted"] = (
                "More than 10 quick-tool results exist. Use get_feature_generation "
                "with a specific feature_id from feature_ids to inspect one result."
            )
            return ToolOk(output=json.dumps(response, ensure_ascii=False))

        max_chars = max(300, min(params.max_chars or 4000, 12000))
        response["expanded"] = [
            _build_feature_detail(
                feature,
                include_content=params.include_content,
                max_chars=max_chars,
                citation_state=self.state,
            )
            for feature in target_features
        ]
        return ToolOk(output=json.dumps(response, ensure_ascii=False))


def _build_feature_detail(
    feature,
    *,
    include_content: bool,
    max_chars: int,
    citation_state: CitationState,
) -> dict[str, Any]:
    citation_id_map = _build_feature_citation_id_map(feature.id, feature.get_citations())
    _register_workflow_citations(feature.get_citations(), citation_state, citation_id_map)

    item: dict[str, Any] = {
        "id": feature.id,
        "title": feature.title or feature.step_name or "Quick tool",
        "type": feature.feature_type,
        "status": feature.status,
        "created_at": feature.created_at.isoformat() if feature.created_at else None,
    }
    if feature.error_message:
        item["error"] = feature.error_message

    if include_content and feature.status == "completed" and feature.get_blocks():
        item["text"] = _blocks_to_text(
            feature.get_blocks(),
            max_chars,
            citation_id_map,
        )

    return item


def _build_feature_citation_id_map(
    feature_id: str,
    citations: dict[str, Any],
) -> dict[str, str]:
    suffix = "".join(ch for ch in (feature_id or "").lower() if ch.isalnum())
    prefix = f"citation_feature_{suffix}" if suffix else "citation_feature"
    mapped: dict[str, str] = {}
    for citation_id in citations.keys():
        if citation_id.startswith("citation_"):
            mapped[citation_id] = f"{prefix}_{citation_id.removeprefix('citation_')}"
    return mapped
