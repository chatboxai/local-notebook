import logging
from typing import List, Dict, Any

from workers.parsers.base import BaseParser, Block, ParseResult
from services.vlm_client import describe_image

logger = logging.getLogger(__name__)


class ImageParser(BaseParser):

    async def parse(self, file_path: str, output_language: str | None = None) -> ParseResult:
        logger.info(f"Parsing image: {file_path}")

        try:
            from services.summary_service import normalize_output_language

            summary_language = normalize_output_language(output_language)
            prompt = (
                "Describe this image. Include:\n"
                "1. The main subject and overall content.\n"
                "2. Key visual elements such as objects, people, scenes, text, or charts.\n"
                "3. The overall style and atmosphere.\n"
                "Be detailed but concise.\n\n"
                f"Output language: {summary_language}"
            )
            description, vlm_model = await describe_image(file_path, prompt=prompt)
            logger.info(f"Image description generated, length={len(description)}, model={vlm_model}")
        except Exception as e:
            logger.error(f"Failed to describe image: {e}")
            error_msg = f"[Image description generation failed: {str(e)}]"
            block = Block(
                id="b_0",
                type="paragraph",
                content=error_msg,
                position={"start": 0, "end": len(error_msg)},
                page=1,
                extra={"is_image": True, "error": str(e)},
            )
            return ParseResult(
                text=error_msg,
                blocks=[block],
                page_count=1,
                images=[],
            )

        block = Block(
            id="b_0",
            type="paragraph",
            content=description,
            position={"start": 0, "end": len(description)},
            page=1,
            extra={
                "is_image": True,
                "vlm_model": vlm_model,
                "image_index": 1,
                "image_path": file_path,
            },
        )

        image_meta = {
            "image_index": 1,
            "file_path": file_path,
            "description": description,
            "vlm_model": vlm_model,
        }

        return ParseResult(
            text=description,
            blocks=[block],
            page_count=1,
            images=[image_meta],
        )

    def get_supported_extensions(self) -> List[str]:
        return [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]
