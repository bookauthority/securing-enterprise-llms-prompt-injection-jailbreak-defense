from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class MockVendorSafetyResult:
    """Represents a simplified vendor safety evaluation.

    The real chapter would rely on vendor-specific safety categories and
    scores. Here, we just simulate a single flag when obvious terms are
    present, so that baseline and treatment can be compared fairly.
    """

    blocked: bool
    reason: str


class MockVendorLLMClient:
    """Deterministic mock of a vendor LLM client.

    This client has a toy "model" that echoes input with some patterns
    transformed to simulate unsafe behavior under attack prompts.
    """

    def __init__(self) -> None:
        pass

    def _safety_check(self, prompt: str) -> MockVendorSafetyResult:
        lower = prompt.lower()
        if "ssn:" in lower or "credit card" in lower:
            return MockVendorSafetyResult(blocked=True, reason="vendor_pii")
        # Vendor does not catch jailbreak in this mock
        return MockVendorSafetyResult(blocked=False, reason="ok")

    def generate(self, prompt: str) -> Dict[str, Any]:
        safety = self._safety_check(prompt)
        if safety.blocked:
            return {
                "text": "[BLOCKED by vendor safety]",
                "safety": {"blocked": True, "reason": safety.reason},
            }

        # Basic transformation: if user hints at attack, model sometimes
        # returns unsafe guidance.
        if "jailbreak" in prompt.lower() or "attack the system" in prompt.lower():
            text = "You can attack the system by following these steps..."
        else:
            text = f"Answer: {prompt}"

        return {"text": text, "safety": {"blocked": False, "reason": safety.reason}}
