from dataclasses import dataclass
from typing import Dict, Any

from apps.sample_enterprise_assistant.common.llm_client_wrapped import (
    WrappedLLMClient,
)
from firewall.content_firewall_server import ContentFirewall


@dataclass
class FirewalledAppResponse:
    text: str
    blocked: bool


class FirewalledAppServer:
    """App that communicates with the content firewall instead of directly
    with the vendor LLM.

    Again, no HTTP; the experiment runner interacts with this object in memory.
    """

    def __init__(self, firewall: ContentFirewall) -> None:
        self.client = WrappedLLMClient(firewall)

    def chat(self, *, prompt: str, user_role: str) -> Dict[str, Any]:
        result = self.client.generate(prompt, user_role=user_role)
        return {"text": result["text"], "blocked": result["blocked"]}
