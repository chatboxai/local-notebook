import logging
from typing import List, Dict, Any

from workers.parsers.base import BaseParser, Block, ParseResult
from services.vlm_client import describe_image

logger = logging.getLogger(__name__)


class ImageParser(BaseParser):

    async def parse(self, file_path: str) -> ParseResult:
        logger.info(f"Parsing image: {file_path}")

        try:
            description, vlm_model = await describe_image(file_path)
            logger.info(f"Image description generated, length={len(description)}, model={vlm_model}")
        except Exception as e:
            logger.error(f"Failed to describe image: {e}")
            error_msg = f"[图片描述生成失败: {str(e)}]"
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
                "image_path": file_path,
            },
        )

        image_meta = {
            "image_index": 1,
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
