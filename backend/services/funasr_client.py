import os
from dataclasses import dataclass, field
from typing import Optional

import httpx


@dataclass
class FunASRSegment:
    speaker: int
    text: str
    start: int
    end: int


@dataclass
class FunASRResult:
    success: bool
    duration: int = 0
    speaker_count: int = 0
    full_text: str = ""
    segments: list[FunASRSegment] = field(default_factory=list)
    error_message: Optional[str] = None


class FunASRClient:
    def __init__(self, base_url: str, timeout: int | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout or int(os.getenv("FUNASR_TIMEOUT", "600"))

    async def transcribe(
        self,
        file_path: str,
        hotword: str | None = None,
    ) -> FunASRResult:
        if not os.path.exists(file_path):
            return FunASRResult(success=False, error_message=f"文件不存在: {file_path}")

        data = {}
        if hotword:
            data["hotword"] = hotword

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                with open(file_path, "rb") as f:
                    response = await client.post(
                        f"{self.base_url}/transcribe",
                        files={"file": (os.path.basename(file_path), f)},
                        data=data,
                    )
        except httpx.TimeoutException:
            return FunASRResult(success=False, error_message=f"FunASR 服务超时（{self.timeout}秒）")
        except httpx.ConnectError:
            return FunASRResult(success=False, error_message=f"无法连接 FunASR 服务: {self.base_url}")
        except Exception as exc:
            return FunASRResult(success=False, error_message=f"语音识别失败: {exc}")

        if response.status_code != 200:
            return FunASRResult(
                success=False,
                error_message=f"FunASR 服务返回错误: {response.status_code} - {response.text[:500]}",
            )

        try:
            payload = response.json()
        except ValueError:
            return FunASRResult(success=False, error_message="FunASR 服务返回了非 JSON 响应")

        if not isinstance(payload, dict):
            return FunASRResult(success=False, error_message="FunASR 服务响应格式不正确")

        if not payload.get("success"):
            return FunASRResult(success=False, error_message=payload.get("error") or "FunASR 识别失败")

        result_data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        raw_segments = result_data.get("segments", [])
        if not isinstance(raw_segments, list):
            return FunASRResult(success=False, error_message="FunASR 响应 segments 格式不正确")

        segments = [
            FunASRSegment(
                speaker=self._int_or_zero(seg.get("speaker")),
                text=str(seg.get("text", "") or "").strip(),
                start=self._int_or_zero(seg.get("start")),
                end=self._int_or_zero(seg.get("end")),
            )
            for seg in raw_segments
            if isinstance(seg, dict)
            if str(seg.get("text", "") or "").strip()
        ]

        return FunASRResult(
            success=True,
            duration=self._int_or_zero(result_data.get("duration")),
            speaker_count=self._int_or_zero(result_data.get("speaker_count")),
            full_text=str(result_data.get("full_text", "") or ""),
            segments=segments,
        )

    async def health_check(self) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/health")
            if response.status_code != 200:
                return False, f"服务返回 {response.status_code}"
            try:
                data = response.json()
            except ValueError:
                return False, "服务返回了非 JSON 响应"
            if not isinstance(data, dict):
                return False, "服务响应格式不正确"
            if data.get("model_loaded") is False:
                return False, "服务可连接，但模型尚未加载"
            return True, "FunASR 服务连接成功"
        except httpx.ConnectError:
            return False, f"无法连接到 {self.base_url}"
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _int_or_zero(value) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
