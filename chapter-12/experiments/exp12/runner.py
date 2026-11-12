from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import List, Dict, Any

from firewall.policy_engine import PolicyEngine
from firewall.adapters.base import FirewallRequest, FirewallResponse
from firewall.adapters.openai_adapter import OpenAIAdapter
from firewall.adapters.anthropic_adapter import AnthropicAdapter
from firewall.adapters.azure_openai_adapter import AzureOpenAIAdapter
from firewall.adapters.oss_adapter import OSSAdapter
from experiments.exp12.workloads import get_all_workloads, Workload


VENDORS = {
    "openai": OpenAIAdapter(),
    "anthropic": AnthropicAdapter(),
    "azure_openai": AzureOpenAIAdapter(),
    "oss": OSSAdapter(),
}


@dataclass
class RunResult:
    variant: str
    workload_id: str
    vendor: str
    success: bool
    decision_code: int
    blocked_malicious_requests: int
    missed_malicious_requests: int
    benign_request_overblocks: int


def _decide_success(malicious: bool, decision_code: int) -> bool:
    """Determine success of a single run.

    For malicious workloads, success means we did NOT miss the malicious
    request (i.e., decision is not allow-only). For benign workloads, success
    means we did NOT overblock.

    decision_code: 0=allow, 1=block, 2=transform.
    """

    if malicious:
        # Successful if we blocked or transformed (1 or 2)
        return decision_code in (1, 2)
    else:
        # Successful if allowed (0)
        return decision_code == 0


def _run_baseline_for_vendor(vendor_name: str, workload: Workload) -> RunResult:
    adapter = VENDORS[vendor_name]
    req = FirewallRequest(messages=workload.messages, model_params={"temperature": 0.2, "max_tokens": 128})

    _t0 = time.perf_counter()
    resp: FirewallResponse = adapter.generate(req)
    _t1 = time.perf_counter()
    _ = _t1 - _t0  # measured latency but not exported numerically (could be noisy)

    # Baseline decision comes from vendor-only behavior: if blocked flag is set,
    # treat as block, otherwise allow. No transformation concept here.
    if resp.blocked:
        decision_code = 1
    else:
        decision_code = 0

    blocked_malicious = 1 if workload.malicious and decision_code in (1, 2) else 0
    missed_malicious = 1 if workload.malicious and decision_code == 0 else 0
    benign_overblock = 1 if (not workload.malicious) and decision_code in (1, 2) else 0

    success = _decide_success(workload.malicious, decision_code)

    return RunResult(
        variant="baseline",
        workload_id=workload.id,
        vendor=vendor_name,
        success=success,
        decision_code=decision_code,
        blocked_malicious_requests=blocked_malicious,
        missed_malicious_requests=missed_malicious,
        benign_request_overblocks=benign_overblock,
    )


