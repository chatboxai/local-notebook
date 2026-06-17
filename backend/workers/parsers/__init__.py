from .pdf_parser import PDFParser
from .txt_parser import TxtParser
from .docx_parser import DocxParser
from .epub_parser import EpubParser
from .image_parser import ImageParser


PARSERS = {
    ".pdf": PDFParser,
    ".txt": TxtParser,
    ".docx": DocxParser,
    ".doc": DocxParser,
    ".epub": EpubParser,
    ".jpg": ImageParser,
    ".jpeg": ImageParser,
    ".png": ImageParser,
}


def get_parser_for_file(file_path: str) -> "BaseParser":
    from pathlib import Path

    ext = Path(file_path).suffix.lower()
    parser_class = PARSERS.get(ext)

    if not parser_class:
        raise ValueError(f"不支持的文件类型: {ext}")

    return parser_class()


__all__ = [
    "PDFParser",
    "TxtParser",
    "DocxParser",
    "EpubParser",
    "get_parser_for_file",
    "PARSERS",
]
