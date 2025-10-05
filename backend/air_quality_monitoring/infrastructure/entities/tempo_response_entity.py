from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class TempoResponseEntity:
    source: str
    results: List[List[Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "results": self.results}