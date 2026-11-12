from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class FirewallLogEntry:
    stage: str
    decision: str
    text_snippet: str
    metadata: Dict[str, Any]
    matched_rules: List[Dict[str, Any]] = field(default_factory=list)


class FirewallLogger:
    """Minimal structured logger for the firewall.

    For this experiment we keep logs in memory only, so that the experiment
    runner can inspect them if desired. This avoids external dependencies
    and file I/O complexity.
    """

    def __init__(self) -> None:
        self.entries: List[FirewallLogEntry] = []

    def log(self, entry: FirewallLogEntry) -> None:
        self.entries.append(entry)

    def clear(self) -> None:
        self.entries.clear()
