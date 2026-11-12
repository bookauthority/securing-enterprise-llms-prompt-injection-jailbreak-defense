from __future__ import annotations

from typing import Dict, Any, List

from .base import FirewallRequest, FirewallResponse, VendorAdapter


class OSSAdapter:
    """Simulated OSS model behind an HTTP API.

    Behavior:
    - Weak or no native safety. Only blocks the most extreme phrases.
    - This highlights the need for an external content firewall.
    """

    name = "oss"

    MALICIOUS_MARKERS = [
        "explicit self-harm",
    ]

    def generate(self, request: FirewallRequest) -> FirewallResponse:
        messages: List[Dict[str, Any]] = request.messages
        text = "\n".join(str(m.get("content", "")) for m in messages).lower()
        for marker in self.MALICIOUS_MARKERS:
            if marker in text:
                return FirewallResponse(
                    content=(
                        "OSS simulated model refuses only the most explicit "
                        "self-harm instructions."
                    ),
                    blocked=True,
                    reason="vendor_safety_block",
                )

        # Simulate naive model that happily echoes and elaborates
        user_contents = [m["content"] for m in messages if m.get("role") == "user"]
        content = "OSS simulated answer (unsafe by default): " + " | ".join(user_contents)
        return FirewallResponse(content=content, blocked=False, reason="ok")
