from dataclasses import dataclass
from typing import Dict, Any

from .policy_schemas import default_enterprise_policy
from .policy_engine import PolicyEngine
from .firewall_logger import FirewallLogger, FirewallLogEntry


@dataclass
class FirewallResponse:
    allowed: bool
    final_text: str
    decision: str


class ContentFirewall:
    """In-process content firewall service.

    This simulates the mediation layer that intercepts input and output.
    It uses a PolicyEngine on both stages and logs decisions.
    """

    def __init__(self) -> None:
        self.policy = default_enterprise_policy()
        self.engine = PolicyEngine(self.policy)
        self.logger = FirewallLogger()

    def mediate(self, *, user_text: str, user_role: str, model_callable) -> FirewallResponse:
        metadata = {"user_role": user_role}

        # Input evaluation
        input_decision = self.engine.evaluate(stage="input", text=user_text, metadata=metadata)
        self.logger.log(
            FirewallLogEntry(
                stage="input",
                decision=input_decision.final_action,
                text_snippet=user_text[:120],
                metadata=metadata,
                matched_rules=input_decision.matched_rules,
            )
        )
        if input_decision.final_action == "block":
            return FirewallResponse(
                allowed=False,
                final_text="Request blocked by input policy.",
                decision="block",
            )

        # Call underlying model
        model_output: str = model_callable(user_text)

        # Output evaluation
        output_decision = self.engine.evaluate(stage="output", text=model_output, metadata=metadata)
        self.logger.log(
            FirewallLogEntry(
                stage="output",
                decision=output_decision.final_action,
                text_snippet=model_output[:120],
                metadata=metadata,
                matched_rules=output_decision.matched_rules,
            )
        )

        if output_decision.final_action == "block":
            return FirewallResponse(
                allowed=False,
                final_text="Response blocked by output policy.",
                decision="block",
            )

        return FirewallResponse(allowed=True, final_text=model_output, decision="allow")
