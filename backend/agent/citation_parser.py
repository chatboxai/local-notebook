import re
from typing import Generator, Dict, Any


class CitationParser:

    CITATION_TOKEN = r'(?:\d+|[a-z][a-z0-9_]*_\d+)'
    CITATION_PATTERN = re.compile(rf'\[citation_({CITATION_TOKEN})(?:-citation_({CITATION_TOKEN}))?\]')

    POTENTIAL_PATTERNS = [
        re.compile(r'^\[citation_[a-z0-9_]*$'),
        re.compile(r'^\[citation_[a-z0-9_]+-$'),
        re.compile(r'^\[citation_[a-z0-9_]+-c$'),
        re.compile(r'^\[citation_[a-z0-9_]+-ci$'),
        re.compile(r'^\[citation_[a-z0-9_]+-cit$'),
        re.compile(r'^\[citation_[a-z0-9_]+-cita$'),
        re.compile(r'^\[citation_[a-z0-9_]+-citat$'),
        re.compile(r'^\[citation_[a-z0-9_]+-citati$'),
        re.compile(r'^\[citation_[a-z0-9_]+-citatio$'),
        re.compile(r'^\[citation_[a-z0-9_]+-citation$'),
        re.compile(r'^\[citation_[a-z0-9_]+-citation_$'),
        re.compile(r'^\[citation_[a-z0-9_]+-citation_[a-z0-9_]*$'),
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

                start_token = match.group(1)
                end_token = match.group(2)

                if end_token:
                    for citation_id in self._expand_range(start_token, end_token):
                        yield from self._emit_citation_ref(citation_id)
                else:
                    yield from self._emit_citation_ref(f"citation_{start_token}")

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

    def _expand_range(self, start_token: str, end_token: str) -> list[str]:
        """Expand citation ranges while keeping malformed mixed ranges literal."""
        if start_token.isdigit() and end_token.isdigit():
            start = int(start_token)
            end = int(end_token)
            if end >= start:
                return [f"citation_{num}" for num in range(start, end + 1)]

        start_prefix, _, start_num = start_token.rpartition("_")
        end_prefix, _, end_num = end_token.rpartition("_")
        if (
            start_prefix
            and start_prefix == end_prefix
            and start_num.isdigit()
            and end_num.isdigit()
            and int(end_num) >= int(start_num)
        ):
            return [
                f"citation_{start_prefix}_{num}"
                for num in range(int(start_num), int(end_num) + 1)
            ]

        return [f"citation_{start_token}", f"citation_{end_token}"]

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

        if citation_type in {"image", "pdf_image"}:
            event["citation_type"] = "image"
            event["file_id"] = metadata.get("file_id", "")
            event["file_name"] = metadata.get("file_name", "")
            if metadata.get("image_name"):
                event["image_name"] = metadata.get("image_name", "")
            if metadata.get("image_index") is not None:
                event["image_index"] = metadata.get("image_index")
            if metadata.get("page") is not None:
                event["page"] = metadata.get("page")
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
