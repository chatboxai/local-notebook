import asyncio
import json
import logging
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnValue

from agent.tools.query_knowledge_base import CitationState

logger = logging.getLogger("tool.read_segments")


class ReadSegmentsParams(BaseModel):
    citation_ids: list[str] = Field(
        default_factory=list,
        description=(
            "List of citation_ids to read. Supports the [citation_X] format. "
            "Use this to retrieve the complete original text of cited segments."
        ),
    )
    offsets: Optional[list[int]] = Field(
        default=None,
        description=(
            "Relative segment offsets. Only applies when citation_ids contains one item. "
            "0=current segment, -1=previous segment, 1=next segment, range -7 to 7. "
            "Example: [-1, 0, 1] reads the previous, current, and next segments."
        ),
    )

    @field_validator("offsets", mode="before")
    @classmethod
    def _parse_offsets(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class ReadSegmentsTool(CallableTool2[ReadSegmentsParams]):
    name: str = "read_segments"
    description: str = (
        "Read the complete original text of text segments. Pass citation_ids such "
        "as [citation_X]. Use offsets to include adjacent context when reading a single citation."
    )
    params: type[ReadSegmentsParams] = ReadSegmentsParams

    def __init__(self, citation_state: Optional[CitationState] = None):
        super().__init__()
        self.state = citation_state or CitationState()

    async def __call__(self, params: ReadSegmentsParams) -> ToolReturnValue:
        state = self.state
        citation_ids = params.citation_ids
        offsets = params.offsets

        if not citation_ids:
            return ToolError(message="citation_ids must not be empty")

        normalized_ids = [cid.strip("[] ") for cid in citation_ids]

        segment_ids: list[str] = []
        errors: list[dict] = []

        for cid in normalized_ids:
            meta = state.citations_map.get(cid)
            if not meta:
                errors.append({"error": f"Citation not found: [{cid}]", "citation_id": f"[{cid}]"})
                continue
            if meta.get("type") != "segment":
                errors.append({"error": f"[{cid}] is not a text citation, so original text cannot be read.", "citation_id": f"[{cid}]"})
                continue
            seg_id = meta.get("segment_id")
            if not seg_id:
                errors.append({"error": f"[{cid}] is missing segment_id.", "citation_id": f"[{cid}]"})
                continue
            segment_ids.append(seg_id)

        if not segment_ids:
            return ToolOk(output=json.dumps(errors or [{"error": "No valid text citations"}], ensure_ascii=False))

        if offsets:
            if len(segment_ids) > 1:
                return ToolOk(output=json.dumps([{
                    "error": "The offsets parameter only applies when citation_ids contains exactly one item.",
                    "hint": "Pass only one citation_id, or omit offsets.",
                }], ensure_ascii=False))
            segment_ids = self._expand_offsets(segment_ids[0], offsets)

        from services.vector_service import get_by_ids
        hits = await asyncio.to_thread(get_by_ids, state.project_id, segment_ids)

        if not hits:
            return ToolOk(output=json.dumps([{"error": "Segment content was not found. It may have been deleted."}], ensure_ascii=False))

        hits_map = {h["id"]: h for h in hits}
        results: list[dict] = []

        for seg_id in segment_ids:
            hit = hits_map.get(seg_id)
            if not hit:
                continue
            item: dict = {
                "file_name": hit["file_name"],
                "content": hit["content"],
            }
            existing_cid = state.segment_to_citation.get(seg_id)
            if existing_cid:
                item["citation_id"] = f"[{existing_cid}]"
            results.append(item)

        if errors:
            results.extend(errors)

        logger.info(f"[read_segments] fetched {len(results)} segments, project={state.project_id}")
        return ToolOk(output=json.dumps(results, ensure_ascii=False))

    @staticmethod
    def _expand_offsets(segment_id: str, offsets: list[int]) -> list[str]:
        last_sep = segment_id.rfind("_s_")
        if last_sep == -1:
            return [segment_id]
        file_id = segment_id[:last_sep]
        try:
            base_index = int(segment_id[last_sep + 3:])
        except ValueError:
            return [segment_id]

        result = []
        for offset in sorted(set(offsets)):
            idx = base_index + offset
            if idx >= 0:
                result.append(f"{file_id}_s_{idx}")
        return result or [segment_id]
