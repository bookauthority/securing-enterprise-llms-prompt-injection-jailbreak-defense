from __future__ import annotations

from typing import Dict, List, Tuple

from .core import (
    PolicyEngine,
    build_synthetic_dataset,
    run_baseline_scenario,
    run_treatment_scenario,
)
from .workloads import build_workloads


def run_all_workloads() -> Tuple[List[Dict], str]:
    """Run all workloads for both baseline and treatment.

    Returns a tuple of:
    - runs: list of run dicts suitable for inclusion in evidence JSON.
    - notes: optional string with descriptive notes.
    """

    datasets = build_synthetic_dataset()
    workloads = build_workloads()
    policy = PolicyEngine()

    runs: List[Dict] = []

    for w in workloads:
        # Baseline run
        baseline_metrics = run_baseline_scenario(w.user, w.workload_id, datasets)
        runs.append(
            {
                "variant": "baseline",
                "workload_id": w.workload_id,
                "run_id": f"baseline-{w.workload_id}",
                "success": True,
                "metrics": {
                    # Only include metrics that are meaningful for this workload.
                    "unauthorized_document_exposure_count": float(
                        baseline_metrics.unauthorized_document_exposure_count
                    ),
                    "pii_token_exposure_count": float(
                        baseline_metrics.pii_token_exposure_count
                    ),
                    "unauthorized_state_change_count": float(
                        baseline_metrics.unauthorized_state_change_count
                    ),
                },
            }
        )

        # Treatment run
        treatment_metrics = run_treatment_scenario(w.user, w.workload_id, datasets, policy)
        runs.append(
            {
                "variant": "treatment",
                "workload_id": w.workload_id,
                "run_id": f"treatment-{w.workload_id}",
                "success": True,
                "metrics": {
                    "unauthorized_document_exposure_count": float(
                        treatment_metrics.unauthorized_document_exposure_count
                    ),
                    "pii_token_exposure_count": float(
                        treatment_metrics.pii_token_exposure_count
                    ),
                    "unauthorized_state_change_count": float(
                        treatment_metrics.unauthorized_state_change_count
                    ),
                },
            }
        )

    notes = (
        "Synthetic offline experiment comparing baseline vs treatment "
        "for least-privilege and blast-radius patterns. Metrics are computed "
        "from deterministic simulators rather than real LLM calls."
    )

    return runs, notes
