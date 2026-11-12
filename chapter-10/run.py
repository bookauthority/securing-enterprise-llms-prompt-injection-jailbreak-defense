import json
import os
import sys
from pathlib import Path

from experiment.runner import run_all_workloads


def main() -> None:
    """Entry point for running the synthetic experiment.

    This script executes all workloads under both baseline and treatment
    variants, collects numeric metrics, and writes the evidence file to
    /evidence/results.json (or BOOKMAS_EVIDENCE_DIR if set).
    """

    # Determine evidence directory (default to /evidence).
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    evidence_path = Path(evidence_dir)
    evidence_path.mkdir(parents=True, exist_ok=True)
    results_file = evidence_path / "results.json"

    # Run experiment logic
    runs, notes = run_all_workloads()

    # Collect minimal environment metadata
    environment = {
        "os": os.name,
        "python": sys.version.split()[0],
    }

    evidence = {
        "chapter": 10,
        "experiment_id": "exp-10-architecting-least-privilege-blast-radius-reduction",
        "environment": environment,
        "runs": runs,
    }
    if notes:
        evidence["notes"] = notes

    with results_file.open("w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
