import asyncio
import base64
import os
import re
from typing import List, Dict, Optional, Tuple

from .base import BaseParser, Block, ParseResult


class PDFParser(BaseParser):

    HEADING_PATTERNS = [
        (r'^#{1}\s+', 1),
        (r'^#{2}\s+', 2),
        (r'^#{3}\s+', 3),
        (r'^#{4}\s+', 4),
        (r'^#{5}\s+', 5),
        (r'^#{6}\s+', 6),
        (r'^第[一二三四五六七八九十百千万零\d]+[章]', 1),
        (r'^第[一二三四五六七八九十百千万零\d]+[卷部篇]', 1),
        (r'^第[一二三四五六七八九十百千万零\d]+[节]', 2),
        (r'^[一二三四五六七八九十]+[、.．]', 2),
        (r'^[（\(][一二三四五六七八九十]+[）\)]', 3),
        (r'^\d+[、.．]\s*\S', 2),
        (r'^[（\(]\d+[）\)]', 3),
    ]

    def get_supported_extensions(self) -> List[str]:
        return [".pdf"]

    async def parse(self, file_path: str, file_id: str | None = None, db=None) -> ParseResult:
        import config
        from services.mineru_client import MinerUClient, MinerUCloudClient

        enabled, source, base_url, api_key = await config.resolve_mineru_config()
        if not enabled:
            raise RuntimeError(
                "PDF 解析需要 MinerU 服务。请在「设置 → MinerU」配置服务地址或 API Key 后重试。"
            )

        if source == "api":
            existing_batch_id = None
            batch_created_at = None

            if file_id and db:
                from models.file import File
                db_file = await db.get(File, file_id)
                if db_file and db_file.mineru_batch_id:
                    existing_batch_id = db_file.mineru_batch_id
                    batch_created_at = db_file.mineru_batch_created

            client = MinerUCloudClient(api_key)
            result, batch_id = await client.parse_pdf(
                file_path,
                existing_batch_id=existing_batch_id,
                batch_created_at=batch_created_at,
            )

            if batch_id and file_id:
                from datetime import datetime, timezone
                from database import AsyncSessionLocal
                from models.file import File
                async with AsyncSessionLocal() as short_db:
                    db_file = await short_db.get(File, file_id)
                    if db_file:
                        db_file.mineru_batch_id = batch_id
                        if not existing_batch_id or existing_batch_id != batch_id:
                            db_file.mineru_batch_created = datetime.now(timezone.utc)
                        await short_db.commit()

            img_path_mapping = result.images or {}
        else:
            client = MinerUClient(base_url)
            result = await client.parse_pdf(file_path)

            img_dir = os.path.join(os.path.dirname(file_path), "images")
            img_path_mapping = {}
            if result.images:
                img_path_mapping = await asyncio.to_thread(
                    self._save_images_from_base64, result.images, img_dir
                )

        if not result.success:
            raise RuntimeError(f"PDF 解析失败: {result.error_message}")

        blocks = []
        extracted_images = []
        parsed_text = result.markdown
        if result.content_list:
            blocks, extracted_images = self._parse_content_list_to_blocks(
                result.content_list, img_path_mapping
            )
            if blocks:
                parsed_text = "\n".join(block.content for block in blocks)

        if not blocks:
            markdown = self._simplify_markdown(result.markdown)
            blocks = self._parse_markdown_to_blocks(markdown)
            parsed_text = markdown

        for i, block in enumerate(blocks):
            block.id = f"b_{i}"

        page_count = result.page_count or await self._get_pdf_page_count(file_path)

        return ParseResult(
            text=parsed_text,
            blocks=blocks,
            page_count=page_count,
            images=extracted_images,
        )

    @staticmethod
    def _save_images_from_base64(images_dict: dict, img_dir: str) -> dict:
        if not images_dict:
            return {}

        os.makedirs(img_dir, exist_ok=True)
        mapping = {}
        written_paths = set()

        for img_name, img_data in images_dict.items():
            try:
                if isinstance(img_data, str) and img_data.startswith("data:"):
                    header, b64 = img_data.split(",", 1)
                    ext = header.split("/")[1].split(";")[0]
                else:
                    b64 = img_data
                    ext = os.path.splitext(img_name)[1].lstrip(".") or "jpg"

                raw = base64.b64decode(b64)
                safe_name = os.path.basename(img_name)
                if not safe_name.lower().endswith(("." + ext)):
                    safe_name = safe_name + "." + ext
                local_path = os.path.join(img_dir, safe_name)
                if local_path not in written_paths:
                    with open(local_path, "wb") as f:
                        f.write(raw)
                    written_paths.add(local_path)
                mapping[img_name] = local_path
                mapping[f"images/{img_name}"] = local_path
                mapping[os.path.basename(img_name)] = local_path
            except Exception:
                pass

        return mapping

    def _parse_content_list_to_blocks(
        self, content_list: List[Dict], img_path_mapping: Optional[dict] = None
    ) -> Tuple[List[Block], List[Dict]]:
        if not content_list:
            return [], []

        img_path_mapping = img_path_mapping or {}
        blocks = []
        extracted_images: List[Dict] = []
        image_index = 0
        position_offset = 0

        for item in content_list:
            if not isinstance(item, dict):
                continue

            item_type = item.get("type", "")

            if item_type == "discarded":
                continue

            if item_type == "table":
                text = item.get("table_body", "")
                text = self._html_table_to_markdown(text)
            elif item_type == "image":
                img_path_key = item.get("img_path", "")
                local_path = img_path_mapping.get(img_path_key, "")
                page_idx = item.get("page_idx", 0)
                page = page_idx + 1 if isinstance(page_idx, int) else 1
                if local_path:
                    extracted_images.append({
                        "image_index": image_index,
                        "file_path": local_path,
                        "page": page,
                        "img_name": os.path.basename(local_path),
                    })
                    image_index += 1
                text = "[Image]"
            elif item_type == "list":
                list_items = item.get("list_items", [])
                if isinstance(list_items, list) and list_items:
                    text = "\n".join(list_items)
                else:
                    text = item.get("text", "")
            elif item_type == "code":
                text = item.get("code_body", "")
                if not text:
                    text = item.get("text", "")
            elif item_type == "page_number":
                continue
            else:
                text = item.get("text", "")

            if not text or not text.strip():
                continue

            page_idx = item.get("page_idx", 0)
            page = page_idx + 1 if isinstance(page_idx, int) else 1

            block_type = "paragraph"
            extra = {}

            bbox = item.get("bbox")
            if bbox and len(bbox) >= 4:
                extra["bbox"] = bbox

            if item_type == "table":
                block_type = "paragraph"
                extra["is_table"] = True
                extra["table_html"] = item.get("table_body", "")

                table_caption = item.get("table_caption", [])
                if table_caption and isinstance(table_caption, list) and len(table_caption) > 0:
                    extra["table_caption"] = table_caption[0]

                table_footnote = item.get("table_footnote", [])
                if table_footnote and isinstance(table_footnote, list) and len(table_footnote) > 0:
                    extra["table_footnote"] = table_footnote[0]

            elif item_type == "image":
                block_type = "paragraph"
                extra["is_image"] = True

            elif item_type == "equation":
                block_type = "paragraph"
                extra["is_formula"] = True

            elif item_type == "header":
                block_type = "heading"
                text_level = item.get("text_level")
                if text_level and isinstance(text_level, int) and text_level <= 6:
                    extra["level"] = text_level
                else:
                    extra["level"] = 1

            elif item_type == "list":
                block_type = "list"
                list_items = item.get("list_items", [])
                if list_items:
                    extra["list_items"] = list_items

            elif item_type == "code":
                block_type = "paragraph"
                extra["is_code"] = True
                guess_lang = item.get("guess_lang", "")
                if guess_lang:
                    extra["guess_lang"] = guess_lang

            elif item_type == "text":
                text_level = item.get("text_level")
                if text_level and isinstance(text_level, int) and text_level <= 6:
                    block_type = "heading"
                    extra["level"] = text_level
                else:
                    text_stripped = text.strip()
                    if text_stripped.startswith(("-", "*", "+")) or \
                       re.match(r'^\d+\.\s', text_stripped):
                        block_type = "list"

            clean_text = text.strip()
            start_pos = position_offset
            end_pos = start_pos + len(clean_text)
            position_offset = end_pos + 1

            blocks.append(Block(
                id="",
                type=block_type,
                content=clean_text,
                position={"start": start_pos, "end": end_pos},
                page=page,
                extra=extra if extra else None
            ))

        return blocks, extracted_images

    def _parse_markdown_to_blocks(self, markdown: str) -> List[Block]:
        blocks = []
        current_pos = 0

        paragraphs = re.split(r'\n\s*\n', markdown)

        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                continue

            start_pos = markdown.find(para_text, current_pos)
            if start_pos == -1:
                start_pos = current_pos
            end_pos = start_pos + len(para_text)
            current_pos = end_pos

            block_type, extra = self._detect_block_type(para_text)

            blocks.append(Block(
                id="",
                type=block_type,
                content=self._clean_markdown_syntax(para_text, block_type),
                position={"start": start_pos, "end": end_pos},
                page=0,
                extra=extra
            ))

        return blocks

    def _detect_block_type(self, text: str) -> Tuple[str, Optional[Dict]]:
        text_stripped = text.strip()

        if text_stripped.startswith("|") and "|" in text_stripped:
            lines = text_stripped.split("\n")
            if len(lines) >= 2 and all("|" in line for line in lines):
                return "paragraph", {"is_table": True}

        if text_stripped.startswith("$$") and text_stripped.endswith("$$"):
            return "paragraph", {"is_formula": True}

        heading_level = self._detect_heading(text_stripped)
        if heading_level:
            return "heading", {"level": heading_level}

        if re.match(r'^[\-\*\+]\s', text_stripped) or re.match(r'^\d+\.\s', text_stripped):
            return "list", None

        return "paragraph", None

    def _detect_heading(self, text: str) -> Optional[int]:
        text = text.strip()
        if not text or "\n" in text or len(text) > 100:
            return None

        for pattern, level in self.HEADING_PATTERNS:
            if re.match(pattern, text):
                return level

        return None

    def _clean_markdown_syntax(self, text: str, block_type: str) -> str:
        if block_type == "heading":
            text = re.sub(r'^#+\s*', '', text)
        return text.strip()

    def _simplify_markdown(self, markdown: str) -> str:
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'[Image]', markdown)
        text = re.sub(r'(\[Image\]\s*){2,}', '[Image]\n\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _html_table_to_markdown(self, html_table: str) -> str:
        from html import unescape

        if not html_table:
            return ""

        text = unescape(html_table)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', text, re.DOTALL | re.IGNORECASE)

        if not rows:
            return ""

        md_rows = []
        for i, row in enumerate(rows):
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
            clean_cells = []
            for cell in cells:
                cell_text = re.sub(r'<[^>]+>', '', cell)
                cell_text = cell_text.replace("\n", " ").strip()
                clean_cells.append(cell_text)

            md_rows.append("| " + " | ".join(clean_cells) + " |")

            if i == 0:
                separator = "| " + " | ".join(["---"] * len(clean_cells)) + " |"
                md_rows.append(separator)

        return "\n".join(md_rows)

    async def _get_pdf_page_count(self, file_path: str) -> int:
        def _count_pages() -> int:
            try:
                from pypdf import PdfReader

                reader = PdfReader(file_path)
                return len(reader.pages)
            except Exception:
                return 0

        return await asyncio.to_thread(_count_pages)
