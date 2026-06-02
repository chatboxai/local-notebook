import asyncio
import io
import json
import logging
import os
import zipfile
from dataclasses import dataclass
from typing import Optional, List

import httpx

logger = logging.getLogger("mineru_client")


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
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            return len(reader.pages)
        except Exception:
            return 0

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
        from datetime import datetime, timezone

        if not os.path.exists(file_path):
            return MinerUResult(
                markdown="", content_list=[], success=False,
                error_message=f"文件不存在: {file_path}"
            ), None

        page_count = await self._get_pdf_page_count(file_path)

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

            return self._parse_zip(resp.content, page_count, file_path), batch_id

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

    def _parse_zip(self, zip_bytes: bytes, page_count: int, file_path: str) -> MinerUResult:
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
                    img_name = os.path.basename(name)
                    local_path = os.path.join(img_dir, img_name)
                    with open(local_path, "wb") as f:
                        f.write(zf.read(name))
                    images_dict[name] = local_path
                    images_dict[img_name] = local_path
                    images_dict[f"images/{img_name}"] = local_path

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
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            return len(reader.pages)
        except Exception:
            return 0

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
