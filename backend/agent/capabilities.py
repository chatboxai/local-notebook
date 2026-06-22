"""Section capability registry for report generation.

Capabilities describe what kind of report section the downstream section writer
can produce. Tool names and descriptions are derived from the actual tool classes
so planner context cannot drift from executable tools.
"""

from dataclasses import dataclass, field
from typing import List, Type

from agent.tools.file_tools import AskImageTool, GetFileMetaTool, ListFilesTool
from agent.tools.query_knowledge_base import QueryKnowledgeBaseTool
from agent.tools.read_segments import ReadSegmentsTool
from agent.tools.web_search import WebSearchTool
from kosong.tooling import Tool


SECTION_TOOL_CLASSES: List[Type[Tool]] = [
    QueryKnowledgeBaseTool,
    ReadSegmentsTool,
    ListFilesTool,
    GetFileMetaTool,
    AskImageTool,
    WebSearchTool,
]

TOOL_CLASS_BY_NAME = {tool_cls.name: tool_cls for tool_cls in SECTION_TOOL_CLASSES}

TOOL_QUERY_KB = QueryKnowledgeBaseTool.name
TOOL_READ_SEGMENTS = ReadSegmentsTool.name
TOOL_LIST_FILES = ListFilesTool.name
TOOL_GET_FILE_META = GetFileMetaTool.name
TOOL_ASK_IMAGE = AskImageTool.name
TOOL_WEB_SEARCH = WebSearchTool.name


@dataclass(frozen=True)
class Capability:
    """A report-section capability."""

    type: str
    name: str
    modality: str  # 'text' | 'image' | 'video' (MVP 仅 text)
    tools: List[str] = field(default_factory=list)


CAPABILITIES: List[Capability] = [
    Capability(
        type="text_section",
        name="Text section",
        modality="text",
        tools=[tool_cls.name for tool_cls in SECTION_TOOL_CLASSES],
    ),
]

_CAPABILITY_BY_TYPE = {c.type: c for c in CAPABILITIES}

DEFAULT_FEATURE_TYPE = "text_section"


def get_capability(feature_type: str) -> Capability:
    return _CAPABILITY_BY_TYPE.get(feature_type) or _CAPABILITY_BY_TYPE[DEFAULT_FEATURE_TYPE]


def describe_capabilities_for_planner() -> str:
    """Describe executable section capabilities for the planner."""
    lines = ["Available section capabilities:"]
    for c in CAPABILITIES:
        lines.append(f"- `{c.type}` ({c.name}, output modality: {c.modality})")
        lines.append("  Uses the downstream section generation agent and its tools listed below.")
    return "\n".join(lines)
