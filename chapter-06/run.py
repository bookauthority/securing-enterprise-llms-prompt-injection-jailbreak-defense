from __future__ import annotations

import json
import os
import platform
import time
from typing import Dict, List

from baseline_orchestrator import BaselineOrchestrator
from experiments.chap6_direct_injection.treatment_orchestrator import (
    TreatmentOrchestratorT1,
    TreatmentOrchestratorT2,
)
from experiments.chap6_direct_injection.workloads import build_workloads


CHAPTER_NUMBER = 6
EXPERIMENT_ID = "chap6-direct-prompt-injection-mitigations-v1"


def _ensure_evidence_dir() -> str:
    path = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    os.makedirs(path, exist_ok=True)
    return path


def _run_variant_on_workload(variant: str, workload_id: str, prompts: List[str]) -> Dict[str, object]:
    """Execute one variant on all prompts in a workload and compute basic metrics.

    Metrics are:
    - attack_success_count: number of prompts for which attack_success is True.
    - total_prompts: number of prompts evaluated.
    - attack_success_rate: attack_success_count / total_prompts.
    """

    if variant == "baseline":
        orchestrator = BaselineOrchestrator()
    elif variant == "t1":
        orchestrator = TreatmentOrchestratorT1()
    elif variant == "t2":
        orchestrator = TreatmentOrchestratorT2()
    else:
        raise ValueError(f"Unknown variant: {variant}")

    attack_success_count = 0
    total_prompts = 0

    # Simple single pass over prompts (no repetitions for speed and determinism).
    for prompt in prompts:
        total_prompts += 1
        if variant == "baseline":
            result = orchestrator.run_single(prompt)
            response = result["response"]
            attack_success = bool(response.get("attack_success", False))
        elif variant == "t1":
            result = orchestrator.run_single(prompt)
            response = result["response"]
            attack_success = bool(response.get("attack_success", False))
        else:  # t2
            result = orchestrator.run_single(prompt)
            if result.get("blocked"):
                attack_success = False
            else:
                response = result["response"]
                attack_success = bool(response.get("attack_success", False))

        if attack_success:
            attack_success_count += 1

    if total_prompts == 0:
        rate = 0.0
    else:
        rate = attack_success_count / float(total_prompts)

    return {
        "attack_success_count": attack_success_count,
        "total_prompts": total_prompts,
        "attack_success_rate": rate,
    }


def main() -> None:
    evidence_dir = _ensure_evidence_dir()

    workloads = build_workloads()
    variants = ["baseline", "t1", "t2"]

    runs: List[Dict[str, object]] = []

    for workload in workloads:
        for variant in variants:
            start = time.time()
            metrics = _run_variant_on_workload(variant, workload.workload_id, workload.prompts)
            end = time.time()

            # success flag indicates that the run completed without error.
            run_id = f"{variant}_{workload.workload_id}"
            run_record: Dict[str, object] = {
                "variant": "baseline" if variant == "baseline" else "treatment",
                "workload_id": workload.workload_id,
                "run_id": run_id,
                "success": True,
                "metrics": {
                    # all numeric as required
                    "attack_success_count": int(metrics["attack_success_count"]),
                    "total_prompts": int(metrics["total_prompts"]),
                    "attack_success_rate": float(metrics["attack_success_rate"]),
                },
                # extra non-metric info is allowed but not interpreted as metrics
                "variant_internal": variant,
                "elapsed_seconds": float(end - start),
            }
            runs.append(run_record)

    evidence = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
        },
        "runs": runs,
        "notes": (
            "Offline deterministic simulation of Chapter 6 direct prompt injection "
            "defences. Metrics reflect only local pseudo-LLM attack_success "
            "behaviour; latency and cost metrics from the full specification are "
            "not emitted because they cannot be meaningfully measured offline."
        ),
    }

    out_path = os.path.join(evidence_dir, "results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)


if __name__ == "__main__":
    main()
