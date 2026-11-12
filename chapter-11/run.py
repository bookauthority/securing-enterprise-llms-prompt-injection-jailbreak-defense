import json
import os
import sys
import platform
from typing import Any, Dict, List

from llm_sec_harness.runner import run_all_workloads


CHAPTER_NUMBER = 11
EXPERIMENT_ID = "exp-llm-sec-011-ci-benchmarks-v1"


def get_evidence_dir() -> str:
    env_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR")
    if env_dir:
        return env_dir
    # Default per instructions
    return "/evidence"


def main() -> None:
    # Run experiment workloads for baseline and treatment
    results: List[Dict[str, Any]] = run_all_workloads()

    evidence = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": {
            "os": platform.platform(),
            "python": sys.version.split()[0],
        },
        "runs": results,
        "notes": (
            "Offline simulated CI-style LLM security harness. "
            "Metrics are derived from deterministic simulated model behaviour "
            "over synthetic prompt-injection and jailbreak workloads."
        ),
    }

    evidence_dir = get_evidence_dir()
    os.makedirs(evidence_dir, exist_ok=True)
    out_path = os.path.join(evidence_dir, "results.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":  # pragma: no cover
    main()
