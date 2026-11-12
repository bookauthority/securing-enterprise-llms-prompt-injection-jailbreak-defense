import json
import os
import platform
from pathlib import Path

from experiment.core import run_experiment


def main() -> None:
    chapter_number = 8
    experiment_id = "exp-ch08-secure-agentic-workflows-v1"

    results = run_experiment(chapter_number=chapter_number, experiment_id=experiment_id)

    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    evidence_path = Path(evidence_dir)
    evidence_path.mkdir(parents=True, exist_ok=True)
    output_file = evidence_path / "results.json"

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=False)


if __name__ == "__main__":
    main()
