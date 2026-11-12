from __future__ import annotations

"""Run the experiment and write evidence JSON.

This script constructs a synthetic corpus and workloads, runs baseline
and treatment pipelines, computes numeric metrics, and writes evidence to
`$BOOKMAS_EVIDENCE_DIR/results.json` (or `/evidence/results.json`).
"""

import json
import os
import sys
from typing import Dict, List

from config import (
    CHAPTER_NUMBER,
    EXPERIMENT_ID,
    build_workloads,
    get_baseline_config,
    get_treatment_config,
)
from rag_simulation import build_corpus, run_pipeline_for_workload


def detect_environment() -> Dict[str, str]:
    return {
        "os": os.name,
        "python": sys.version.split()[0],
    }


def main() -> None:
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    evidence_path = os.path.join(evidence_dir, "results.json")

    corpus_chunks = build_corpus()
    workloads = build_workloads()

    baseline_cfg = get_baseline_config()
    treatment_cfg = get_treatment_config()

    runs: List[Dict[str, object]] = []

    for workload in workloads:
        queries_text = [q.text for q in workload.queries]
        metrics_by_variant = run_pipeline_for_workload(
            workload_name=workload.name,
            queries=queries_text,
            base_chunks=corpus_chunks,
            baseline_config=baseline_cfg,
            treatment_config=treatment_cfg,
        )

        for variant in ("baseline", "treatment"):
            metrics = metrics_by_variant[variant]
            # Validate metrics are numeric values only.
            numeric_metrics: Dict[str, float] = {}
            for k, v in metrics.items():
                if not isinstance(v, (int, float)):
                    continue
                numeric_metrics[k] = float(v)

            run_record: Dict[str, object] = {
                "variant": variant,
                "workload_id": workload.name,
                "run_id": f"{variant}-{workload.name}",
                "success": True,
                "metrics": numeric_metrics,
            }
            runs.append(run_record)

    evidence: Dict[str, object] = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": "exp-07-rag-indirect-injection-hardening-v1",
        "environment": detect_environment(),
        "runs": runs,
        "notes": (
            "Offline simulated RAG experiment with baseline and hardened "
            "pipelines. Metrics are averages over a small synthetic query "
            "set per workload."
        ),
    }

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)


if __name__ == "__main__":
    main()
