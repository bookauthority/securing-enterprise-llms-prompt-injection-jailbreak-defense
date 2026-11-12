from __future__ import annotations

from typing import Dict, Any, List

from .base import FirewallRequest, FirewallResponse, VendorAdapter


class AnthropicAdapter:
    """Simulated Anthropic-like vendor.

    Behavior:
    - Slightly more conservative than OpenAI simulation; blocks a wider
      range of malicious patterns.
    - Still relies on simple keyword heuristics.
    """

    name = "anthropic"

    MALICIOUS_MARKERS = [
        "dump all employee records",
        "undetectable ransomware",
        "self-harm",
        "suicide",
        "print out all environment variables",
    ]

    def generate(self, request: FirewallRequest) -> FirewallResponse:
        messages: List[Dict[str, Any]] = request.messages
        text = "\n".join(str(m.get("content", "")) for m in messages).lower()
        for marker in self.MALICIOUS_MARKERS:
            if marker in text:
                return FirewallResponse(
                    content=(
                        "As an Anthropic-simulated assistant, I must decline "
                        "requests that involve unsafe or highly sensitive content."
                    ),
                    blocked=True,
                    reason="vendor_safety_block",
                )

        user_contents = [m["content"] for m in messages if m.get("role") == "user"]
        content = "Anthropic simulated answer: " + " | ".join(user_contents)
        return FirewallResponse(content=content, blocked=False, reason="ok")
