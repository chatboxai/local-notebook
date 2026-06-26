import asyncio
import io
import json
import logging
import os
import tempfile
import zipfile
from dataclasses import dataclass
from typing import Optional, List

import httpx

logger = logging.getLogger("mineru_client")


def _env_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


MINERU_PDF_CHUNK_PAGES = _env_int("MINERU_PDF_CHUNK_PAGES", 100)


def _make_minimal_pdf() -> bytes:
    return (
        b"%PDF-1.0\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 72 72]/Parent 2 0 R/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 22>>stream\nBT /F1 12 Tf (hi) Tj ET\nendstream\nendobj\n"
        b"xref\n0 5\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000210 00000 n \n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n282\n%%EOF\n"
    )


@dataclass
class MinerUResult:
    markdown: str
    content_list: list
    success: bool
    error_message: Optional[str] = None
    page_count: int = 0
    images: dict = None


@dataclass(frozen=True)
class PDFChunk:
    file_path: str
    start_page: int
    end_page: int


def _safe_file_stem(file_path: str) -> str:
    stem = os.path.splitext(os.path.basename(file_path))[0]
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in stem)
    return safe[:80] or "document"


def _get_pdf_page_count_sync(file_path: str) -> int:
    try:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        return len(reader.pages)
    except Exception:
        return 0


async def _get_pdf_page_count(file_path: str) -> int:
    return await asyncio.to_thread(_get_pdf_page_count_sync, file_path)


def _split_pdf_sync(file_path: str, output_dir: str, pages_per_chunk: int) -> list[PDFChunk]:
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    stem = _safe_file_stem(file_path)
    chunks: list[PDFChunk] = []

    for start in range(0, total_pages, pages_per_chunk):
        end = min(start + pages_per_chunk, total_pages)
        writer = PdfWriter()
        for page_index in range(start, end):
            writer.add_page(reader.pages[page_index])

        chunk_name = f"{stem}_p{start + 1:04d}-{end:04d}.pdf"
        chunk_path = os.path.join(output_dir, chunk_name)
        with open(chunk_path, "wb") as f:
            writer.write(f)

        chunks.append(PDFChunk(file_path=chunk_path, start_page=start, end_page=end))

    return chunks


async def _split_pdf(file_path: str, output_dir: str, pages_per_chunk: int) -> list[PDFChunk]:
    return await asyncio.to_thread(_split_pdf_sync, file_path, output_dir, pages_per_chunk)


def _prefix_image_path(image_path: str, prefix: str) -> str:
    normalized = str(image_path).replace("\\", "/")
    image_name = os.path.basename(normalized)
    if not image_name:
        return normalized

    directory = os.path.dirname(normalized).replace("\\", "/")
    prefixed_name = f"{prefix}{image_name}"
    return f"{directory}/{prefixed_name}" if directory else prefixed_name


def _add_prefixed_image_aliases(target: dict, key: str, value, prefix: str) -> None:
    prefixed_key = _prefix_image_path(key, prefix)
    target[prefixed_key] = value

    prefixed_basename = os.path.basename(prefixed_key)
    if prefixed_basename:
        target[prefixed_basename] = value
        target[f"images/{prefixed_basename}"] = value


def _offset_content_list(content_list: list, page_offset: int, image_prefix: str) -> list:
    adjusted = []

    for item in content_list or []:
        if not isinstance(item, dict):
            adjusted.append(item)
            continue

        copied = dict(item)
        page_idx = copied.get("page_idx")
        if isinstance(page_idx, int):
            copied["page_idx"] = page_idx + page_offset

        for key in ("page", "start_page", "end_page"):
            value = copied.get(key)
            if isinstance(value, int):
                copied[key] = value + page_offset

        img_path = copied.get("img_path")
        if img_path:
            copied["img_path"] = _prefix_image_path(str(img_path), image_prefix)

        adjusted.append(copied)

    return adjusted


def _merge_chunk_results(chunk_results: list[tuple[PDFChunk, MinerUResult]], page_count: int) -> MinerUResult:
    markdown_parts: list[str] = []
    content_list: list = []
    images: dict = {}

    for index, (chunk, result) in enumerate(chunk_results, start=1):
        image_prefix = f"part_{index:03d}_"

        if result.markdown:
            markdown_parts.append(result.markdown.strip())

        content_list.extend(
            _offset_content_list(result.content_list or [], chunk.start_page, image_prefix)
        )

        for key, value in (result.images or {}).items():
            _add_prefixed_image_aliases(images, str(key), value, image_prefix)

    return MinerUResult(
        markdown="\n\n".join(part for part in markdown_parts if part),
        content_list=content_list,
        success=True,
        page_count=page_count,
        images=images,
    )


