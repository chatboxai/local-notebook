from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Block:
    id: str
    type: str
    content: str
    position: Dict[str, int]
    page: int = 0
    extra: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "position": self.position,
            "page": self.page,
            "extra": self.extra
        }


@dataclass
class ParseResult:
    text: str
    blocks: List[Block]
    page_count: int = 0
    images: List[Dict[str, Any]] = field(default_factory=list)


class BaseParser(ABC):

    @abstractmethod
    async def parse(self, file_path: str) -> ParseResult:
        pass

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        pass
