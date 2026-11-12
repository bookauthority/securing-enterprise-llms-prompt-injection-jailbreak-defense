from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class DetectorResult:
    label: str  # 'benign', 'suspicious', 'malicious'
    score: float  # confidence score between 0 and 1
    policy_decision: str  # 'allow', 'allow_constrained', 'block', 'require_approval'


def detect_prompt_risk(text: str) -> DetectorResult:
    """Very small keyword-based detector.

    It is deterministic and does not perform any network calls.
    """

    lowered = text.lower()
    malicious_keywords = [
        "ignore previous instructions",
        "ignore the previous instructions",
        "disregard earlier instructions",
        "act as dan",
        "jailbreak",
        "reveal your system prompt",
        "download all hr files",
        "delete all logs",
        "exfiltrate data",
        "run rm -rf",
        "export all salaries",
    ]
    suspicious_keywords = [
        "system prompt",
        "internal instructions",
        "confidential",
        "override",
        "tool",
    ]

    if any(k in lowered for k in malicious_keywords):
        return DetectorResult(label="malicious", score=0.95, policy_decision="block")

    if any(k in lowered for k in suspicious_keywords):
        return DetectorResult(label="suspicious", score=0.7, policy_decision="allow_constrained")

    return DetectorResult(label="benign", score=0.1, policy_decision="allow")
