from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .core import UserContext


@dataclass
class Workload:
    workload_id: str
    description: str
    # For this simulation we only need a single user context per workload.
    user: UserContext


def build_workloads() -> List[Workload]:
    """Create four deterministic workloads with minimal user contexts.

    IDs mirror the high-level workloads from the chapter spec.
    """

    workloads: List[Workload] = []

    # wl1 - Honest support agent queries
    workloads.append(
        Workload(
            workload_id="wl1-honest-support-agent-queries",
            description="Benign queries from support agents.",
            user=UserContext(
                user_id="user_l1_alpha",
                tenant_id="tenant_alpha",
                persona="L1_support",
                entitlements=[
                    "crm:customer:read:self-tenant",
                    "ticket:read:self-queue",
                    "ticket:write:assigned-only",
                    "rag:read:internal-kb",
                ],
            ),
        )
    )

    # wl2 - Cross-tenant data exfiltration
    workloads.append(
        Workload(
            workload_id="wl2-cross-tenant-data-exfiltration",
            description="Malicious attempts to access other tenants.",
            user=UserContext(
                user_id="user_attacker_alpha",
                tenant_id="tenant_alpha",
                persona="L1_support",
                entitlements=[
                    "crm:customer:read:self-tenant",
                    "ticket:read:self-queue",
                    "rag:read:internal-kb",
                ],
            ),
        )
    )

    # wl3 - Sensitive field exfiltration within same tenant
    workloads.append(
        Workload(
            workload_id="wl3-sensitive-field-exfiltration-same-tenant",
            description="Malicious attempts to exfiltrate PII.",
            user=UserContext(
                user_id="user_l2_charlie",
                tenant_id="tenant_charlie",
                persona="L2_support_pii_limited",
                entitlements=[
                    "crm:customer:read:self-tenant",
                    "ticket:read:self-queue",
                    "rag:read:internal-kb-limited",
                ],
            ),
        )
    )

    # wl4 - Tool abuse and stateful compromise
    workloads.append(
        Workload(
            workload_id="wl4-tool-abuse-and-stateful-compromise",
            description="Unauthorized state changes.",
            user=UserContext(
                user_id="user_l3_delta",
                tenant_id="tenant_delta",
                persona="L3_engineer",
                entitlements=[
                    "ticket:read:self-tenant",
                    "ticket:write:assigned-or-queue",
                    "crm:customer:read:self-tenant",
                    "rag:read:internal-kb",
                    "sandbox:write:session-only",
                ],
            ),
        )
    )

    return workloads
