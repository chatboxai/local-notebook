import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnValue

from agent.tools.query_knowledge_base import CitationState


class ListWorkflowStepResultsParams(BaseModel):
    pass


class GetWorkflowStepResultsParams(BaseModel):
    step_ids: Optional[List[str]] = Field(
        default=None,
        description=(
            "Optional list of upstream dependency step_ids to read. "
            "If omitted, returns all completed upstream dependency results."
        ),
    )
    max_chars_per_step: int = Field(
        default=3000,
        description="Maximum number of characters returned per dependency result.",
    )

    @field_validator("step_ids", mode="before")
    @classmethod
    def _parse_step_ids(cls, value):
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


class ListWorkflowStepResultsTool(CallableTool2[ListWorkflowStepResultsParams]):
    name: str = "list_workflow_step_results"
    description: str = (
        "List the current report section's upstream dependency steps and whether their "
        "generated results are available. Use this before reading dependency results."
    )
    params: type[ListWorkflowStepResultsParams] = ListWorkflowStepResultsParams

    def __init__(self, citation_state: Optional[CitationState] = None):
        super().__init__()
        self.state = citation_state or CitationState()

    async def __call__(self, params: ListWorkflowStepResultsParams) -> ToolReturnValue:
        if not self.state.workflow_id or not self.state.current_step_id:
            return ToolError(message="Workflow step context is not available.")

        features = await _load_workflow_features(self.state.workflow_id)
        current = _find_current_feature(features, self.state.current_step_id)
        if not current:
            return ToolError(message="Current workflow step was not found.")

        available = []
        by_step_id = {item["step_id"]: item for item in features if item.get("step_id")}
        try:
            upstream_step_ids = _collect_upstream_step_ids(features, self.state.current_step_id)
        except ValueError as exc:
            return ToolError(message=str(exc))

        for step_id in upstream_step_ids:
            item = by_step_id.get(step_id)
            if not item:
                available.append({
                    "step_id": step_id,
                    "status": "missing",
                    "available": False,
                })
                continue
            content = _blocks_to_plain_text(item["blocks"], item["citations"], self.state, remap=False)
            available.append({
                "step_id": step_id,
                "step_name": item["step_name"],
                "status": item["status"],
                "available": item["status"] == "completed" and bool(content.strip()),
                "content_chars": len(content),
            })

        return ToolOk(output=json.dumps({
            "current_step_id": self.state.current_step_id,
            "upstream_dependencies": available,
            "hint": (
                "Call get_workflow_step_results without step_ids to read all completed "
                "upstream dependency results, or pass specific step_ids from this list."
            ),
        }, ensure_ascii=False))


class GetWorkflowStepResultsTool(CallableTool2[GetWorkflowStepResultsParams]):
    name: str = "get_workflow_step_results"
    description: str = (
        "Read generated results from the current section's completed upstream dependency "
        "steps. Returned citations are remapped into this section's local citation space, "
        "so read_segments can be called with those citation ids."
    )
    params: type[GetWorkflowStepResultsParams] = GetWorkflowStepResultsParams

    def __init__(self, citation_state: Optional[CitationState] = None):
        super().__init__()
        self.state = citation_state or CitationState()

    async def __call__(self, params: GetWorkflowStepResultsParams) -> ToolReturnValue:
        if not self.state.workflow_id or not self.state.current_step_id:
            return ToolError(message="Workflow step context is not available.")

        features = await _load_workflow_features(self.state.workflow_id)
        try:
            upstream_step_ids = _collect_upstream_step_ids(features, self.state.current_step_id)
        except ValueError as exc:
            return ToolError(message=str(exc))

        requested = params.step_ids or upstream_step_ids
        if not requested:
            return ToolOk(output=json.dumps({
                "results": [],
                "message": "This step has no upstream dependencies.",
            }, ensure_ascii=False))

        allowed = set(upstream_step_ids)
        disallowed = [step_id for step_id in requested if step_id not in allowed]
        if disallowed:
            return ToolError(message=(
                "Only upstream dependency step results can be read. "
                f"Invalid step_ids: {', '.join(disallowed)}"
            ))

        by_step_id = {item["step_id"]: item for item in features if item.get("step_id")}

        results = []
        errors = []
        max_chars = max(200, min(params.max_chars_per_step or 3000, 12000))
        for step_id in requested:
            item = by_step_id.get(step_id)
            if not item:
                errors.append({"step_id": step_id, "error": "Dependency step was not found."})
                continue
            if item["status"] != "completed":
                errors.append({
                    "step_id": step_id,
                    "step_name": item["step_name"],
                    "status": item["status"],
                    "error": "Dependency step is not completed yet.",
                })
                continue
            content = _blocks_to_plain_text(
                item["blocks"],
                item["citations"],
                self.state,
                remap=True,
            ).strip()
            truncated = len(content) > max_chars
            if truncated:
                content = content[:max_chars].rstrip() + "\n...[truncated]"
            results.append({
                "step_id": step_id,
                "step_name": item["step_name"],
                "content": content,
                "truncated": truncated,
            })

        return ToolOk(output=json.dumps({
            "results": results,
            "errors": errors,
            "hint": (
                "Citations in returned content are local to the current section. "
                "Use read_segments with these citation ids when original text verification is needed."
            ),
        }, ensure_ascii=False))


