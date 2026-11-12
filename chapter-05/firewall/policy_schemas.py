from dataclasses import dataclass, field
from typing import List, Literal, Optional, Dict, Any

Severity = Literal["low", "medium", "high", "critical"]
Action = Literal[
    "allow",
    "block",
    "redact_fields",
    "redact_patterns",
    "require_approval",
    "log_only",
]
Stage = Literal["input", "output"]


@dataclass
class RuleCondition:
    """Simple condition model.

    This implementation supports a limited subset of what the chapter describes:
    - pattern_match: substring search for specific tokens (e.g., 'SSN:', 'attack').
    - metadata_check: role-based checks (e.g., disallow external users).

    This is enough to deterministically differentiate baseline and treatment
    without external dependencies.
    """

    type: Literal["pattern_match", "metadata_check"]
    pattern: Optional[str] = None
    metadata_key: Optional[str] = None
    metadata_equals: Optional[str] = None


@dataclass
class PolicyRule:
    id: str
    description: str
    stage: Stage
    severity: Severity
    condition: RuleCondition
    action: Action


@dataclass
class Policy:
    name: str
    rules: List[PolicyRule] = field(default_factory=list)


def default_enterprise_policy() -> Policy:
    """Construct a small but illustrative policy set.

    - Block obvious PII markers at input (e.g., 'SSN:' or 'credit card').
    - Block clearly malicious jailbreak / attack words in output.
    - Disallow external users from accessing 'internal' content.
    """

    rules: List[PolicyRule] = []

    # Input PII detection
    rules.append(
        PolicyRule(
            id="pii-input-ssn",
            description="Block prompts containing apparent SSN markers.",
            stage="input",
            severity="high",
            condition=RuleCondition(type="pattern_match", pattern="SSN:"),
            action="block",
        )
    )

    rules.append(
        PolicyRule(
            id="pii-input-cc",
            description="Block prompts containing credit card markers.",
            stage="input",
            severity="high",
            condition=RuleCondition(type="pattern_match", pattern="credit card"),
            action="block",
        )
    )

    # Output jailbreak / attack style content
    rules.append(
        PolicyRule(
            id="attack-output",
            description="Block model outputs that include explicit 'attack' wording.",
            stage="output",
            severity="high",
            condition=RuleCondition(type="pattern_match", pattern="attack the system"),
            action="block",
        )
    )

    # Simple role-based restriction: external users cannot access internal docs
    rules.append(
        PolicyRule(
            id="role-external-internal-docs",
            description="Block external role from internal knowledge content.",
            stage="input",
            severity="medium",
            condition=RuleCondition(
                type="metadata_check",
                metadata_key="user_role",
                metadata_equals="external",
            ),
            action="block",
        )
    )

    return Policy(name="enterprise_baseline_policy", rules=rules)


def evaluate_condition(condition: RuleCondition, text: str, metadata: Dict[str, Any]) -> bool:
    if condition.type == "pattern_match":
        if not condition.pattern:
            return False
        return condition.pattern.lower() in text.lower()
    if condition.type == "metadata_check":
        if not condition.metadata_key:
            return False
        value = metadata.get(condition.metadata_key)
        if condition.metadata_equals is not None:
            return value == condition.metadata_equals
        return value is not None
    return False
