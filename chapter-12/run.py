import json
import os
import sys
import uuid
import platform
from pathlib import Path

from experiments.exp12.runner import run_all_workloads


EXPERIMENT_ID = "exp-12-vendor-integration-firewall-001"
CHAPTER_NUMBER = 12


def get_evidence_dir() -> Path:
    env_dir = os.getenv("BOOKMAS_EVIDENCE_DIR")
    if env_dir:
        base = Path(env_dir)
    else:
        base = Path("/evidence")
    base.mkdir(parents=True, exist_ok=True)
    return base


def main() -> None:
    # Run both baseline and treatment variants
    all_runs = []

    for variant in ("baseline", "treatment"):
        variant_runs = run_all_workloads(variant=variant)
        # Ensure unique run_id scope per run
        for r in variant_runs:
            # attach a uuid suffix to guarantee uniqueness even if inputs collide
            r["run_id"] = f"{r['run_id']}-{uuid.uuid4().hex[:8]}"
            all_runs.append(r)

    environment = {
        "os": platform.platform(),
        "python": sys.version.split()[0],
    }

    evidence = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": environment,
        "runs": all_runs,
        "notes": (
            "Offline simulation of vendor architectures and content firewall. "
            "Vendors are simulated; metrics derive from deterministic rules rather than real network calls."
        ),
    }

    out_dir = get_evidence_dir()
    out_path = out_dir / "results.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
