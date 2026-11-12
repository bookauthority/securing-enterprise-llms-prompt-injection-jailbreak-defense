from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from .policy_schemas import Policy, PolicyRule, Stage, evaluate_condition


@dataclass
class PolicyDecision:
    stage: Stage
    final_action: str
    matched_rules: List[Dict[str, Any]]


class PolicyEngine:
    """Simple, deterministic policy engine.

    This engine evaluates all rules for a given stage and returns the
    strongest action (block > redact > require_approval > allow/log_only).
    """

    def __init__(self, policy: Policy):
        self.policy = policy

    def evaluate(self, *, stage: Stage, text: str, metadata: Dict[str, Any]) -> PolicyDecision:
        matched: List[Dict[str, Any]] = []
        # Default action is allow
        final_action = "allow"

        for rule in self.policy.rules:
            if rule.stage != stage:
                continue
            if evaluate_condition(rule.condition, text, metadata):
                matched.append(
                    {
                        "rule_id": rule.id,
                        "rule_description": rule.description,
                        "severity": rule.severity,
                        "action": rule.action,
                    }
                )
                # Simplified precedence: block dominates everything
                if rule.action == "block":
                    final_action = "block"
                elif final_action != "block" and rule.action in {"redact_fields", "redact_patterns"}:
                    final_action = rule.action
                elif final_action in {"allow", "log_only"} and rule.action == "require_approval":
                    final_action = "require_approval"

        return PolicyDecision(stage=stage, final_action=final_action, matched_rules=matched)
