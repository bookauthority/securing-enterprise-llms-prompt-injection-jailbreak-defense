import json
import os
import platform
import sys
from pathlib import Path

from experiment.simulation import (
    WORKLOAD_IDS,
    run_experiment_for_workload,
)


CHAPTER_NUMBER = 13
EXPERIMENT_ID = "ch13-endtoend-casestudies-v1"


def get_environment_metadata() -> dict:
    return {
        "os": platform.platform(),
        "python": sys.version.replace("\n", " "),
    }


def main() -> None:
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    evidence_path = Path(evidence_dir) / "results.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)

    runs = []
    notes_parts = []

    for workload_id in WORKLOAD_IDS:
        for variant in ("baseline", "treatment"):
            result = run_experiment_for_workload(workload_id=workload_id, variant=variant)
            runs.append(
                {
                    "variant": variant,
                    "workload_id": workload_id,
                    "run_id": result["run_id"],
                    "success": bool(result["success"]),
                    "metrics": result["metrics"],
                }
            )
            notes_parts.append(
                f"Executed {workload_id} variant={variant} with {result['request_count']} simulated requests."
            )

    evidence = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": get_environment_metadata(),
        "runs": runs,
        "notes": (
            "Offline, rule-based simulation of Chapter 13 end-to-end case studies. "
            "No real LLMs, tools, or external services were invoked. "
            + " ".join(notes_parts)
        ),
    }

    with evidence_path.open("w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)


if __name__ == "__main__":  # pragma: no cover
    main()
