import json
import os
import sys
import uuid
import platform
from typing import Dict, Any, List

from experiments.ch5_firewall_baseline.experiment_runner import (
    run_all_workloads,
    WORKLOAD_IDS,
)


def main() -> None:
    # Determine evidence directory
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    results_path = os.path.join(evidence_dir, "results.json")

    # Run experiment for both variants and collect metrics
    runs: List[Dict[str, Any]] = []

    for variant in ("baseline", "treatment"):
        variant_results = run_all_workloads(variant)
        for workload_id, summary in variant_results.items():
            run_entry = {
                "variant": variant,
                "workload_id": workload_id,
                "run_id": str(uuid.uuid4()),
                "success": True,
                "metrics": {
                    # Only numeric metrics here
                    "mean_latency_ms": float(summary["mean_latency_ms"]),
                    "blocked_fraction": float(summary["blocked_fraction"]),
                    "total_requests": float(summary["total_requests"]),
                },
            }
            runs.append(run_entry)

    # Sanity: ensure at least one baseline and treatment per workload
    variants_present = {(r["workload_id"], r["variant"]) for r in runs}
    for wid in WORKLOAD_IDS:
        assert (wid, "baseline") in variants_present, f"Missing baseline for {wid}"
        assert (wid, "treatment") in variants_present, f"Missing treatment for {wid}"

    evidence: Dict[str, Any] = {
        "chapter": 5,
        "experiment_id": "exp-ch5-content-firewall-baseline-v1",
        "environment": {
            "os": platform.platform(),
            "python": sys.version.split()[0],
        },
        "runs": runs,
        "notes": (
            "Offline simulated experiment with mock LLM and reduced workloads. "
            "Metrics are relative and deterministic within this environment."
        ),
    }

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)


if __name__ == "__main__":
    main()
