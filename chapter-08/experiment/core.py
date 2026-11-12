from __future__ import annotations

import dataclasses
import platform
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

from .agents import (
    ApprovalSimulator,
    NaiveAgent,
    PolicyEngine,
    SecureOrchestrator,
    Tool,
    ToolContract,
    ToolExecutionResult,
    ToolCallProposal,
)
from .metrics import RunMetrics, compute_metrics
from .workloads import Workload, WorkloadId, get_workloads


Variant = Literal["baseline", "treatment"]


@dataclass
class RequestLog:
    workload_id: WorkloadId
    variant: Variant
    proposals: List[ToolCallProposal]
    executed: List[ToolExecutionResult]
    blocked_unsafe_attempts: int


def _build_tools() -> Dict[str, Tool]:
    return {
        "doc_search": Tool("doc_search", risk_level="low"),
        "markdown_formatter": Tool("markdown_formatter", risk_level="low"),
        "ticket_read": Tool("ticket_read", risk_level="medium"),
        "ticket_update": Tool("ticket_update", risk_level="high"),
        "crm_view_customer": Tool("crm_view_customer", risk_level="high"),
        "repo_search": Tool("repo_search", risk_level="medium"),
        "ci_trigger": Tool("ci_trigger", risk_level="high"),
    }


def _build_contracts() -> Dict[str, ToolContract]:
    tools = _build_tools()
    return {name: ToolContract(name=name, risk_level=t.risk_level) for name, t in tools.items()}


def _run_variant_on_workload(
    variant: Variant, workload: Workload
) -> RequestLog:
    tools = _build_tools()
    contracts = _build_contracts()

    if variant == "baseline":
        agent = NaiveAgent(tools)
        proposals_all: List[ToolCallProposal] = []
        executed_all: List[ToolExecutionResult] = []
        blocked_unsafe_attempts = 0
        for prompt in workload.prompts:
            proposals, executed = agent.run_request(prompt, workload.workload_id)
            proposals_all.extend(proposals)
            executed_all.extend(executed)
        # For baseline we do not distinguish per-request; blocked attempts are 0.
        # The metrics module expects per-request groupings, so we group all
        # executed calls by prompt position.
        per_request_executed: List[List[ToolExecutionResult]] = []
        idx = 0
        for _ in workload.prompts:
            # Each run_request returns some number of executions; to keep
            # the structure stable, we recompute per prompt.
            # Instead, run again per prompt but ignore side effect since tools
            # are deterministic.
            p = workload.prompts[idx]
            _, executed = agent.run_request(p, workload.workload_id)
            per_request_executed.append(executed)
            idx += 1
        # blocked_unsafe_attempts remains 0.
        blocked_unsafe_attempts = 0
        # Compose logs from recomputed per-request execs.
        executed_flat: List[ToolExecutionResult] = [c for lst in per_request_executed for c in lst]
        proposals_flat: List[ToolCallProposal] = []
        for prompt in workload.prompts:
            props, _ = agent.run_request(prompt, workload.workload_id)
            proposals_flat.extend(props)
        return RequestLog(
            workload_id=workload.workload_id,
            variant=variant,
            proposals=proposals_flat,
            executed=executed_flat,
            blocked_unsafe_attempts=blocked_unsafe_attempts,
        )

    # Treatment variant
    policy_engine = PolicyEngine(contracts)
    approval_sim = ApprovalSimulator()
    orchestrator = SecureOrchestrator(tools, contracts, policy_engine, approval_sim)

    proposals_flat: List[ToolCallProposal] = []
    executed_flat: List[ToolExecutionResult] = []
    blocked_unsafe_attempts = 0

    for prompt in workload.prompts:
        proposals, executed = orchestrator.run_request(prompt, workload.workload_id)
        proposals_flat.extend(proposals)
        executed_flat.extend(executed)
        # Count blocked unsafe attempts using policy and offline labeler logic.
        # For simplicity, infer blocked unsafe as difference between unsafe
        # attempts in baseline vs executed in treatment, but we cannot re-run
        # baseline here safely without double work. Instead, we approximate:
        # - Within orchestrator, unsafe_attempts that are blocked are counted
        #   indirectly by inspecting proposals that did not execute but would
        #   be unsafe by baseline labeler. To keep this deterministic and
        #   bounded, we recompute that labeler here.
        from .agents import NaiveAgent as LabelAgent

        # Use a temporary baseline-like agent only to label unsafe per proposal.
        label_agent = LabelAgent(_build_tools())
        for prop in proposals:
            unsafe = label_agent._label_unsafe_baseline(
                workload.workload_id, prompt, prop
            )
            executed_names = {e.tool_name for e in executed}
            if unsafe and prop.tool_name not in executed_names:
                blocked_unsafe_attempts += 1

    return RequestLog(
        workload_id=workload.workload_id,
        variant=variant,
        proposals=proposals_flat,
        executed=executed_flat,
        blocked_unsafe_attempts=blocked_unsafe_attempts,
    )


