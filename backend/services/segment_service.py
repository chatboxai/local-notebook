import re
from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class SegmentInfo:
    segment_index: int
    content: str
    pos_start: int
    pos_end: int
    block_ids: List[str]


@dataclass
class SplitResult:
    segments: List[SegmentInfo]
    warnings: List[str] = field(default_factory=list)


class SegmentService:

    OVERFLOW_RATIO = 1.2

    def __init__(
        self,
        min_segment_chars: int = 200,
        max_segment_chars: int = 400,
        overlap_chars: int = 50
    ):
        self.min_segment_chars = min_segment_chars
        self.max_segment_chars = max_segment_chars
        self.overlap_chars = overlap_chars
        self.hard_limit = int(max_segment_chars * self.OVERFLOW_RATIO)

    def split_text(
        self,
        raw_text: str,
        blocks: List[Dict[str, Any]] | None = None
    ) -> List[SegmentInfo]:
        result = self.split_text_with_warnings(raw_text, blocks or [])
        return result.segments

    def split_text_with_warnings(
        self,
        raw_text: str,
        blocks: List[Dict[str, Any]]
    ) -> SplitResult:
        if not raw_text:
            return SplitResult(segments=[], warnings=[])

        units = self._split_into_units(raw_text)
        if not units:
            return SplitResult(segments=[], warnings=[])

        segments = []
        warnings = []
        current_content = ""
        current_start = 0
        segment_index = 0

        for unit in units:
            unit_text = unit['text']
            unit_start = unit['start']
            unit_end = unit['end']
            is_atomic = unit.get('is_atomic', False)

            if is_atomic:
                if current_content.strip():
                    if len(current_content) >= self.min_segment_chars:
                        current_end = current_start + len(current_content)
                        block_ids = self._find_block_ids(blocks, current_start, current_end)
                        segments.append(SegmentInfo(
                            segment_index=segment_index,
                            content=current_content.strip(),
                            pos_start=current_start,
                            pos_end=current_end,
                            block_ids=block_ids
                        ))
                        segment_index += 1
                        current_content = ""

                atomic_content = current_content + unit_text if current_content else unit_text
                atomic_start = current_start if current_content else unit_start

                if len(atomic_content) > self.hard_limit:
                    original_len = len(atomic_content)
                    atomic_content = atomic_content[:self.hard_limit]
                    warnings.append(
                        f"Segment {segment_index}: 内容过长({original_len}字)，已截断至{self.hard_limit}字"
                    )

                block_ids = self._find_block_ids(blocks, atomic_start, unit_end)
                segments.append(SegmentInfo(
                    segment_index=segment_index,
                    content=atomic_content.strip(),
                    pos_start=atomic_start,
                    pos_end=unit_end,
                    block_ids=block_ids
                ))
                segment_index += 1
                current_content = ""
                current_start = unit_end
                continue

            if len(current_content) + len(unit_text) <= self.max_segment_chars:
                if not current_content:
                    current_start = unit_start
                current_content += unit_text
            else:
                if len(current_content) >= self.min_segment_chars:
                    current_end = current_start + len(current_content)
                    block_ids = self._find_block_ids(blocks, current_start, current_end)
                    segments.append(SegmentInfo(
                        segment_index=segment_index,
                        content=current_content.strip(),
                        pos_start=current_start,
                        pos_end=current_end,
                        block_ids=block_ids
                    ))
                    segment_index += 1
                    overlap_text = current_content[-self.overlap_chars:] if len(current_content) > self.overlap_chars else ""
                    current_content = overlap_text + unit_text
                    current_start = unit_end - len(current_content)
                else:
                    current_content += unit_text

        if current_content.strip():
            current_end = current_start + len(current_content)
            block_ids = self._find_block_ids(blocks, current_start, current_end)

            if len(current_content) > self.hard_limit:
                original_len = len(current_content)
                current_content = current_content[:self.hard_limit]
                warnings.append(
                    f"Segment {segment_index}: 内容过长({original_len}字)，已截断至{self.hard_limit}字"
                )

            if len(current_content) < self.min_segment_chars and segments:
                last_seg = segments[-1]
                merged_content = last_seg.content + "\n" + current_content.strip()
                if len(merged_content) <= self.max_segment_chars:
                    merged_block_ids = list(set(last_seg.block_ids + block_ids))
                    segments[-1] = SegmentInfo(
                        segment_index=last_seg.segment_index,
                        content=merged_content,
                        pos_start=last_seg.pos_start,
                        pos_end=current_end,
                        block_ids=sorted(
                            merged_block_ids,
                            key=lambda x: int(x.split('_')[1]) if '_' in x else 0
                        )
                    )
                else:
                    segments.append(SegmentInfo(
                        segment_index=segment_index,
                        content=current_content.strip(),
                        pos_start=current_start,
                        pos_end=current_end,
                        block_ids=block_ids
                    ))
            else:
                segments.append(SegmentInfo(
                    segment_index=segment_index,
                    content=current_content.strip(),
                    pos_start=current_start,
                    pos_end=current_end,
                    block_ids=block_ids
                ))

        return SplitResult(segments=segments, warnings=warnings)

    def _split_into_units(self, text: str) -> List[Dict[str, Any]]:
        units = []
        atomic_blocks = []

        md_table_pattern = r'(?:^|\n)(\|[^\n]*\|(?:\n\|[^\n]*\|)+)'
        for match in re.finditer(md_table_pattern, text):
            atomic_blocks.append({
                'start': match.start(1) if match.group(0).startswith('\n') else match.start(),
                'end': match.end(),
                'text': match.group(1) if match.group(0).startswith('\n') else match.group(0)
            })

        latex_block_pattern = r'\$\$[\s\S]*?\$\$'
        for match in re.finditer(latex_block_pattern, text):
            atomic_blocks.append({
                'start': match.start(),
                'end': match.end(),
                'text': match.group(0)
            })

        html_table_pattern = r'<table[^>]*>[\s\S]*?</table>'
        for match in re.finditer(html_table_pattern, text, re.IGNORECASE):
            atomic_blocks.append({
                'start': match.start(),
                'end': match.end(),
                'text': match.group(0)
            })

        atomic_blocks.sort(key=lambda x: x['start'])
        merged_atomic = []
        for block in atomic_blocks:
            if not merged_atomic or block['start'] >= merged_atomic[-1]['end']:
                merged_atomic.append(block)
            elif block['end'] > merged_atomic[-1]['end']:
                merged_atomic[-1]['end'] = block['end']
                merged_atomic[-1]['text'] = text[merged_atomic[-1]['start']:block['end']]

        current_pos = 0
        for atomic in merged_atomic:
            if current_pos < atomic['start']:
                normal_text = text[current_pos:atomic['start']]
                normal_units = self._split_sentences(normal_text, current_pos)
                units.extend(normal_units)
            units.append({
                'text': atomic['text'],
                'start': atomic['start'],
                'end': atomic['end'],
                'is_atomic': True
            })
            current_pos = atomic['end']

        if current_pos < len(text):
            normal_text = text[current_pos:]
            normal_units = self._split_sentences(normal_text, current_pos)
            units.extend(normal_units)

        return units

    def _split_sentences(self, text: str, offset: int = 0) -> List[Dict[str, Any]]:
        pattern = r'([。！？!?；;]+|\.(?:\s|$)|\n)'
        sentences = []
        last_end = 0

        for match in re.finditer(pattern, text):
            end = match.end()
            sentence_text = text[last_end:end]
            if sentence_text.strip():
                sentences.append({
                    "text": sentence_text,
                    "start": offset + last_end,
                    "end": offset + end,
                    "is_atomic": False
                })
            last_end = end

        if last_end < len(text):
            remaining = text[last_end:]
            if remaining.strip():
                sentences.append({
                    "text": remaining,
                    "start": offset + last_end,
                    "end": offset + len(text),
                    "is_atomic": False
                })

        return sentences

    def _find_block_ids(
        self,
        blocks: List[Dict[str, Any]],
        start_pos: int,
        end_pos: int
    ) -> List[str]:
        block_ids = []
        for block in blocks:
            block_start = block.get('pos_start', block.get('position', {}).get('start', 0))
            block_end = block.get('pos_end', block.get('position', {}).get('end', 0))
            block_id = block.get('block_id', block.get('id', ''))
            if block_start < end_pos and block_end > start_pos:
                block_ids.append(block_id)
        return block_ids


segment_service = SegmentService()
