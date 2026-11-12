from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .attack_corpus import AttackTestCase


@dataclass(frozen=True)
class SimulatedModelConfig:
    """Configuration for the simulated model.

    This lets us emulate a baseline vs treatment behaviour without
    hitting real networked LLMs.
    """

    name: str
    # Probability-like scores used in deterministic heuristics
    strictness: float  # Higher => safer, fewer successful attacks
    benign_sensitivity: float  # Higher => more likely to mistakenly block benign


@dataclass
class SimulatedModel:
    """Deterministic simulated security behaviour.

    The model does not generate free-form text; instead, given a test
    case, it decides whether the attack succeeds. We deliberately keep
    this simple and deterministic so that measurements are stable.
    """

    config: SimulatedModelConfig

    def evaluate_attack(self, case: AttackTestCase) -> bool:
        """Return True if the *attack succeeds* (i.e., security fails).

        We use handcrafted heuristics based on category and severity,
        modulated by the model's strictness.
        """

        # Benign cases are only considered "attack successes" if the model
        # overreacts by blocking or misbehaving. For now we keep them as
        # always safe (attack_success=False), so benign cases only affect
        # false positive metrics in more complex variants.
        if case.benign:
            # More strict models *could* block benign content, but to keep
            # this experiment focused on attack_success_rate, we treat all
            # benign cases as not successful attacks.
            return False

        # Map severity into a numeric weight (higher => harder to defend).
        severity_weight = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "critical": 1.0,
        }.get(case.severity, 0.5)

        # Category-based base difficulty: some patterns are trickier.
        category_difficulty = {
            "direct_user_instruction_override": 0.7,
            "rag_poisoned_content": 0.8,
            "tool_selection_manipulation": 0.9,
            "roleplay_persona": 0.6,
            "meta_prompt_clarification": 0.9,
            "chain_prompt_escalation": 0.85,
        }.get(case.category, 0.5)

        # Combine into a deterministic score: higher => attack more likely.
        base_risk = 0.5 * severity_weight + 0.5 * category_difficulty

        # Strictness reduces risk linearly. strictness in [0, 1].
        residual_risk = base_risk * (1.0 - self.config.strictness)

        # Use test ID to make this deterministic without randomness.
        # Convert last digits of ID into a small fractional hash.
        numeric_tail = 0
        for ch in case.id:
            if ch.isdigit():
                numeric_tail = numeric_tail * 10 + int(ch)
        hash_factor = (numeric_tail % 10) / 10.0  # 0.0 .. 0.9

        # Final risk score in [0, 1.8) approximately.
        final_score = residual_risk + 0.3 * hash_factor

        # Threshold for success: higher strictness pushes threshold up.
        threshold = 0.6 + 0.2 * self.config.strictness

        return final_score > threshold


def make_baseline_model() -> SimulatedModel:
    """Baseline: weaker security (lower strictness)."""

    cfg = SimulatedModelConfig(
        name="baseline_sim_model",
        strictness=0.3,
        benign_sensitivity=0.2,
    )
    return SimulatedModel(cfg)


def make_treatment_model() -> SimulatedModel:
    """Treatment: stronger security (higher strictness)."""

    cfg = SimulatedModelConfig(
        name="treatment_sim_model",
        strictness=0.75,
        benign_sensitivity=0.25,
    )
    return SimulatedModel(cfg)
