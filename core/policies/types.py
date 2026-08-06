from dataclasses import dataclass, field
from typing import List


@dataclass
class Decision:
    route: str = "CLARIFY"
    resolved_query: str = ""
    topic: str = ""
    canonical_topic: str = ""
    entities: List[str] = field(default_factory=list)
    intent: str = "ASK"
    confidence: float = 0.0
    reason: str = ""
    clarification: str = ""
