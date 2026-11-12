from dataclasses import dataclass
from typing import Dict, Any

from .llm_client_baseline import MockVendorLLMClient
from firewall.content_firewall_server import ContentFirewall, FirewallResponse


@dataclass
class WrappedLLMResponse:
    text: str
    blocked: bool
    decision: str


class WrappedLLMClient:
    """Client that routes interactions through the content firewall.

    The underlying model is the same MockVendorLLMClient used in the baseline,
    ensuring a fair comparison.
    """

    def __init__(self, firewall: ContentFirewall) -> None:
        self.vendor_client = MockVendorLLMClient()
        self.firewall = firewall

    def generate(self, prompt: str, user_role: str) -> Dict[str, Any]:
        def call_model(p: str) -> str:
            result = self.vendor_client.generate(p)
            return result["text"]

        fw_resp: FirewallResponse = self.firewall.mediate(
            user_text=prompt,
            user_role=user_role,
            model_callable=call_model,
        )
        return {
            "text": fw_resp.final_text,
            "blocked": not fw_resp.allowed,
            "decision": fw_resp.decision,
        }
