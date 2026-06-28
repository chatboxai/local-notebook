import re
from dataclasses import dataclass
from typing import Any, List

from .base import BaseParser, Block, ParseResult


@dataclass
class _MergedAudioSegment:
    speaker: int
    text: str
    start: int
    end: int
    source_segment_count: int = 1


class AudioParser(BaseParser):
    MAX_MERGE_GAP_MS = 1200
    SOFT_TEXT_UNITS = 90
    HARD_TEXT_UNITS = 150
    TERMINAL_PUNCTUATION = set("。！？；.!?;")
    LATIN_WORD_RE = re.compile(r"[A-Za-z0-9]+")

    def get_supported_extensions(self) -> List[str]:
        return [".wav", ".mp3", ".m4a"]

    async def parse(self, file_path: str) -> ParseResult:
        import config
        from services.funasr_client import FunASRClient

        enabled, base_url = await config.resolve_funasr_config()
        if not enabled or not base_url:
            raise RuntimeError("FunASR 服务地址未配置。请在「设置 → FunASR」配置服务地址后重新上传。")

        result = await FunASRClient(base_url).transcribe(file_path)
        if not result.success:
            raise RuntimeError(f"音频识别失败: {result.error_message or '未知错误'}")

        blocks = self._build_blocks(result.segments)
        text = "\n".join(block.content for block in blocks)

        return ParseResult(
            text=text,
            blocks=blocks,
            page_count=0,
            images=[],
        )

    def _build_blocks(self, segments) -> list[Block]:
        blocks: list[Block] = []
        position_offset = 0

        for seg in self._merge_segments(segments):
            content = seg.text
            if not content:
                continue

            start_pos = position_offset
            end_pos = start_pos + len(content)
            position_offset = end_pos + 1

            blocks.append(Block(
                id=f"b_{len(blocks)}",
                type="paragraph",
                content=content,
                position={"start": start_pos, "end": end_pos},
                page=0,
                extra={
                    "media_type": "audio",
                    "speaker": seg.speaker,
                    "time_start": seg.start,
                    "time_end": seg.end,
                    "time_range": self._format_time_range(seg.start, seg.end),
                    "raw_text": content,
                    "source_segment_count": seg.source_segment_count,
                },
            ))

        return blocks

    def _merge_segments(self, segments: list[Any]) -> list[_MergedAudioSegment]:
        merged: list[_MergedAudioSegment] = []
        current: _MergedAudioSegment | None = None

        for raw_segment in segments:
            segment = self._normalize_segment(raw_segment)
            if not segment:
                continue

            if current and self._should_merge(current, segment):
                current.text = self._join_text(current.text, segment.text)
                current.end = max(current.end, segment.end)
                current.source_segment_count += segment.source_segment_count
                continue

            if current:
                merged.append(current)
            current = segment

        if current:
            merged.append(current)

        return merged

    def _normalize_segment(self, segment: Any) -> _MergedAudioSegment | None:
        text = str(getattr(segment, "text", "") or "").strip()
        if not text:
            return None
        return _MergedAudioSegment(
            speaker=self._int_or_zero(getattr(segment, "speaker", 0)),
            text=text,
            start=self._int_or_zero(getattr(segment, "start", 0)),
            end=self._int_or_zero(getattr(segment, "end", 0)),
        )

    def _should_merge(self, current: _MergedAudioSegment, next_segment: _MergedAudioSegment) -> bool:
        if current.speaker != next_segment.speaker:
            return False

        gap_ms = max(0, next_segment.start - current.end)
        if gap_ms > self.MAX_MERGE_GAP_MS:
            return False

        current_units = self._text_units(current.text)
        combined_units = self._text_units(self._join_text(current.text, next_segment.text))
        if combined_units > self.HARD_TEXT_UNITS:
            return False

        if current_units >= self.SOFT_TEXT_UNITS and self._ends_with_terminal_punctuation(current.text):
            return False

        return True

    def _text_units(self, text: str) -> int:
        cjk_units = sum(1 for char in text if self._is_cjk(char))
        latin_units = len(self.LATIN_WORD_RE.findall(text)) * 2
        other_units = sum(
            1
            for char in text
            if not char.isspace()
            and not self._is_cjk(char)
            and not char.isascii()
            and not self._is_punctuation(char)
        )
        return cjk_units + latin_units + other_units

    def _ends_with_terminal_punctuation(self, text: str) -> bool:
        stripped = text.rstrip()
        return bool(stripped and stripped[-1] in self.TERMINAL_PUNCTUATION)

    def _join_text(self, left: str, right: str) -> str:
        if not left:
            return right
        if not right:
            return left
        if self._needs_space(left[-1], right[0]):
            return f"{left} {right}"
        return f"{left}{right}"

    @staticmethod
    def _needs_space(left: str, right: str) -> bool:
        if not (left.isascii() and right.isascii()):
            return False
        return (left.isalnum() or left in ".,?!;:%") and (right.isalnum() or right in "([{")

    @staticmethod
    def _is_cjk(char: str) -> bool:
        return "\u4e00" <= char <= "\u9fff" or "\u3400" <= char <= "\u4dbf"

    @staticmethod
    def _is_punctuation(char: str) -> bool:
        return not char.isalnum() and not char.isspace()

    @staticmethod
    def _int_or_zero(value) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def _format_time_range(self, start_ms: int, end_ms: int) -> str:
        return f"{self._format_time(start_ms)}-{self._format_time(end_ms)}"

    @staticmethod
    def _format_time(ms: int) -> str:
        total_seconds = max(0, ms // 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
