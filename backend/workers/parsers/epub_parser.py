import asyncio
import re
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseParser, Block, ParseResult


# 章节正文里按文档顺序提取的块级标签;table 单独处理为 markdown
_BLOCK_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre", "table")
# 用于「最外层块」判定:若某元素的祖先里出现这些标签,说明它是嵌套内容,跳过避免重复
_CONTAINER_TAGS = {"p", "li", "blockquote", "pre", "table"}
# 不进入正文索引的标签
_DROP_TAGS = ("script", "style", "nav", "header", "footer")


class EpubParser(BaseParser):
    """EPUB 解析器:按 OPF spine 的阅读顺序抽取结构化文本。

    第一版只做「结构化文本抽取」,不做原始版式还原:
    - 阅读顺序由 spine 决定,不依赖 zip 内文件名排序。
    - page 统一为 0,章节信息(spine_index / href / chapter_title 等)放在 extra,
      避免误用 PDF 的页码逻辑。
    - 不抽取图片(images 返回空)。
    """

    def get_supported_extensions(self) -> List[str]:
        return [".epub"]

    async def parse(self, file_path: str) -> ParseResult:
        return await asyncio.to_thread(self._parse_sync, file_path)

    def _parse_sync(self, file_path: str) -> ParseResult:
        import ebooklib
        from ebooklib import epub

        try:
            book = epub.read_epub(file_path)
        except Exception as exc:  # 坏文件 / 非法 zip / 缺 OPF
            raise RuntimeError(
                f"EPUB 解析失败,文件可能损坏或格式不规范: {exc}"
            ) from exc

        href_to_title = self._build_toc_title_map(book)

        # (content, block_type, extra) 三元组,保持全书阅读顺序
        collected: List[Tuple[str, str, Dict[str, Any]]] = []
        chapter_index = 0

        for spine_index, idref, linear in self._iter_spine(book):
            item = book.get_item_with_id(idref)
            if item is None or item.get_type() != ebooklib.ITEM_DOCUMENT:
                continue
            if self._is_nav_document(item):
                continue

            href = item.get_name() or ""
            try:
                raw = item.get_content()
            except Exception:
                continue

            chapter_blocks = self._extract_chapter_blocks(raw)
            if not chapter_blocks:
                continue

            chapter_title = self._chapter_title(href, chapter_blocks, href_to_title)

            for content, block_type, extra in chapter_blocks:
                extra = dict(extra)
                extra.update(
                    {
                        "chapter_index": chapter_index,
                        "spine_index": spine_index,
                        "href": href,
                    }
                )
                if chapter_title:
                    extra["chapter_title"] = chapter_title
                if not linear:
                    extra["linear"] = False
                collected.append((content, block_type, extra))

            chapter_index += 1

        if not collected:
            raise RuntimeError(
                "未能从 EPUB 中提取到正文文本。该文件可能是加密(DRM)、"
                "固定版式或图片型 EPUB,暂不支持。"
            )

        blocks, text = self._build_blocks(collected)

        return ParseResult(text=text, blocks=blocks, page_count=0, images=[])

    # ── spine ────────────────────────────────────────────────────────────────

    @staticmethod
    def _iter_spine(book) -> List[Tuple[int, str, bool]]:
        """返回 (spine_index, idref, linear) 列表,顺序即阅读顺序。

        ebooklib 的 book.spine 元素可能是 (idref, 'yes'/'no') 元组,也可能是裸 idref。
        """
        result: List[Tuple[int, str, bool]] = []
        for index, entry in enumerate(book.spine or []):
            if isinstance(entry, (tuple, list)):
                idref = entry[0]
                linear_flag = entry[1] if len(entry) > 1 else "yes"
                linear = str(linear_flag).lower() != "no"
            else:
                idref = entry
                linear = True
            if idref:
                result.append((index, idref, linear))
        return result

    @staticmethod
    def _is_nav_document(item) -> bool:
        # EPUB3 的导航文档是带 nav 属性的 XHTML,不应作为正文索引
        props = getattr(item, "properties", None) or []
        return "nav" in props

    # ── 目录标题映射 ──────────────────────────────────────────────────────────

    def _build_toc_title_map(self, book) -> Dict[str, str]:
        """从 toc(NCX / EPUB3 nav)构建 href(去锚点) -> 标题 的扁平映射。"""
        mapping: Dict[str, str] = {}

        def walk(nodes):
            for node in nodes:
                # 可能是 Link,也可能是 (Section, [children]) 元组
                if isinstance(node, (tuple, list)):
                    for sub in node:
                        if isinstance(sub, (tuple, list)):
                            walk(sub)
                        else:
                            add(sub)
                else:
                    add(node)

        def add(link):
            href = getattr(link, "href", None)
            title = getattr(link, "title", None)
            if href and title:
                key = href.split("#", 1)[0]
                mapping.setdefault(key, title.strip())

        try:
            walk(book.toc or [])
        except Exception:
            pass
        return mapping

    def _chapter_title(
        self,
        href: str,
        chapter_blocks: List[Tuple[str, str, Dict[str, Any]]],
        href_to_title: Dict[str, str],
    ) -> Optional[str]:
        key = href.split("#", 1)[0]
        # basename 也试一下,toc 的 href 可能带相对路径前缀
        title = href_to_title.get(key) or href_to_title.get(key.split("/")[-1])
        if title:
            return title
        # 退而求其次:用章节第一个标题块
        for content, block_type, _ in chapter_blocks:
            if block_type == "heading" and content:
                return content
        return None

    # ── HTML -> 块 ────────────────────────────────────────────────────────────

    def _extract_chapter_blocks(
        self, raw: bytes
    ) -> List[Tuple[str, str, Dict[str, Any]]]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(raw, "html.parser")

        for tag in soup(list(_DROP_TAGS)):
            tag.decompose()

        body = soup.body or soup
        blocks: List[Tuple[str, str, Dict[str, Any]]] = []

        for el in body.find_all(_BLOCK_TAGS):
            # 只取最外层块,跳过嵌套在其它块里的元素,避免重复抽取
            if any(p.name in _CONTAINER_TAGS for p in el.parents):
                continue

            name = el.name.lower()

            if name == "table":
                md = self._table_to_markdown(el)
                if md:
                    blocks.append((md, "paragraph", {"is_table": True}))
                continue

            text = self._normalize_text(el.get_text(separator=" "))
            if not text:
                continue

            if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                blocks.append((text, "heading", {"level": int(name[1])}))
            elif name == "li":
                blocks.append((text, "list", {}))
            elif name == "pre":
                blocks.append((text, "paragraph", {"is_code": True}))
            else:  # p / blockquote
                blocks.append((text, "paragraph", {}))

        return blocks

    @staticmethod
    def _normalize_text(text: str) -> str:
        if not text:
            return ""
        text = text.replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\s*\n\s*", " ", text)
        return text.strip()

    def _table_to_markdown(self, table_el) -> str:
        rows = table_el.find_all("tr")
        if not rows:
            return ""

        md_rows: List[str] = []
        for i, row in enumerate(rows):
            cells = row.find_all(["td", "th"])
            clean = [self._normalize_text(c.get_text(separator=" ")) for c in cells]
            if not clean:
                continue
            md_rows.append("| " + " | ".join(clean) + " |")
            if i == 0:
                md_rows.append("| " + " | ".join(["---"] * len(clean)) + " |")

        return "\n".join(md_rows)

    # ── 拼装 ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_blocks(
        collected: List[Tuple[str, str, Dict[str, Any]]]
    ) -> Tuple[List[Block], str]:
        blocks: List[Block] = []
        contents: List[str] = []
        position_offset = 0

        for content, block_type, extra in collected:
            start_pos = position_offset
            end_pos = start_pos + len(content)
            position_offset = end_pos + 1  # 与 "\n".join 的全文偏移保持一致

            blocks.append(
                Block(
                    id=f"b_{len(blocks)}",
                    type=block_type,
                    content=content,
                    position={"start": start_pos, "end": end_pos},
                    page=0,
                    extra=extra or None,
                )
            )
            contents.append(content)

        return blocks, "\n".join(contents)
