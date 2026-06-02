import re
from typing import Generator, Dict, Any


class CitationParser:

    CITATION_PATTERN = re.compile(r'\[citation_(\d+)(?:-citation_(\d+))?\]')

    POTENTIAL_PATTERNS = [
        re.compile(r'^\[citation_\d*$'),
        re.compile(r'^\[citation_\d+-$'),
        re.compile(r'^\[citation_\d+-c$'),
        re.compile(r'^\[citation_\d+-ci$'),
        re.compile(r'^\[citation_\d+-cit$'),
        re.compile(r'^\[citation_\d+-cita$'),
        re.compile(r'^\[citation_\d+-citat$'),
        re.compile(r'^\[citation_\d+-citati$'),
        re.compile(r'^\[citation_\d+-citatio$'),
        re.compile(r'^\[citation_\d+-citation$'),
        re.compile(r'^\[citation_\d+-citation_$'),
        re.compile(r'^\[citation_\d+-citation_\d*$'),
    ]

    CITATION_PREFIXES = ['[', '[c', '[ci', '[cit', '[cita', '[citat',
                         '[citati', '[citatio', '[citation', '[citation_']

    def __init__(self, citation_map: Dict[str, Any], start_display_num: int = 1):
        self.citation_map = citation_map
        self.display_num = start_display_num
        self.buffer = ""
        self.id_to_display: Dict[str, int] = {}
        self.emitted_citations: list = []

    def feed(self, chunk: str) -> Generator[Dict[str, Any], None, None]:
        self.buffer += chunk

        while True:
            match = self.CITATION_PATTERN.search(self.buffer)

            if match:
                before_text = self.buffer[:match.start()]
                if before_text:
                    yield {"type": "text", "content": before_text}

                start_num = int(match.group(1))
                end_num = int(match.group(2)) if match.group(2) else None

                if end_num:
                    for num in range(start_num, end_num + 1):
                        yield from self._emit_citation_ref(f"citation_{num}")
                else:
                    yield from self._emit_citation_ref(f"citation_{start_num}")

                self.buffer = self.buffer[match.end():]
                continue

            last_bracket = self.buffer.rfind('[')

            if last_bracket != -1:
                potential = self.buffer[last_bracket:]

                if self._is_potential_citation(potential):
                    safe_part = self.buffer[:last_bracket]
                    if safe_part:
                        yield {"type": "text", "content": safe_part}
                    self.buffer = potential
                else:
                    if self.buffer:
                        yield {"type": "text", "content": self.buffer}
                    self.buffer = ""
            else:
                if self.buffer:
                    yield {"type": "text", "content": self.buffer}
                self.buffer = ""

            break

    def flush(self) -> Generator[Dict[str, Any], None, None]:
        if self.buffer:
            yield {"type": "text", "content": self.buffer}
            self.buffer = ""

    def _is_potential_citation(self, s: str) -> bool:
        if s in self.CITATION_PREFIXES:
            return True
        for pattern in self.POTENTIAL_PATTERNS:
            if pattern.match(s):
                return True
        return False

    def _emit_citation_ref(self, citation_id: str) -> Generator[Dict[str, Any], None, None]:
        metadata = self.citation_map.get(citation_id, {})

        if citation_id in self.id_to_display:
            display_num = self.id_to_display[citation_id]
        elif metadata.get('display_num') is not None:
            display_num = metadata['display_num']
            self.id_to_display[citation_id] = display_num
        else:
            display_num = self.display_num
            self.id_to_display[citation_id] = display_num
            self.display_num += 1

        citation_type = metadata.get("type", "segment")

        event: Dict[str, Any] = {
            "type": "citation_ref",
            "display_num": display_num,
            "citation_id": citation_id,
        }

        if citation_type == "image":
            event["citation_type"] = "image"
            event["file_id"] = metadata.get("file_id", "")
            event["file_name"] = metadata.get("file_name", "")
            if metadata.get("image_name"):
                event["image_name"] = metadata.get("image_name", "")
                event["image_index"] = metadata.get("image_index", 0)
                event["page"] = metadata.get("page", 0)
        elif citation_type == "web":
            event["citation_type"] = "web"
            event["title"] = metadata.get("title", "")
            event["url"] = metadata.get("url", "")
            event["snippet"] = (metadata.get("snippet", "")[:200]
                                if metadata.get("snippet") else "")
            event["source"] = metadata.get("source", "")
            event["published_date"] = metadata.get("published_date", "")
            event["favicon"] = metadata.get("favicon", "")
        else:
            event["file_name"] = metadata.get("file_name", "")
            event["segment_id"] = metadata.get("segment_id", "")
            event["summary"] = (metadata.get("summary", "")[:100]
                                if metadata.get("summary") else "")

        self.emitted_citations.append(event)
        yield event

    def get_citation_summary(self) -> Dict[str, Any]:
        unique_list = []
        seen: set = set()

        for event in self.emitted_citations:
            display_num = event["display_num"]
            if display_num not in seen:
                seen.add(display_num)
                unique_list.append({
                    "display_num": display_num,
                    "file_name": event.get("file_name", ""),
                    "segment_id": event.get("segment_id", ""),
                    "summary": event.get("summary", ""),
                })

        return {
            "total_refs": len(self.emitted_citations),
            "unique_citations": len(unique_list),
            "citation_list": unique_list,
        }