import re
from typing import List, Dict, Any

from .base import BaseParser, Block, ParseResult


class TxtParser(BaseParser):

    HEADING_PATTERNS = [
        (r'^#{1,6}\s+', 'heading'),
        (r'^第[一二三四五六七八九十百千万零\d]+[章卷部篇]', 'heading'),
        (r'^第[一二三四五六七八九十百千万零\d]+[节]', 'heading'),
        (r'^[一二三四五六七八九十]+[、．.]', 'heading'),
        (r'^[（(][一二三四五六七八九十]+[）)]', 'heading'),
        (r'^\d+[、．.]\s*\S', 'heading'),
        (r'^[（(]\d+[）)]', 'heading'),
    ]

    LIST_PATTERNS = [
        (r'^[\-\*\+]\s', 'list'),
        (r'^\d+[\.\)]\s', 'list'),
    ]

    def get_supported_extensions(self) -> List[str]:
        return [".txt"]

    async def parse(self, file_path: str) -> ParseResult:
        import aiofiles

        async with aiofiles.open(file_path, encoding="utf-8", errors="ignore") as f:
            text = await f.read()

        blocks = self._create_blocks(text)

        return ParseResult(
            text=text,
            blocks=blocks,
            page_count=0,
            images=[]
        )

    def _create_blocks(self, text: str) -> List[Block]:
        if not text:
            return []

        blocks = []
        position_offset = 0

        paragraphs = re.split(r'\n\s*\n', text)

        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                continue

            start_pos = text.find(para_text, position_offset)
            if start_pos == -1:
                start_pos = position_offset
            end_pos = start_pos + len(para_text)
            position_offset = end_pos

            block_type = self._detect_block_type(para_text)

            clean_content = self._clean_content(para_text, block_type)

            extra = {}
            if block_type == "heading":
                level = self._get_heading_level(para_text)
                if level:
                    extra["level"] = level

            blocks.append(Block(
                id=f"b_{len(blocks)}",
                type=block_type,
                content=clean_content,
                position={"start": start_pos, "end": end_pos},
                page=0,
                extra=extra if extra else None
            ))

        return blocks

    def _detect_block_type(self, text: str) -> str:
        text_stripped = text.strip()

        if not text_stripped:
            return "paragraph"

        if (text_stripped.startswith('|') and '|' in text_stripped) or \
           (text_stripped.startswith('<table')):
            return "table"

        if text_stripped.startswith('```') or text_stripped.startswith('>'):
            return "code"

        if text_stripped.startswith('$$'):
            return "equation"

        for pattern, block_type in self.HEADING_PATTERNS:
            if re.match(pattern, text_stripped):
                return block_type

        for pattern, block_type in self.LIST_PATTERNS:
            if re.match(pattern, text_stripped):
                return block_type

        return "paragraph"

    def _clean_content(self, text: str, block_type: str) -> str:
        if block_type == "heading":
            text = re.sub(r'^#+\s*', '', text)

        return text.strip()

    def _get_heading_level(self, text: str) -> int:
        text = text.strip()

        match = re.match(r'^(#{1,6})\s', text)
        if match:
            return len(match.group(1))

        return 1