def run_experiment(chapter_number: int, experiment_id: str) -> Dict[str, object]:
    """Run the experiment and return evidence dict following the required schema.

    The evidence contains:
    - chapter (int)
    - experiment_id (str)
    - environment (os, python)
    - runs: per (variant, workload) combination with numeric metrics.
    - notes: textual description of limitations and omitted metrics.
    """

    workloads = get_workloads()
    variants: List[Variant] = ["baseline", "treatment"]

    evidence_runs: List[Dict[str, object]] = []

    for workload in workloads:
        for variant in variants:
            log = _run_variant_on_workload(variant, workload)

            # Group executed calls per prompt to compute per-request metrics.
            # For simplicity, assume that run_request was called once per prompt
            # and group by prompt index again using variant-specific behavior.
            # We re-simulate per-request execution to get structured data.
            per_request_executed: List[List[ToolExecutionResult]] = []
            tools = _build_tools()
            contracts = _build_contracts()
            if variant == "baseline":
                agent = NaiveAgent(tools)
                for prompt in workload.prompts:
                    _, executed = agent.run_request(prompt, workload.workload_id)
                    per_request_executed.append(executed)
                blocked_unsafe = 0
            else:
                policy_engine = PolicyEngine(contracts)
                approval_sim = ApprovalSimulator()
                orchestrator = SecureOrchestrator(tools, contracts, policy_engine, approval_sim)
                blocked_unsafe = 0
                for prompt in workload.prompts:
                    proposals, executed = orchestrator.run_request(
                        prompt, workload.workload_id
                    )
                    per_request_executed.append(executed)
                    # Recompute blocked unsafe attempts as before.
                    from .agents import NaiveAgent as LabelAgent

                    label_agent = LabelAgent(_build_tools())
                    executed_names = {e.tool_name for e in executed}
                    for prop in proposals:
                        unsafe = label_agent._label_unsafe_baseline(
                            workload.workload_id, prompt, prop
                        )
                        if unsafe and prop.tool_name not in executed_names:
                            blocked_unsafe += 1

            metrics: RunMetrics = compute_metrics(
                all_executed=per_request_executed,
                all_blocked_unsafe_attempts=blocked_unsafe,
            )

            metrics_dict = {
                "successful_unsafe_tool_actions": float(
                    metrics.successful_unsafe_tool_actions
                ),
                "unsafe_tool_action_rate": float(metrics.unsafe_tool_action_rate),
                "blocked_unsafe_tool_attempts": float(
                    metrics.blocked_unsafe_tool_attempts
                ),
                "missed_unsafe_actions": float(metrics.missed_unsafe_actions),
                "tool_invocations_per_request": float(
                    metrics.tool_invocations_per_request
                ),
            }

            run_record: Dict[str, object] = {
                "variant": variant,
                "workload_id": workload.workload_id,
                "run_id": f"{variant}-{workload.workload_id}-run-1",
                "success": True,
                "metrics": metrics_dict,
            }
            evidence_runs.append(run_record)

    notes = (
        "This offline experiment simulates baseline and treatment orchestrators "
        "using deterministic rule-based logic instead of real LLM calls. "
        "Only a subset of metrics from the chapter specification are measured: "
        "successful_unsafe_tool_actions, unsafe_tool_action_rate, "
        "blocked_unsafe_tool_attempts, missed_unsafe_actions, and "
        "tool_invocations_per_request. Metrics that require network access, "
        "true human approvers, or wall-clock timing (e.g., latency_p50, "
        "latency_p95, human_approval_load) are omitted to avoid fabricating "
        "data."
    )

    evidence: Dict[str, object] = {
        "chapter": int(chapter_number),
        "experiment_id": experiment_id,
        "environment": {
            "os": platform.system(),
            "python": platform.python_version(),
        },
        "runs": evidence_runs,
        "notes": notes,
    }

    return evidence
