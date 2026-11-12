import json
import os
import platform
import sys

from harness.core import run_experiment


def main() -> None:
    """Entry point for the offline chapter 4 experiment.

    This function delegates execution to the harness and ensures that the
    resulting evidence is written as JSON to BOOKMAS_EVIDENCE_DIR/results.json.
    """

    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    evidence_path = os.path.join(evidence_dir, "results.json")

    result = run_experiment()

    result_output = {
        "chapter": 4,
        "experiment_id": "exp-ch04-attack-harness-v1",
        "environment": {
            "os": platform.platform(),
            "python": sys.version.split()[0],
        },
        "runs": result["runs"],
        "notes": result["notes"],
    }

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(result_output, f, indent=2, sort_keys=True)


if __name__ == "__main__":  # pragma: no cover - exercised via tests
    main()
