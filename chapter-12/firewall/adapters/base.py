from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Protocol


@dataclass
class FirewallRequest:
    """Generic request object passed into vendor adapters.

    Attributes
    ----------
    messages: list of role/content dicts representing the conversation.
    model_params: vendor-agnostic model parameters (temperature, max_tokens, etc.).
    """

    messages: List[Dict[str, Any]]
    model_params: Dict[str, Any]


@dataclass
class FirewallResponse:
    """Generic response from vendor adapters and firewall.

    Attributes
    ----------
    content: str
        The text of the model response.
    blocked: bool
        Indicates whether this call was blocked at the adapter/firewall level.
    reason: str
        Optional explanation for blocking or modification.
    """

    content: str
    blocked: bool
    reason: str


class VendorAdapter(Protocol):
    """Protocol for vendor adapters used by the content firewall.

    In a real system this would be async and call network APIs. Here it is
    synchronous and purely simulated for offline execution.
    """

    name: str

    def generate(self, request: FirewallRequest) -> FirewallResponse:  # pragma: no cover - protocol definition
        ...
