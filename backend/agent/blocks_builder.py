"""把 while-loop agent 产出的 markdown 转成前端 FeatureBlock 列表。

引用拆分复用 CitationParser，使整份 workflow 的引用编号全局连续：
调用方传入共享的 citation_map 与 start_display_num，本函数返回更新后的
next_display_num，并把分配到的 display_num 回写进 citation_map（与 chat_agent
的 _sync_display_nums 行为一致）。
"""

import re
from typing import Any, Dict, List, Tuple

from agent.citation_parser import CitationParser

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
_QUOTE_RE = re.compile(r"^\s*>\s?(.*)$")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}.*$")


def _text_to_parts(parser: CitationParser, text: str) -> List[Dict[str, Any]]:
    """把一段文本经引用解析拆成 content_parts。"""
    parts: List[Dict[str, Any]] = []
    events = list(parser.feed(text)) + list(parser.flush())
    for ev in events:
        if ev["type"] == "text":
            content = ev.get("content", "")
            if content:
                parts.append({"type": "text", "content": content})
        elif ev["type"] == "citation_ref":
            part = {k: v for k, v in ev.items()}
            parts.append(part)
    if not parts:
        parts.append({"type": "text", "content": text})
    return parts


def markdown_to_blocks(
    markdown: str,
    citation_map: Dict[str, Any],
    start_display_num: int = 1,
) -> Tuple[List[Dict[str, Any]], int]:
    """markdown -> (blocks, next_display_num)。"""
    parser = CitationParser(citation_map=citation_map, start_display_num=start_display_num)
    blocks: List[Dict[str, Any]] = []

    lines = (markdown or "").replace("\r\n", "\n").split("\n")
    i = 0
    n = len(lines)
    para_buf: List[str] = []

    def flush_para() -> None:
        if not para_buf:
            return
        text = " ".join(s.strip() for s in para_buf).strip()
        para_buf.clear()
        if text:
            blocks.append({
                "block_type": "paragraph",
                "content_parts": _text_to_parts(parser, text),
            })

    in_code = False
    code_buf: List[str] = []

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 代码块：原样收集为一个段落
        if stripped.startswith("```"):
            if in_code:
                in_code = False
                code_text = "\n".join(code_buf)
                code_buf.clear()
                if code_text.strip():
                    blocks.append({
                        "block_type": "paragraph",
                        "content_parts": [{"type": "text", "content": code_text}],
                    })
            else:
                flush_para()
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # 空行：段落分隔
        if not stripped:
            flush_para()
            i += 1
            continue

        # 标题
        m = _HEADING_RE.match(line)
        if m:
            flush_para()
            level = len(m.group(1))
            text = m.group(2).strip()
            blocks.append({
                "block_type": "heading",
                "level": level,
                "content_parts": _text_to_parts(parser, text),
            })
            i += 1
            continue

        # 表格：连续的 | … | 行（含分隔行），存原始 markdown 到 content
        if _TABLE_ROW_RE.match(line) and i + 1 < n and _TABLE_SEP_RE.match(lines[i + 1]):
            flush_para()
            table_lines = [line]
            i += 1
            while i < n and _TABLE_ROW_RE.match(lines[i]):
                table_lines.append(lines[i])
                i += 1
            raw_table = "\n".join(table_lines)
            blocks.append({
                "block_type": "paragraph",
                "content": raw_table,
                "content_parts": [{"type": "text", "content": raw_table}],
                "extra": {"is_table": True},
            })
            continue

        # 引用
        m = _QUOTE_RE.match(line)
        if m:
            flush_para()
            text = m.group(1).strip()
            blocks.append({
                "block_type": "quote",
                "content_parts": _text_to_parts(parser, text),
            })
            i += 1
            continue

        # 列表项：每项一个 list block（前端 processFeatureBlocks 会归组）
        m = _LIST_RE.match(line)
        if m:
            flush_para()
            text = m.group(1).strip()
            blocks.append({
                "block_type": "list",
                "content_parts": _text_to_parts(parser, text),
            })
            i += 1
            continue

        # 普通段落行
        para_buf.append(line)
        i += 1

    flush_para()
    if in_code and code_buf:
        code_text = "\n".join(code_buf)
        if code_text.strip():
            blocks.append({
                "block_type": "paragraph",
                "content_parts": [{"type": "text", "content": code_text}],
            })

    # 把分配到的 display_num 回写进 citation_map，供后续栏目复用同一编号
    for citation_id, display_num in parser.id_to_display.items():
        entry = citation_map.get(citation_id)
        if entry is not None and entry.get("display_num") is None:
            entry["display_num"] = display_num

    return blocks, parser.display_num