async def _load_workflow_features(workflow_id: str) -> List[Dict[str, Any]]:
    from database import AsyncSessionLocal
    from models.feature import Feature

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Feature)
            .where(Feature.workflow_id == workflow_id)
            .order_by(Feature.step_index.asc())
        )
        features = list(result.scalars().all())

    items = []
    for feature in features:
        config = feature.get_custom_config()
        step_id = config.get("step_id")
        items.append({
            "id": feature.id,
            "step_id": step_id,
            "step_name": feature.step_name or step_id or "",
            "order_index": feature.step_index,
            "depends_on": config.get("depends_on") or [],
            "status": feature.status,
            "blocks": feature.get_blocks(),
            "citations": feature.get_citations(),
        })
    return items


def _find_current_feature(features: List[Dict[str, Any]], current_step_id: str) -> Optional[Dict[str, Any]]:
    for item in features:
        if item.get("step_id") == current_step_id:
            return item
    return None


def _collect_upstream_step_ids(features: List[Dict[str, Any]], current_step_id: str) -> List[str]:
    by_step_id = {
        item["step_id"]: item
        for item in features
        if item.get("step_id")
    }
    if current_step_id not in by_step_id:
        raise ValueError("Current workflow step was not found.")

    order_index = {
        step_id: int(item.get("order_index") or 0)
        for step_id, item in by_step_id.items()
    }
    visiting: set[str] = set()
    visited: Dict[str, set[str]] = {}

    def collect(step_id: str) -> set[str]:
        if step_id in visited:
            return visited[step_id]
        if step_id in visiting:
            raise ValueError(f"Dependency cycle detected at step_id {step_id!r}.")
        visiting.add(step_id)
        item = by_step_id[step_id]
        result: set[str] = set()
        for dep_id in item.get("depends_on") or []:
            if dep_id not in by_step_id:
                continue
            result.add(dep_id)
            result.update(collect(dep_id))
        visiting.remove(step_id)
        visited[step_id] = result
        return result

    return sorted(collect(current_step_id), key=lambda step_id: order_index.get(step_id, 0))


def _blocks_to_plain_text(
    blocks: List[Dict[str, Any]],
    citations: Dict[str, Any],
    state: CitationState,
    *,
    remap: bool,
) -> str:
    lines: List[str] = []
    for block in blocks or []:
        text = _parts_to_text(block.get("content_parts") or [], citations, state, remap=remap)
        if not text and block.get("content"):
            text = str(block["content"])
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
    return "\n\n".join(lines)


def _parts_to_text(
    parts: List[Dict[str, Any]],
    citations: Dict[str, Any],
    state: CitationState,
    *,
    remap: bool,
) -> str:
    chunks: List[str] = []
    for part in parts:
        if part.get("type") == "text":
            chunks.append(str(part.get("content") or ""))
        elif part.get("type") == "citation_ref":
            citation_id = str(part.get("citation_id") or "")
            if remap:
                citation_id = _register_dependency_citation(citation_id, citations, state)
            chunks.append(f"[{citation_id}]")
    return "".join(chunks)


def _register_dependency_citation(
    workflow_citation_id: str,
    source_citations: Dict[str, Any],
    state: CitationState,
) -> str:
    if workflow_citation_id in state.workflow_citation_to_local:
        return state.workflow_citation_to_local[workflow_citation_id]

    source_meta = source_citations.get(workflow_citation_id)
    if not isinstance(source_meta, dict):
        return workflow_citation_id

    citation_type = source_meta.get("type")
    segment_id = source_meta.get("segment_id")
    image_id = source_meta.get("image_id")

    if citation_type == "segment" and segment_id in state.segment_to_citation:
        local_id = state.segment_to_citation[segment_id]
    elif citation_type == "image" and image_id in state.image_to_citation:
        local_id = state.image_to_citation[image_id]
    else:
        local_id = f"citation_{state.citation_counter}"
        state.citation_counter += 1
        copied = {k: v for k, v in source_meta.items() if k != "display_num"}
        copied["source_workflow_citation_id"] = workflow_citation_id
        state.citations_map[local_id] = copied
        if citation_type == "segment" and segment_id:
            state.segment_to_citation[segment_id] = local_id
        if citation_type == "image" and image_id:
            state.image_to_citation[image_id] = local_id

    state.workflow_citation_to_local[workflow_citation_id] = local_id
    return local_id
