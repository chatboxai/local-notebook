"""Workflow citation helpers for concurrent report section generation."""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, Iterable, List, Tuple

from sqlalchemy import select

LOCAL_CITATION_RE = re.compile(r"^citation_(\d+)$")
LOCAL_CITATION_MARKER_RE = re.compile(r"\[citation_(\d+)\]")
WORKFLOW_CITATION_RE = re.compile(r"^citation_([a-z][a-z0-9_]*)_(\d+)$")


def workflow_citation_id(step_id: str, local_citation_id: str) -> str:
    """Return the workflow-level citation id for a feature-local citation id."""
    match = LOCAL_CITATION_RE.match(local_citation_id or "")
    if not match:
        return local_citation_id
    return f"citation_{step_id}_{match.group(1)}"


def convert_local_feature_to_workflow(
    blocks: List[Dict[str, Any]],
    local_citations: Dict[str, Any],
    step_id: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Namespace one feature's local citation ids with its stable workflow step_id."""
    id_map = {
        local_id: workflow_citation_id(step_id, local_id)
        for local_id in local_citations.keys()
    }

    workflow_citations: Dict[str, Any] = {}
    for local_id, meta in local_citations.items():
        workflow_id = id_map.get(local_id, local_id)
        if not isinstance(meta, dict):
            continue
        copied = {k: copy.deepcopy(v) for k, v in meta.items() if k != "display_num"}
        copied["step_id"] = step_id
        copied["local_citation_id"] = local_id
        workflow_citations[workflow_id] = copied

    return [_convert_block(block, id_map) for block in blocks], workflow_citations


def _convert_block(block: Dict[str, Any], id_map: Dict[str, str]) -> Dict[str, Any]:
    converted = copy.deepcopy(block)
    if converted.get("content_parts"):
        converted["content_parts"] = [
            _convert_part(part, id_map)
            for part in converted["content_parts"]
        ]
    if converted.get("content"):
        converted["content"] = _replace_local_markers(str(converted["content"]), id_map)
    return converted


def _convert_part(part: Dict[str, Any], id_map: Dict[str, str]) -> Dict[str, Any]:
    converted = copy.deepcopy(part)
    if converted.get("type") != "citation_ref":
        return converted
    citation_id = converted.get("citation_id")
    if citation_id in id_map:
        converted["citation_id"] = id_map[citation_id]
    converted.pop("display_num", None)
    return converted


def _replace_local_markers(text: str, id_map: Dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        local_id = f"citation_{match.group(1)}"
        return f"[{id_map.get(local_id, local_id)}]"

    return LOCAL_CITATION_MARKER_RE.sub(replace, text)


def iter_block_citation_ids(blocks: Iterable[Dict[str, Any]]) -> Iterable[str]:
    """Yield citation ids in the order they appear in block content."""
    for block in blocks or []:
        for part in block.get("content_parts") or []:
            if part.get("type") == "citation_ref" and part.get("citation_id"):
                yield str(part["citation_id"])

        content = block.get("content")
        if isinstance(content, str):
            for match in re.finditer(r"\[([a-zA-Z0-9_]+)\]", content):
                citation_id = match.group(1)
                if citation_id.startswith("citation_"):
                    yield citation_id


def apply_display_nums_to_blocks(
    blocks: List[Dict[str, Any]],
    citations: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Copy blocks and refresh citation_ref display_num values from citations."""
    converted = copy.deepcopy(blocks or [])
    for block in converted:
        for part in block.get("content_parts") or []:
            if part.get("type") != "citation_ref":
                continue
            citation_id = part.get("citation_id")
            meta = citations.get(citation_id) if citation_id else None
            if isinstance(meta, dict):
                part["display_num"] = meta.get("display_num")
    return converted


async def finalize_workflow_citations(db, workflow_id: str) -> Dict[str, Any]:
    """Rebuild workflow citations and display numbers in final report order."""
    from models.feature import Feature
    from models.workflow import Workflow

    result = await db.execute(
        select(Feature)
        .where(Feature.workflow_id == workflow_id, Feature.status == "completed")
        .order_by(Feature.step_index.asc())
    )
    features = list(result.scalars().all())

    workflow_citations: Dict[str, Any] = {}
    for feature in features:
        workflow_citations.update(feature.get_citations())

    ordered_ids: List[str] = []
    seen: set[str] = set()
    for feature in features:
        for citation_id in iter_block_citation_ids(feature.get_blocks()):
            if citation_id in seen or citation_id not in workflow_citations:
                continue
            seen.add(citation_id)
            ordered_ids.append(citation_id)

    for meta in workflow_citations.values():
        if isinstance(meta, dict):
            meta.pop("display_num", None)
    for display_num, citation_id in enumerate(ordered_ids, start=1):
        meta = workflow_citations.get(citation_id)
        if isinstance(meta, dict):
            meta["display_num"] = display_num

    for feature in features:
        feature_citations = feature.get_citations()
        refreshed = {
            cid: workflow_citations[cid]
            for cid in feature_citations.keys()
            if cid in workflow_citations
        }
        feature.set_citations(refreshed)
        feature.set_blocks(apply_display_nums_to_blocks(feature.get_blocks(), workflow_citations))

    wf = await db.get(Workflow, workflow_id)
    if wf:
        wf.set_citations(workflow_citations)
        wf.next_citation_display_num = len(ordered_ids) + 1

    return workflow_citations
