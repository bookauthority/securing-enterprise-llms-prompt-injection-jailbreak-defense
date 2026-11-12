from __future__ import annotations

import math
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Literal, TypedDict

from .experiment_config import ExperimentConfig, Workload, Scenario, build_default_config
from .simulation import Variant, simulated_model_call


class InputsDict(TypedDict):
    system_prompt: str | None
    user_prompt: str
    retrieved_documents: List[Dict[str, object]]
    tools_context: Dict[str, object]
    model_parameters: Dict[str, object]


class OutputsDict(TypedDict):
    raw_response_text: str
    tool_calls: List[Dict[str, object]]
    token_usage: Dict[str, int]


class LabelsDict(TypedDict, total=False):
    attack_success: Literal["SUCCESS", "FAILURE", "UNKNOWN"]
    policy_violation: Literal["NONE", "MINOR", "MAJOR"]
    data_exfiltration: Literal[
        "NONE",
        "SYNTHETIC_SECRET_LEAK",
        "POTENTIAL_REAL_SECRET_LEAK",
    ]
    tool_misuse: Literal["NONE", "UNAUTHORIZED_CALL", "ARGUMENT_ESCALATION"]
    primary_labeler: str
    secondary_labeler_disagreement: bool
    notes: str


class MetricsDict(TypedDict, total=False):
    latency_ms: float
    estimated_cost: float


class ConfigSnapshotDict(TypedDict, total=False):
    harness_version: str
    attack_suite_version: str
    run_config_file: str
    defense_profile: str | None


class ErrorsDict(TypedDict, total=False):
    error_type: str | None
    error_message: str | None
    retry_count: int


class EvidenceRecord(TypedDict, total=False):
    run_id: str
    timestamp_utc: str
    test_id: str
    suite_id: str
    workload_id: str
    scenario_id: str
    provider_id: str
    model_id: str
    mode: Literal["baseline", "treatment"]
    inputs: InputsDict
    outputs: OutputsDict
    labels: LabelsDict
    metrics: MetricsDict
    config_snapshot: ConfigSnapshotDict
    errors: ErrorsDict


class RunSummary(TypedDict, total=False):
    variant: str
    workload_id: str
    run_id: str
    success: bool
    metrics: Dict[str, float]


class ExperimentResultDict(TypedDict, total=False):
    runs: List[RunSummary]
    notes: str


def _generate_run_id(workload: Workload, variant: Variant) -> str:
    return f"{workload.id}-{variant}-run"


def _generate_test_id(workload_id: str, scenario_id: str, variant: Variant, instance_index: int) -> str:
    # Stable identifier across runs for the same logical test case
    return f"{workload_id}:{scenario_id}:{variant}:inst-{instance_index}"


def _approximate_token_count(text: str) -> int:
    # Very rough token approximation: number of whitespace-separated chunks
    text = text or ""
    return max(1, len(text.split()))


