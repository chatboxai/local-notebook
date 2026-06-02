import asyncio
import re
from typing import List

from .base import BaseParser, Block, ParseResult


class DocxParser(BaseParser):

    def get_supported_extensions(self) -> List[str]:
        return [".docx", ".doc"]

    async def parse(self, file_path: str) -> ParseResult:
        result = await asyncio.to_thread(self._parse_sync, file_path)
        return result

    def _parse_sync(self, file_path: str) -> ParseResult:
        import docx

        doc = docx.Document(file_path)

        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)

        text = "\n\n".join(paragraphs)

        blocks = self._create_blocks(text, paragraphs)

        return ParseResult(
            text=text,
            blocks=blocks,
            page_count=0,
            images=[]
        )

    def _create_blocks(self, full_text: str, paragraphs: List[str]) -> List[Block]:
        if not paragraphs:
            return []

        blocks = []
        position_offset = 0

        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                continue

            start_pos = full_text.find(para_text, position_offset)
            if start_pos == -1:
                start_pos = position_offset
            end_pos = start_pos + len(para_text)
            position_offset = end_pos

            block_type = self._detect_block_type(para_text)

            blocks.append(Block(
                id=f"b_{len(blocks)}",
                type=block_type,
                content=para_text,
                position={"start": start_pos, "end": end_pos},
                page=0,
                extra=None
            ))

        return blocks

    def _detect_block_type(self, text: str) -> str:
        text_stripped = text.strip()

        if not text_stripped:
            return "paragraph"

        if len(text_stripped) < 100:
            if re.match(r'^第[一二三四五六七八九十百千万零\d]+[章卷部篇节]', text_stripped):
                return "heading"
            if re.match(r'^[一二三四五六七八九十]+[、．.]', text_stripped):
                return "heading"
            if re.match(r'^[（(][一二三四五六七八九十]+[）)]', text_stripped):
                return "heading"
            if re.match(r'^\d+[、．.]\s*\S', text_stripped):
                return "heading"

        if re.match(r'^[\-\*\+]\s', text_stripped):
            return "list"
        if re.match(r'^\d+[\.\)]\s', text_stripped):
            return "list"

        return "paragraph"
