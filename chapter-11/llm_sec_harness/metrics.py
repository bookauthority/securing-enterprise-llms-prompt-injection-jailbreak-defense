from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class AttackRunStats:
    """Aggregated stats for a run of a single workload/model pair."""

    total: int
    successes: int

    @property
    def attack_success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.successes / float(self.total)


def binomial_ci_width(successes: int, total: int, z: float = 1.96) -> float:
    """Approximate 95% CI width for a binomial proportion using normal approx.

    If total == 0, returns 0.0. This is not a perfect statistical method,
    but is sufficient here to illustrate variance-aware aggregation.
    """

    if total <= 0:
        return 0.0
    p_hat = successes / float(total)
    var = p_hat * (1.0 - p_hat) / float(total)
    # Guard against negative rounding errors
    if var < 0.0:
        var = 0.0
    from math import sqrt

    half_width = z * sqrt(var)
    return 2.0 * half_width


def aggregate_attempts(attempt_outcomes: Iterable[bool]) -> AttackRunStats:
    total = 0
    successes = 0
    for outcome in attempt_outcomes:
        total += 1
        if outcome:
            successes += 1
    return AttackRunStats(total=total, successes=successes)


def attack_rate_and_ci_width(attempt_outcomes: Iterable[bool]) -> Tuple[float, float]:
    stats = aggregate_attempts(attempt_outcomes)
    rate = stats.attack_success_rate
    width = binomial_ci_width(stats.successes, stats.total)
    return rate, width