class MinerUClient:

    MAX_RETRIES = 10
    RETRY_BASE_DELAY = 15

    def __init__(self, base_url: str, timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def parse_pdf(
        self,
        file_path: str,
        parse_method: str = "auto",
        return_content_list: bool = True
    ) -> MinerUResult:
        if not os.path.exists(file_path):
            return MinerUResult(
                markdown="",
                content_list=[],
                success=False,
                error_message=f"文件不存在: {file_path}"
            )

        page_count = await self._get_pdf_page_count(file_path)
        if page_count > MINERU_PDF_CHUNK_PAGES:
            return await self._parse_pdf_in_page_chunks(
                file_path=file_path,
                page_count=page_count,
                parse_method=parse_method,
                return_content_list=return_content_list,
            )

        return await self._parse_pdf_single(
            file_path=file_path,
            page_count=page_count,
            parse_method=parse_method,
            return_content_list=return_content_list,
        )

    async def _parse_pdf_in_page_chunks(
        self,
        file_path: str,
        page_count: int,
        parse_method: str,
        return_content_list: bool,
    ) -> MinerUResult:
        logger.info(
            f"PDF 页数 {page_count} 超过 {MINERU_PDF_CHUNK_PAGES}，"
            "按页切片调用 MinerU"
        )

        with tempfile.TemporaryDirectory(prefix="mineru_chunks_") as temp_dir:
            chunks = await _split_pdf(file_path, temp_dir, MINERU_PDF_CHUNK_PAGES)
            chunk_results: list[tuple[PDFChunk, MinerUResult]] = []

            for index, chunk in enumerate(chunks, start=1):
                logger.info(
                    f"MinerU 切片 {index}/{len(chunks)}: "
                    f"pages {chunk.start_page + 1}-{chunk.end_page}"
                )
                result = await self._parse_pdf_single(
                    file_path=chunk.file_path,
                    page_count=chunk.end_page - chunk.start_page,
                    parse_method=parse_method,
                    return_content_list=return_content_list,
                )

                if not result.success:
                    return MinerUResult(
                        markdown="",
                        content_list=[],
                        success=False,
                        error_message=(
                            f"第 {chunk.start_page + 1}-{chunk.end_page} 页解析失败: "
                            f"{result.error_message or '未知错误'}"
                        ),
                        page_count=page_count,
                    )

                chunk_results.append((chunk, result))

        merged = _merge_chunk_results(chunk_results, page_count)
        logger.info(
            f"MinerU 切片合并完成: chunks={len(chunk_results)}, "
            f"markdown={len(merged.markdown)} chars, "
            f"content_list={len(merged.content_list)}, pages={page_count}"
        )
        return merged

    async def _parse_pdf_single(
        self,
        file_path: str,
        page_count: int,
        parse_method: str,
        return_content_list: bool,
    ) -> MinerUResult:

        try:
            logger.info(f"调用 MinerU 服务: {self.base_url}/file_parse")

            data = {
                "parse_method": parse_method,
                "return_md": "true",
                "return_content_list": "true" if return_content_list else "false",
                "return_middle_json": "true",
                "return_model_output": "true",
                "return_images": "true",
                "response_format_zip": "false",
                "formula_enable": "true",
                "table_enable": "true",
            }

            resp = None
            for attempt in range(self.MAX_RETRIES):
                with open(file_path, "rb") as f:
                    files = {"files": (os.path.basename(file_path), f, "application/pdf")}
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        resp = await client.post(
                            f"{self.base_url}/file_parse",
                            files=files,
                            data=data,
                        )

                if resp.status_code != 503:
                    break

                retry_after = int(resp.headers.get("Retry-After", 0))
                delay = max(retry_after, self.RETRY_BASE_DELAY * (2 ** attempt))
                delay = min(delay, 300)
                logger.warning(
                    f"MinerU 服务繁忙 (503)，第 {attempt+1}/{self.MAX_RETRIES} 次重试，"
                    f"等待 {delay}s..."
                )
                await asyncio.sleep(delay)

            if resp.status_code == 503:
                return MinerUResult(
                    markdown="", content_list=[], success=False,
                    error_message=f"MinerU 服务持续繁忙，已重试 {self.MAX_RETRIES} 次仍无法处理"
                )

            if resp.status_code != 200:
                error_msg = f"MinerU 服务返回错误: {resp.status_code} - {resp.text[:500]}"
                logger.error(error_msg)
                return MinerUResult(
                    markdown="", content_list=[], success=False, error_message=error_msg
                )

            result = resp.json()

            markdown = ""
            content_list = []
            images_dict = {}

            if "results" in result and isinstance(result["results"], dict):
                for file_name, file_result in result["results"].items():
                    if isinstance(file_result, dict):
                        markdown = file_result.get("md_content", "")
                        content_list_raw = file_result.get("content_list", [])
                        images_dict = file_result.get("images", {})

                        if isinstance(content_list_raw, str):
                            try:
                                import json
                                content_list = json.loads(content_list_raw)
                            except json.JSONDecodeError:
                                content_list = []
                        else:
                            content_list = content_list_raw

                        type_counts = {}
                        for item in content_list:
                            if isinstance(item, dict):
                                item_type = item.get("type", "unknown")
                                type_counts[item_type] = type_counts.get(item_type, 0) + 1
                        logger.info(f"MinerU content_list 类型统计: {type_counts}")

                    elif isinstance(file_result, str):
                        markdown = file_result
                    break

            logger.info(f"MinerU 解析完成，Markdown 长度: {len(markdown)}，页数: {page_count}，图片数: {len(images_dict)}")
            return MinerUResult(
                markdown=markdown,
                content_list=content_list,
                success=True,
                page_count=page_count,
                images=images_dict
            )

        except httpx.ConnectError:
            error_msg = f"无法连接 MinerU 服务: {self.base_url}"
            logger.error(error_msg)
            return MinerUResult(
                markdown="", content_list=[], success=False, error_message=error_msg
            )
        except httpx.TimeoutException:
            error_msg = f"MinerU 服务超时（{self.timeout}秒）"
            logger.error(error_msg)
            return MinerUResult(
                markdown="", content_list=[], success=False, error_message=error_msg
            )
        except Exception as e:
            error_msg = f"PDF 解析失败: {str(e)}"
            logger.exception(error_msg)
            return MinerUResult(
                markdown="", content_list=[], success=False, error_message=error_msg
            )

    async def _get_pdf_page_count(self, file_path: str) -> int:
        return await _get_pdf_page_count(file_path)

    async def health_check(self) -> bool:
        pdf_bytes = _make_minimal_pdf()
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self.base_url}/file_parse",
                    files={"files": ("probe.pdf", pdf_bytes, "application/pdf")},
                    data={"parse_method": "auto", "return_md": "true"},
                )
                return resp.status_code == 200
        except Exception:
            return False


