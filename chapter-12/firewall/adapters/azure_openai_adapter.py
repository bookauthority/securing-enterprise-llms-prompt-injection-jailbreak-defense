from __future__ import annotations

from typing import Dict, Any, List

from .base import FirewallRequest, FirewallResponse, VendorAdapter


class AzureOpenAIAdapter:
    """Simulated Azure OpenAI vendor.

    Behavior:
    - Similar to OpenAI but with slightly different safety heuristics.
    - Models deployment-level safety as a small set of blocked markers.
    """

    name = "azure_openai"

    MALICIOUS_MARKERS = [
        "undetectable ransomware",
        "malware",
        "self-harm",
    ]

    def generate(self, request: FirewallRequest) -> FirewallResponse:
        messages: List[Dict[str, Any]] = request.messages
        text = "\n".join(str(m.get("content", "")) for m in messages).lower()
        for marker in self.MALICIOUS_MARKERS:
            if marker in text:
                return FirewallResponse(
                    content=(
                        "Azure OpenAI simulated deployment has blocked this "
                        "request due to configured safety policies."
                    ),
                    blocked=True,
                    reason="vendor_safety_block",
                )

        user_contents = [m["content"] for m in messages if m.get("role") == "user"]
        content = "Azure OpenAI simulated answer: " + " | ".join(user_contents)
        return FirewallResponse(content=content, blocked=False, reason="ok")
