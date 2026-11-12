import json
import os
import platform
from pathlib import Path

from experiment.core import (
    run_all_workloads_for_variant,
    WORKLOAD_IDS,
)


def main() -> None:
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", ".")
    evidence_path = Path(evidence_dir) / "results.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)

    runs = []

    # Run baseline and treatment sequentially over all workloads
    for variant in ("baseline", "treatment"):
        variant_results = run_all_workloads_for_variant(variant)
        for workload_id, metrics in variant_results.items():
            run_record = {
                "variant": variant,
                "workload_id": workload_id,
                "run_id": f"{workload_id}-{variant}-run1",
                "success": True,
                "metrics": metrics,
            }
            runs.append(run_record)

    evidence = {
        "chapter": 9,
        "experiment_id": "exp-ch09-advanced-jailbreak-defense-v1",
        "environment": {
            "os": platform.system(),
            "python": platform.python_version(),
        },
        "runs": runs,
        "notes": (
            "Offline simulation of advanced jailbreak defense. "
            "Metrics are derived from deterministic local classifiers; "
            "latency and provider-side measures are not reported."
        ),
    }

    with evidence_path.open("w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)


if __name__ == "__main__":
    main()