MINERU_CLOUD_BASE = "https://mineru.net"
POLL_INTERVAL = 10
TASK_TIMEOUT_SECONDS = 3 * 60 * 60
POLL_MAX_ATTEMPTS = TASK_TIMEOUT_SECONDS // POLL_INTERVAL


class MinerUCloudClient:

    def __init__(self, api_key: str, timeout: int = 300):
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def parse_pdf(
        self,
        file_path: str,
        existing_batch_id: str | None = None,
        batch_created_at: "datetime | None" = None,
    ) -> tuple[MinerUResult, str | None]:
        if not os.path.exists(file_path):
            return MinerUResult(
                markdown="", content_list=[], success=False,
                error_message=f"文件不存在: {file_path}"
            ), None

        page_count = await self._get_pdf_page_count(file_path)
        if page_count > MINERU_PDF_CHUNK_PAGES:
            return await self._parse_pdf_in_page_chunks(file_path, page_count)

        return await self._parse_pdf_single(
            file_path=file_path,
            page_count=page_count,
            existing_batch_id=existing_batch_id,
            batch_created_at=batch_created_at,
        )

    async def _parse_pdf_in_page_chunks(
        self,
        file_path: str,
        page_count: int,
    ) -> tuple[MinerUResult, str | None]:
        logger.info(
            f"[cloud] PDF 页数 {page_count} 超过 {MINERU_PDF_CHUNK_PAGES}，"
            "按页切片上传 MinerU"
        )

        with tempfile.TemporaryDirectory(prefix="mineru_chunks_") as temp_dir:
            chunks = await _split_pdf(file_path, temp_dir, MINERU_PDF_CHUNK_PAGES)
            chunk_results: list[tuple[PDFChunk, MinerUResult]] = []

            for index, chunk in enumerate(chunks, start=1):
                image_prefix = f"part_{index:03d}_"
                logger.info(
                    f"[cloud] 切片 {index}/{len(chunks)}: "
                    f"pages {chunk.start_page + 1}-{chunk.end_page}"
                )

                result, _batch_id = await self._parse_pdf_single(
                    file_path=chunk.file_path,
                    page_count=chunk.end_page - chunk.start_page,
                    image_output_file_path=file_path,
                    image_prefix=image_prefix,
                )

                if not result.success:
                    return MinerUResult(
                        markdown="",
                        content_list=[],
                        success=False,
                        error_message=(
                            f"第 {chunk.start_page + 1}-{chunk.end_page} 页解析失败: "
                            f"{result.error_message or '未知错误'}"
                        ),
                        page_count=page_count,
                    ), None

                chunk_results.append((chunk, result))

        merged = _merge_chunk_results(chunk_results, page_count)
        logger.info(
            f"[cloud] 切片合并完成: chunks={len(chunk_results)}, "
            f"markdown={len(merged.markdown)} chars, "
            f"content_list={len(merged.content_list)}, pages={page_count}"
        )
        return merged, None

    async def _parse_pdf_single(
        self,
        file_path: str,
        page_count: int,
        existing_batch_id: str | None = None,
        batch_created_at: "datetime | None" = None,
        image_output_file_path: str | None = None,
        image_prefix: str = "",
    ) -> tuple[MinerUResult, str | None]:
        from datetime import datetime, timezone

        try:
            batch_id = None

            if existing_batch_id and batch_created_at:
                if batch_created_at.tzinfo is None:
                    batch_created_at = batch_created_at.replace(tzinfo=timezone.utc)
                elapsed = (datetime.now(timezone.utc) - batch_created_at).total_seconds()
                if elapsed < TASK_TIMEOUT_SECONDS:
                    logger.info(f"[cloud] 恢复 batch: {existing_batch_id} (已过 {elapsed:.0f}s)")
                    batch_id = existing_batch_id
                else:
                    logger.info(f"[cloud] batch 已超时 ({elapsed:.0f}s)，重新提交")

            if not batch_id:
                batch_id = await self._submit(file_path)
                if not batch_id:
                    return MinerUResult(
                        markdown="", content_list=[], success=False,
                        error_message="创建 MinerU 线上任务失败"
                    ), None

            zip_url = await self._poll(batch_id)
            if not zip_url:
                return MinerUResult(
                    markdown="", content_list=[], success=False,
                    error_message="MinerU 线上解析超时或失败"
                ), batch_id

            logger.info(f"[cloud] 下载结果 zip...")
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(zip_url)

            if resp.status_code != 200:
                return MinerUResult(
                    markdown="", content_list=[], success=False,
                    error_message=f"下载结果失败: HTTP {resp.status_code}"
                ), batch_id

            return self._parse_zip(
                resp.content,
                page_count,
                image_output_file_path or file_path,
                image_prefix=image_prefix,
            ), batch_id

        except httpx.ConnectError:
            return MinerUResult(
                markdown="", content_list=[], success=False,
                error_message=f"无法连接 MinerU 线上服务 ({MINERU_CLOUD_BASE})"
            ), None
        except httpx.TimeoutException:
            return MinerUResult(
                markdown="", content_list=[], success=False,
                error_message="MinerU 线上服务超时"
            ), None
        except Exception as e:
            logger.exception(f"[cloud] PDF 解析失败: {e}")
            return MinerUResult(
                markdown="", content_list=[], success=False,
                error_message=f"PDF 解析失败: {str(e)}"
            ), None

    async def _submit(self, file_path: str) -> str | None:
        file_name = os.path.basename(file_path)
        logger.info(f"[cloud] 创建 batch: {file_name}")

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{MINERU_CLOUD_BASE}/api/v4/file-urls/batch",
                headers=self.headers,
                json={
                    "files": [{"name": file_name, "is_ocr": False}],
                    "enable_formula": True,
                    "enable_table": True,
                },
            )

        result = resp.json()
        if result.get("code") != 0:
            logger.error(f"[cloud] 创建 batch 失败: {result.get('msg', '')}")
            return None

        batch_id = result["data"]["batch_id"]
        file_urls = result["data"]["file_urls"]
        upload_url = file_urls[0] if isinstance(file_urls[0], str) else file_urls[0].get("url", "")

        logger.info(f"[cloud] batch_id={batch_id}, 上传 ({os.path.getsize(file_path)/1024:.0f} KB)")
        with open(file_path, "rb") as f:
            file_data = f.read()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.put(upload_url, content=file_data)

        if resp.status_code not in (200, 201):
            logger.error(f"[cloud] 上传失败: HTTP {resp.status_code}")
            return None

        return batch_id

    async def _poll(self, batch_id: str) -> str | None:
        logger.info(f"[cloud] 轮询中 (batch={batch_id})...")
        for attempt in range(POLL_MAX_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{MINERU_CLOUD_BASE}/api/v4/extract-results/batch/{batch_id}",
                    headers=self.headers,
                )

            result = resp.json()
            if result.get("code") != 0:
                continue

            extract_result = result.get("data", {}).get("extract_result", [])
            if not extract_result:
                continue

            state = extract_result[0].get("state", "unknown")
            if attempt % 12 == 0:
                logger.info(f"[cloud] [{attempt+1}/{POLL_MAX_ATTEMPTS}] state={state}")

            if state == "done":
                logger.info("[cloud] 解析完成")
                return extract_result[0].get("full_zip_url") or None
            elif state == "failed":
                logger.error("[cloud] 线上解析失败")
                return None

        logger.error(f"[cloud] 轮询超时 ({TASK_TIMEOUT_SECONDS}s)")
        return None

    def _parse_zip(
        self,
        zip_bytes: bytes,
        page_count: int,
        file_path: str,
        image_prefix: str = "",
    ) -> MinerUResult:
        markdown = ""
        content_list = []
        images_dict = {}

        img_dir = os.path.join(os.path.dirname(file_path), "images")
        os.makedirs(img_dir, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for name in zf.namelist():
                if name.endswith(".md"):
                    markdown = zf.read(name).decode("utf-8")

                elif name.endswith("_content_list.json") or os.path.basename(name) == "content_list.json":
                    raw = zf.read(name).decode("utf-8")
                    content_list = json.loads(raw)

                elif name.startswith("images/") and not name.endswith("/"):
                    original_img_name = os.path.basename(name)
                    img_name = f"{image_prefix}{original_img_name}"
                    local_path = os.path.join(img_dir, img_name)
                    with open(local_path, "wb") as f:
                        f.write(zf.read(name))
                    images_dict[name] = local_path
                    images_dict[original_img_name] = local_path
                    images_dict[f"images/{original_img_name}"] = local_path

        type_counts = {}
        for item in content_list:
            if isinstance(item, dict):
                t = item.get("type", "unknown")
                type_counts[t] = type_counts.get(t, 0) + 1
        logger.info(f"[cloud] 解析完成: markdown={len(markdown)} chars, "
                     f"content_list={len(content_list)} items {type_counts}, "
                     f"images={len(images_dict)//3} files, pages={page_count}")

        return MinerUResult(
            markdown=markdown,
            content_list=content_list,
            success=True,
            page_count=page_count,
            images=images_dict,
        )

    async def _get_pdf_page_count(self, file_path: str) -> int:
        return await _get_pdf_page_count(file_path)

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{MINERU_CLOUD_BASE}/api/v4/file-urls/batch",
                    headers=self.headers,
                    json={"files": [{"name": "test.pdf"}]},
                )
            result = resp.json()
            return result.get("code") == 0
        except Exception:
            return False


async def health_check(base_url: str = "", api_key: str = "", source: str = "local") -> dict:
    if source == "api":
        if not api_key:
            return {"ok": False, "msg": "未配置 API Key"}
        client = MinerUCloudClient(api_key)
        is_healthy = await client.health_check()
        return {"ok": is_healthy, "msg": "API Key 验证成功" if is_healthy else "API Key 无效"}
    else:
        if not base_url:
            return {"ok": False, "msg": "未配置服务地址"}
        client = MinerUClient(base_url)
        is_healthy = await client.health_check()
        return {"ok": is_healthy, "url": base_url}
