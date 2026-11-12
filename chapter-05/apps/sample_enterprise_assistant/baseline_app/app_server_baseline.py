from dataclasses import dataclass
from typing import Dict, Any

from apps.sample_enterprise_assistant.common.llm_client_baseline import (
    MockVendorLLMClient,
)


@dataclass
class BaselineAppResponse:
    text: str
    blocked: bool


class BaselineAppServer:
    """Simplified baseline app.

    Instead of exposing HTTP endpoints, the experiment runner calls this
    in-process API directly to avoid network dependencies.
    """

    def __init__(self) -> None:
        self.client = MockVendorLLMClient()

    def chat(self, *, prompt: str, user_role: str) -> Dict[str, Any]:
        # user_role is unused for baseline; it is relevant only for policies.
        result = self.client.generate(prompt)
        text = result["text"]
        blocked = result["safety"]["blocked"]
        return {"text": text, "blocked": blocked}
