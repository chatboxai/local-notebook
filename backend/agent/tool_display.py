from __future__ import annotations

from typing import Any, TypedDict


class ToolDisplayInfo(TypedDict):
    display: str
    display_key: str
    display_params: dict[str, Any]


_TOOL_DISPLAY_BY_NAME: dict[str, tuple[str, str]] = {
    "query_knowledge_base": ("ui.searchingKnowledgeBase", "Searching knowledge base..."),
    "read_segments": ("ui.readingSourceText", "Reading source text..."),
    "list_files": ("ui.listingFiles", "Listing files..."),
    "get_file_meta": ("ui.gettingFileDetails", "Getting file details..."),
    "ask_image": ("ui.analyzingImages", "Analyzing images..."),
    "web_search": ("ui.searchingWeb", "Searching web..."),
}


def get_tool_display_info(name: str) -> ToolDisplayInfo:
    known = _TOOL_DISPLAY_BY_NAME.get(name)
    if known:
        display_key, display = known
        return {
            "display": display,
            "display_key": display_key,
            "display_params": {},
        }

    return {
        "display": f"Running {name}...",
        "display_key": "ui.runningTool",
        "display_params": {"name": name},
    }
