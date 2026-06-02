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
            "要读取的 citation_id 列表，支持 [citation_X] 格式。"
            "用于获取已引用段落的完整原文内容。"
        ),
    )
    offsets: Optional[list[int]] = Field(
        default=None,
        description=(
            "相对位置列表（仅当 citation_ids 只有一个时生效）。"
            "0=当前片段，-1=前一个，1=后一个，范围 -7 到 7。"
            "示例：[-1, 0, 1] 读取前一个、当前、后一个共 3 个片段。"
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
        "读取文本块的完整原文内容。支持传 citation_ids（如 [citation_X]），"
        "可配合 offsets 获取上下文相邻段落（仅单 citation 时生效）。"
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
            return ToolError(message="citation_ids 不能为空")

        normalized_ids = [cid.strip("[] ") for cid in citation_ids]

        segment_ids: list[str] = []
        errors: list[dict] = []

        for cid in normalized_ids:
            meta = state.citations_map.get(cid)
            if not meta:
                errors.append({"error": f"未找到 citation: [{cid}]", "citation_id": f"[{cid}]"})
                continue
            if meta.get("type") != "segment":
                errors.append({"error": f"[{cid}] 不是文本引用，无法读取原文", "citation_id": f"[{cid}]"})
                continue
            seg_id = meta.get("segment_id")
            if not seg_id:
                errors.append({"error": f"[{cid}] 缺少 segment_id", "citation_id": f"[{cid}]"})
                continue
            segment_ids.append(seg_id)

        if not segment_ids:
            return ToolOk(output=json.dumps(errors or [{"error": "无有效的文本引用"}], ensure_ascii=False))

        if offsets:
            if len(segment_ids) > 1:
                return ToolOk(output=json.dumps([{
                    "error": "offsets 参数仅在 citation_ids 只有一个时生效",
                    "hint": "请只传一个 citation_id，或不使用 offsets 参数",
                }], ensure_ascii=False))
            segment_ids = self._expand_offsets(segment_ids[0], offsets)

        from services.vector_service import get_by_ids
        hits = await asyncio.to_thread(get_by_ids, state.project_id, segment_ids)

        if not hits:
            return ToolOk(output=json.dumps([{"error": "未找到段落内容，可能已被删除"}], ensure_ascii=False))

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