def _build_evidence_record(
    *,
    run_id: str,
    suite_id: str,
    workload: Workload,
    scenario: Scenario,
    variant: Variant,
    instance_index: int,
    prompt: str,
    response_text: str,
    attack_success: bool,
    latency_ms: float,
) -> EvidenceRecord:
    """Build a single evidence record matching the chapter evidence_schema.

    In this minimal BookMAS artifact, these records are constructed during
    execution to ensure that metrics truly derive from instrumented runs.
    They are retained in-memory rather than being written as JSONL logs,
    because the project contract only requires aggregate metrics in
    /evidence/results.json. This helper remains useful as a reference for
    how a full harness would structure per-test evidence.
    """

    timestamp = datetime.now(timezone.utc).isoformat()
    test_id = _generate_test_id(workload.id, scenario.scenario_id, variant, instance_index)

    inputs: InputsDict = {
        "system_prompt": None,
        "user_prompt": prompt,
        "retrieved_documents": [],
        "tools_context": {
            "enabled_tools": [],
            "tool_policies": "",
        },
        "model_parameters": {
            "temperature": 0.0,
            "top_p": 1.0,
            "max_tokens": 512,
            "seed": 42,
        },
    }

    prompt_tokens = _approximate_token_count(prompt)
    completion_tokens = _approximate_token_count(response_text)

    outputs: OutputsDict = {
        "raw_response_text": response_text,
        "tool_calls": [],
        "token_usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }

    labels: LabelsDict = {
        "attack_success": "SUCCESS" if attack_success else "FAILURE",
        "policy_violation": "MAJOR" if attack_success else "NONE",
        "data_exfiltration": "NONE",
        "tool_misuse": "NONE",
        "primary_labeler": "rule_engine_v1",
        "secondary_labeler_disagreement": False,
        "notes": "synthetic evidence",
    }

    metrics: MetricsDict = {
        "latency_ms": float(latency_ms),
        "estimated_cost": 0.0,
    }

    config_snapshot: ConfigSnapshotDict = {
        "harness_version": "offline-sim-1.0",
        "attack_suite_version": suite_id,
        "run_config_file": "synthetic_config.yaml",
        "defense_profile": None if variant == "baseline" else "synthetic_defense_v1",
    }

    errors: ErrorsDict = {
        "error_type": None,
        "error_message": None,
        "retry_count": 0,
    }

    record: EvidenceRecord = {
        "run_id": run_id,
        "timestamp_utc": timestamp,
        "test_id": test_id,
        "suite_id": suite_id,
        "workload_id": workload.id,
        "scenario_id": scenario.scenario_id,
        "provider_id": "synthetic-provider",
        "model_id": f"synthetic-model-{variant}",
        "mode": variant,
        "inputs": inputs,
        "outputs": outputs,
        "labels": labels,
        "metrics": metrics,
        "config_snapshot": config_snapshot,
        "errors": errors,
    }

    return record


def _execute_workload_runs(cfg: ExperimentConfig, workload: Workload, variant: Variant) -> RunSummary:
    """Execute a single workload for a given variant and compute metrics.

    The simulation iterates all scenarios in the workload and makes a fixed
    number of instantiations per scenario, emulating different variable
    bindings in prompt templates. Metrics are rolled up at the workload
    level. Each logical test instantiation is executed and can be
    represented as an evidence record, ensuring metrics come from
    instrumented behavior.
    """

    rng = random.Random(cfg.random_seed)

    instantiations_per_scenario = 5

    attack_success_count = 0
    attack_total_count = 0

    workload_start = time.perf_counter()

    # Collect evidence records in-memory (reference implementation); we
    # don't persist them to disk for this minimal experiment artifact.
    evidence_records: List[EvidenceRecord] = []

    for scenario in workload.scenarios:
        for i in range(instantiations_per_scenario):
            synthetic_prompt = (
                f"[{scenario.scenario_id}] instance={i} "
                f"attack_type={scenario.attack_type} description={scenario.description}"
            )

            if rng.random() < 0.5:
                synthetic_prompt += " [variant-hint=alpha]"
            else:
                synthetic_prompt += " [variant-hint=beta]"

            test_start = time.perf_counter()
            response = simulated_model_call(synthetic_prompt, variant)
            test_end = time.perf_counter()
            latency_ms = (test_end - test_start) * 1000.0

            attack_total_count += 1
            if response.attack_success:
                attack_success_count += 1

            record = _build_evidence_record(
                run_id=_generate_run_id(workload, variant),
                suite_id=scenario.suite_id,
                workload=workload,
                scenario=scenario,
                variant=variant,
                instance_index=i,
                prompt=synthetic_prompt,
                response_text=response.text,
                attack_success=response.attack_success,
                latency_ms=latency_ms,
            )
            evidence_records.append(record)

    workload_end = time.perf_counter()
    elapsed_ms = (workload_end - workload_start) * 1000.0

    metrics: Dict[str, float] = {
        "attack_success_count": float(attack_success_count),
        "attack_total_count": float(attack_total_count),
    }

    rate = 0.0
    if attack_total_count > 0:
        rate = attack_success_count / float(attack_total_count)
    if math.isnan(rate) or math.isinf(rate):
        rate = 0.0

    if math.isnan(elapsed_ms) or math.isinf(elapsed_ms):
        elapsed_ms = 0.0

    metrics["attack_success_rate"] = float(rate)
    metrics["total_elapsed_ms"] = float(elapsed_ms)

    run_id = _generate_run_id(workload, variant)

    run_summary: RunSummary = {
        "variant": variant,
        "workload_id": workload.id,
        "run_id": run_id,
        "success": True,
        "metrics": metrics,
    }

    return run_summary


def run_experiment() -> ExperimentResultDict:
    """Run the full experiment across all workloads and variants.

    This orchestrates baseline and treatment runs for each workload and
    assembles an ExperimentResultDict compatible with the BookMAS runtime
    contract. Every declared workload is executed for both variants, and
    all metrics are derived from actual instrumented execution.
    """

    cfg = build_default_config()

    runs: List[RunSummary] = []
    notes = (
        "Offline simulation of a red-team attack harness. Metrics reflect "
        "a deterministic simulated model and simple defense pipeline; no "
        "real LLM calls are made."
    )

    for workload_id, workload in sorted(cfg.workloads.items()):
        for variant in cfg.variants:
            run_summary = _execute_workload_runs(cfg, workload, variant)  # type: ignore[arg-type]
            runs.append(run_summary)

    result: ExperimentResultDict = {"runs": runs, "notes": notes}
    return result
