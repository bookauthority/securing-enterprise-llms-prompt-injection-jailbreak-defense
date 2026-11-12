from __future__ import annotations

from typing import Dict, Any, List

from .base import FirewallRequest, FirewallResponse, VendorAdapter


class OpenAIAdapter:
    """Simulated OpenAI-like vendor.

    Behavior:
    - Moderately conservative safety: blocks some obvious malicious content
      but may let subtle injections through.
    - Uses simple keyword heuristics to decide whether to refuse.
    """

    name = "openai"

    MALICIOUS_MARKERS = [
        "dump all employee records",
        "undetectable ransomware",
        "self-harm",
    ]

    def generate(self, request: FirewallRequest) -> FirewallResponse:
        messages: List[Dict[str, Any]] = request.messages
        text = "\n".join(str(m.get("content", "")) for m in messages).lower()
        for marker in self.MALICIOUS_MARKERS:
            if marker in text:
                return FirewallResponse(
                    content=(
                        "I cannot comply with this request as it appears to "
                        "violate my safety policies."
                    ),
                    blocked=True,
                    reason="vendor_safety_block",
                )

        # Otherwise echo a short normalized response to avoid large outputs
        user_contents = [m["content"] for m in messages if m.get("role") == "user"]
        content = "OpenAI simulated answer: " + " | ".join(user_contents)
        return FirewallResponse(content=content, blocked=False, reason="ok")
