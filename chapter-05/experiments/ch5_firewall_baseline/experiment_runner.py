import time
from typing import Dict, Any, List

from apps.sample_enterprise_assistant.baseline_app.app_server_baseline import (
    BaselineAppServer,
)
from apps.sample_enterprise_assistant.firewalled_app.app_server_firewalled import (
    FirewalledAppServer,
)
from firewall.content_firewall_server import ContentFirewall
from .workloads import all_workloads, Workload


WORKLOAD_IDS = [
    "wl-benign-enterprise-queries",
    "wl-policy-violating-inputs",
    "wl-jailbreak-and-prompt-injection-outputs",
    "wl-mixed-live-session-simulation",
]


def _run_single_workload_baseline(app: BaselineAppServer, workload: Workload) -> Dict[str, Any]:
    latencies: List[float] = []
    blocked_count = 0
    for item in workload.items:
        start = time.perf_counter()
        resp = app.chat(prompt=item.prompt, user_role=item.user_role)
        end = time.perf_counter()
        latencies.append((end - start) * 1000.0)
        if resp["blocked"]:
            blocked_count += 1
    total = len(workload.items)
    mean_latency = sum(latencies) / total if total > 0 else 0.0
    blocked_fraction = blocked_count / total if total > 0 else 0.0
    return {
        "mean_latency_ms": mean_latency,
        "blocked_fraction": blocked_fraction,
        "total_requests": total,
    }


def _run_single_workload_treatment(app: FirewalledAppServer, workload: Workload) -> Dict[str, Any]:
    latencies: List[float] = []
    blocked_count = 0
    for item in workload.items:
        start = time.perf_counter()
        resp = app.chat(prompt=item.prompt, user_role=item.user_role)
        end = time.perf_counter()
        latencies.append((end - start) * 1000.0)
        if resp["blocked"]:
            blocked_count += 1
    total = len(workload.items)
    mean_latency = sum(latencies) / total if total > 0 else 0.0
    blocked_fraction = blocked_count / total if total > 0 else 0.0
    return {
        "mean_latency_ms": mean_latency,
        "blocked_fraction": blocked_fraction,
        "total_requests": total,
    }


def run_all_workloads(variant: str) -> Dict[str, Dict[str, Any]]:
    """Run all workloads for the given variant.

    Returns a mapping workload_id -> summary metrics.
    """

    workloads = {w.id: w for w in all_workloads()}
    results: Dict[str, Dict[str, Any]] = {}

    if variant == "baseline":
        app = BaselineAppServer()
        for wid, wl in workloads.items():
            results[wid] = _run_single_workload_baseline(app, wl)
    elif variant == "treatment":
        firewall = ContentFirewall()
        app = FirewalledAppServer(firewall)
        for wid, wl in workloads.items():
            results[wid] = _run_single_workload_treatment(app, wl)
    else:
        raise ValueError(f"Unknown variant: {variant}")

    return results