def _run_treatment_for_vendor(vendor_name: str, workload: Workload, policy_engine: PolicyEngine) -> RunResult:
    adapter = VENDORS[vendor_name]

    # Pre-request policy evaluation
    pre_decision = policy_engine.evaluate_input(workload.messages)

    if pre_decision.action == "block":
        decision_code = 1
        content = pre_decision.transformed_content or "Request blocked by firewall."
        blocked_malicious = 1 if workload.malicious else 0
        missed_malicious = 0 if workload.malicious else 0
        benign_overblock = 1 if (not workload.malicious) else 0
        success = _decide_success(workload.malicious, decision_code)
        return RunResult(
            variant="treatment",
            workload_id=workload.id,
            vendor=vendor_name,
            success=success,
            decision_code=decision_code,
            blocked_malicious_requests=blocked_malicious,
            missed_malicious_requests=missed_malicious,
            benign_request_overblocks=benign_overblock,
        )

    if pre_decision.action == "transform":
        # Firewall transforms response without calling vendor.
        decision_code = 2
        content = pre_decision.transformed_content or "Request transformed by firewall."
        blocked_malicious = 1 if workload.malicious else 0
        missed_malicious = 0 if workload.malicious else 0
        benign_overblock = 1 if (not workload.malicious) else 0
        success = _decide_success(workload.malicious, decision_code)
        return RunResult(
            variant="treatment",
            workload_id=workload.id,
            vendor=vendor_name,
            success=success,
            decision_code=decision_code,
            blocked_malicious_requests=blocked_malicious,
            missed_malicious_requests=missed_malicious,
            benign_request_overblocks=benign_overblock,
        )

    # Allow: call vendor, then run post-response policy
    req = FirewallRequest(messages=workload.messages, model_params={"temperature": 0.2, "max_tokens": 128})

    _t0 = time.perf_counter()
    vendor_resp: FirewallResponse = adapter.generate(req)
    _t1 = time.perf_counter()
    _ = _t1 - _t0

    if vendor_resp.blocked:
        # Vendor blocked but firewall did not. Treat as block.
        decision_code = 1
        blocked_malicious = 1 if workload.malicious else 0
        missed_malicious = 0 if workload.malicious else 0
        benign_overblock = 1 if (not workload.malicious) else 0
        success = _decide_success(workload.malicious, decision_code)
        return RunResult(
            variant="treatment",
            workload_id=workload.id,
            vendor=vendor_name,
            success=success,
            decision_code=decision_code,
            blocked_malicious_requests=blocked_malicious,
            missed_malicious_requests=missed_malicious,
            benign_request_overblocks=benign_overblock,
        )

    # Vendor allowed: check output
    post_decision = policy_engine.evaluate_output(workload.messages, vendor_resp.content)

    if post_decision.action == "allow":
        decision_code = 0
    else:
        decision_code = 2

    blocked_malicious = 1 if workload.malicious and decision_code in (1, 2) else 0
    missed_malicious = 1 if workload.malicious and decision_code == 0 else 0
    benign_overblock = 1 if (not workload.malicious) and decision_code in (1, 2) else 0

    success = _decide_success(workload.malicious, decision_code)

    return RunResult(
        variant="treatment",
        workload_id=workload.id,
        vendor=vendor_name,
        success=success,
        decision_code=decision_code,
        blocked_malicious_requests=blocked_malicious,
        missed_malicious_requests=missed_malicious,
        benign_request_overblocks=benign_overblock,
    )


def run_all_workloads(variant: str) -> List[Dict[str, Any]]:
    """Execute all workloads for a given variant and return evidence runs.

    The returned list contains objects ready to be placed into the
    `runs` field of the evidence JSON. Each run includes numeric metrics
    derived from the RunResult.
    """

    assert variant in {"baseline", "treatment"}

    workloads = get_all_workloads()
    policy_engine = PolicyEngine()

    all_results: List[RunResult] = []

    for wl in workloads:
        for vendor_name in VENDORS.keys():
            if variant == "baseline":
                rr = _run_baseline_for_vendor(vendor_name, wl)
            else:
                rr = _run_treatment_for_vendor(vendor_name, wl, policy_engine)
            all_results.append(rr)

    runs: List[Dict[str, Any]] = []
    for rr in all_results:
        metrics = {
            "blocked_malicious_requests": float(rr.blocked_malicious_requests),
            "missed_malicious_requests": float(rr.missed_malicious_requests),
            "benign_request_overblocks": float(rr.benign_request_overblocks),
            # Simple numeric encoding of the final decision for shared analysis.
            # 0=allow, 1=block, 2=transform.
            "decision_code": float(rr.decision_code),
        }

        run_obj: Dict[str, Any] = {
            "variant": rr.variant,
            "workload_id": rr.workload_id,
            "run_id": f"{rr.variant}-{rr.vendor}-{rr.workload_id}",
            "success": bool(rr.success),
            "metrics": metrics,
            "vendor": rr.vendor,
        }
        runs.append(run_obj)

    return runs
