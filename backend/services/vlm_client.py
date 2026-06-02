import base64
import logging
from typing import Optional

import httpx

import config

logger = logging.getLogger(__name__)

BAILIAN_VLM_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"


async def resolve_vlm_config() -> tuple[str, str, str]:
    source = await config.get_setting("vlm_source", "")
    if source == "custom":
        api_key = await config.get_setting("vlm_api_key", "")
        base_url = await config.get_setting("vlm_base_url", "")
        model = await config.get_setting("vlm_model", "")
        return api_key or "", base_url or "", model or ""
    api_key = await config.get_setting("bailian_api_key", "")
    base_url = BAILIAN_VLM_URL
    model = await config.get_setting("vlm_bailian_model", "")
    return api_key or "", base_url, model or ""


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_mime_type(image_path: str) -> str:
    ext = image_path.lower().split(".")[-1] if "." in image_path else ""
    mime_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "bmp": "image/bmp",
    }
    return mime_types.get(ext, "image/jpeg")


async def describe_image(
    image_path: str,
    prompt: Optional[str] = None,
    timeout: float = 60.0,
) -> tuple[str, str]:
    api_key, base_url, model = await resolve_vlm_config()

    if not api_key:
        raise RuntimeError("VLM API Key 未配置，请在设置页面配置 VLM")
    if not base_url:
        raise RuntimeError("VLM Base URL 未配置")
    if not model:
        raise RuntimeError("VLM 模型未配置")

    if prompt is None:
        prompt = (
            "请详细描述这张图片的内容。包括：\n"
            "1. 图片的主题和主要内容\n"
            "2. 关键视觉元素（物体、人物、场景、文字等）\n"
            "3. 整体风格和氛围\n"
            "请用中文回答，描述要详细但简洁。"
        )

    base64_image = encode_image_to_base64(image_path)
    mime_type = get_image_mime_type(image_path)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        "max_tokens": 1000,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                description = data["choices"][0]["message"]["content"]
                return description.strip(), model
            else:
                raise RuntimeError(f"VLM 响应格式异常: {data}")

        except httpx.HTTPStatusError as e:
            error_msg = f"VLM API 错误: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    error_msg += f" - {error_data['error'].get('message', '')}"
            except Exception:
                pass
            raise RuntimeError(error_msg)
        except Exception as e:
            raise RuntimeError(f"VLM 调用失败: {e}")
