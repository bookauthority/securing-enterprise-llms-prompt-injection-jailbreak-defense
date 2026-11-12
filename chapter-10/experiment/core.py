from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ----------------------------- Data Model ---------------------------------


@dataclass
class Record:
    """Represents a generic data record used by tools.

    Each record belongs to a tenant and may carry PII fields.
    """

    record_id: str
    tenant_id: str
    data: Dict[str, str]
    pii_fields: List[str] = field(default_factory=list)
    sensitive: bool = False


# --------------------------- Synthetic Dataset -----------------------------


def build_synthetic_dataset() -> Dict[str, List[Record]]:
    """Return deterministic synthetic datasets for CRM, tickets, and RAG.

    Each dataset is keyed by a domain name ("crm", "tickets", "rag").

    Tenants: tenant_alpha, tenant_bravo, tenant_charlie, tenant_delta
    """

    crm: List[Record] = []
    tickets: List[Record] = []
    rag: List[Record] = []

    # CRM records per tenant
    for tenant in ["tenant_alpha", "tenant_bravo", "tenant_charlie", "tenant_delta"]:
        for i in range(3):
            rid = f"{tenant}-cust-{i}"
            crm.append(
                Record(
                    record_id=rid,
                    tenant_id=tenant,
                    data={
                        "name": f"Customer {i} of {tenant}",
                        "email": f"cust{i}@{tenant}.example.com",
                        "ssn": f"123-45-67{i}{i}",
                        "card_number": f"41111111111111{i}{i}",
                    },
                    pii_fields=["email", "ssn", "card_number"],
                    sensitive=True,
                )
            )

    # Tickets per tenant
    for tenant in ["tenant_alpha", "tenant_bravo", "tenant_charlie", "tenant_delta"]:
        for i in range(5):
            rid = f"{tenant}-ticket-{i}"
            assigned_user = f"user_{i % 2}"  # user_0 or user_1
            queue = "payments" if i % 2 == 0 else "general"
            tickets.append(
                Record(
                    record_id=rid,
                    tenant_id=tenant,
                    data={
                        "title": f"Issue {i} for {tenant}",
                        "status": "open",
                        "assigned_user": assigned_user,
                        "queue": queue,
                        "internal_note": f"Internal note {i} for {tenant}",
                    },
                    pii_fields=[],
                    sensitive=False,
                )
            )

    # RAG docs per tenant
    for tenant in ["tenant_alpha", "tenant_bravo", "tenant_charlie", "tenant_delta"]:
        for i in range(4):
            rid = f"{tenant}-doc-{i}"
            rag.append(
                Record(
                    record_id=rid,
                    tenant_id=tenant,
                    data={
                        "content": (
                            f"Knowledge base article {i} for {tenant}. "
                            f"Contains guidance and possibly PII like SSN 999-99-99{i}{i}."
                        )
                    },
                    pii_fields=["content"],
                    sensitive=True,
                )
            )

    return {"crm": crm, "tickets": tickets, "rag": rag}


# ---------------------------- Policy Engine --------------------------------


@dataclass
class UserContext:
    user_id: str
    tenant_id: str
    persona: str
    entitlements: List[str]


class PolicyEngine:
    """Very small, deterministic policy engine.

    Interprets entitlements strings as allowed actions.
    """

    def __init__(self) -> None:
        pass

    def is_allowed(self, user: UserContext, action: str, resource_tenant: str) -> bool:
        """Return True if the action is allowed on the given tenant.

        - Enforces same-tenant access.
        - Requires that an entitlement starts with the action prefix.
        """

        if user.tenant_id != resource_tenant:
            return False

        for ent in user.entitlements:
            if ent.startswith(action):
                return True
        return False


# -------------------------- Redaction Utilities ----------------------------


def redact_value(value: str) -> str:
    """Redact a PII value but keep last 4 characters where possible."""

    if len(value) <= 4:
        return "*" * len(value)
    visible = value[-4:]
    return "*" * (len(value) - 4) + visible


def apply_redaction(record: Record, allowed_pii_fields: List[str]) -> Tuple[Record, int]:
    """Return a redacted copy of the record and the number of redacted fields.

    Any PII field not in `allowed_pii_fields` is masked via `redact_value`.
    """

    redacted = Record(
        record_id=record.record_id,
        tenant_id=record.tenant_id,
        data=dict(record.data),
        pii_fields=list(record.pii_fields),
        sensitive=record.sensitive,
    )
    redactions = 0
    for field in record.pii_fields:
        if field not in allowed_pii_fields and field in redacted.data:
            redacted.data[field] = redact_value(str(redacted.data[field]))
            redactions += 1
    return redacted, redactions


# ------------------------------ Tools --------------------------------------


class ToolCRM:
    def __init__(self, dataset: List[Record]):
        self.dataset = dataset

    def query_all(self) -> List[Record]:
        return list(self.dataset)


class ToolTickets:
    def __init__(self, dataset: List[Record]):
        self.dataset = dataset

    def list_open_by_tenant(self, tenant_id: str) -> List[Record]:
        return [r for r in self.dataset if r.tenant_id == tenant_id and r.data.get("status") == "open"]

    def close_ticket(self, record_id: str) -> Optional[Record]:
        for r in self.dataset:
            if r.record_id == record_id:
                r.data["status"] = "closed"
                return r
        return None


class ToolRAG:
    def __init__(self, dataset: List[Record]):
        self.dataset = dataset

    def search_all(self) -> List[Record]:
        return list(self.dataset)


# ------------------------- Baseline vs Treatment ---------------------------


@dataclass
class Metrics:
    unauthorized_document_exposure_count: int = 0
    pii_token_exposure_count: int = 0
    unauthorized_state_change_count: int = 0


def _simulate_pii_tokens(records: List[Record], pii_fields: List[str]) -> int:
    """Approximate number of PII tokens exposed by counting characters.

    This is a deterministic surrogate metric: each character is treated as
    one token to keep implementation simple and bounded.
    """

    count = 0
    for r in records:
        for f in pii_fields:
            if f in r.data:
                count += len(str(r.data[f]))
    return count


def run_baseline_scenario(
    user: UserContext,
    variant_workload_id: str,
    datasets: Dict[str, List[Record]],
) -> Metrics:
    """Simulate baseline behavior for a given workload.

    The behavior is simplistic:
    - Any tool can read from any tenant.
    - Tickets can be closed without restriction.
    - No redaction is applied.
    """

    crm = ToolCRM(datasets["crm"]).query_all()
    tickets_tool = ToolTickets(datasets["tickets"])
    rag_docs = ToolRAG(datasets["rag"]).search_all()

    metrics = Metrics()

    # Workload-dependent logic: we use workload id prefixes to drive behavior.
    if variant_workload_id.startswith("wl1"):
        # Benign queries: read own-tenant CRM and tickets
        exposed_docs = [r for r in crm if r.tenant_id == user.tenant_id]
        metrics.unauthorized_document_exposure_count = 0
        metrics.pii_token_exposure_count = _simulate_pii_tokens(exposed_docs, ["email", "ssn", "card_number"])

    elif variant_workload_id.startswith("wl2"):
        # Cross-tenant exfiltration: attacker asks for everything
        exposed_docs = list(crm) + list(rag_docs)
        # Any document not in user's tenant is unauthorized
        for r in exposed_docs:
            if r.tenant_id != user.tenant_id:
                metrics.unauthorized_document_exposure_count += 1
        metrics.pii_token_exposure_count = _simulate_pii_tokens(exposed_docs, ["email", "ssn", "card_number", "content"])

    elif variant_workload_id.startswith("wl3"):
        # PII exfil within tenant: ask for all PII in same tenant
        exposed_docs = [r for r in crm if r.tenant_id == user.tenant_id]
        metrics.unauthorized_document_exposure_count = 0  # same tenant, allowed
        metrics.pii_token_exposure_count = _simulate_pii_tokens(exposed_docs, ["ssn", "card_number"])

    elif variant_workload_id.startswith("wl4"):
        # Tool abuse: close all tickets across tenants, count cross-tenant as unauthorized state change
        for r in list(tickets_tool.dataset):
            before = r.data.get("status")
            tickets_tool.close_ticket(r.record_id)
            after = r.data.get("status")
            if before != after and r.tenant_id != user.tenant_id:
                metrics.unauthorized_state_change_count += 1
        metrics.unauthorized_document_exposure_count = 0
        metrics.pii_token_exposure_count = 0

    return metrics


def run_treatment_scenario(
    user: UserContext,
    variant_workload_id: str,
    datasets: Dict[str, List[Record]],
    policy: PolicyEngine,
) -> Metrics:
    """Simulate treatment behavior for a given workload.

    Treatment enforces:
    - Same-tenant checks via PolicyEngine.
    - Redaction of disallowed PII fields (email, ssn, card_number).
    - Restricted ticket state changes (only same-tenant tickets).
    """

    crm_tool = ToolCRM(datasets["crm"])
    tickets_tool = ToolTickets(datasets["tickets"])
    rag_tool = ToolRAG(datasets["rag"])

    metrics = Metrics()

    allowed_pii_fields = ["name"]  # user never allowed to see raw PII

    if variant_workload_id.startswith("wl1"):
        # Only read same-tenant CRM with redaction.
        visible: List[Record] = []
        for r in crm_tool.query_all():
            if policy.is_allowed(user, "crm:customer:read", r.tenant_id):
                redacted, _ = apply_redaction(r, allowed_pii_fields)
                visible.append(redacted)
        metrics.unauthorized_document_exposure_count = 0
        metrics.pii_token_exposure_count = _simulate_pii_tokens(visible, ["ssn", "card_number", "email"])

    elif variant_workload_id.startswith("wl2"):
        # Cross-tenant exfil: policy restricts to same tenant only.
        exposed: List[Record] = []
        for r in crm_tool.query_all():
            if policy.is_allowed(user, "crm:customer:read", r.tenant_id):
                redacted, _ = apply_redaction(r, allowed_pii_fields)
                exposed.append(redacted)
        for r in rag_tool.search_all():
            if policy.is_allowed(user, "rag:read", r.tenant_id):
                redacted, _ = apply_redaction(r, allowed_pii_fields)
                exposed.append(redacted)
        # No cross-tenant access expected by policy
        metrics.unauthorized_document_exposure_count = 0
        metrics.pii_token_exposure_count = _simulate_pii_tokens(exposed, ["ssn", "card_number", "email", "content"])

    elif variant_workload_id.startswith("wl3"):
        # PII exfil in same tenant: treatment still redacts disallowed PII.
        exposed: List[Record] = []
        for r in crm_tool.query_all():
            if policy.is_allowed(user, "crm:customer:read", r.tenant_id):
                redacted, redactions = apply_redaction(r, allowed_pii_fields)
                exposed.append(redacted)
                # For metrics, count remaining PII tokens that leaked.
        metrics.unauthorized_document_exposure_count = 0
        metrics.pii_token_exposure_count = _simulate_pii_tokens(exposed, ["ssn", "card_number"])

    elif variant_workload_id.startswith("wl4"):
        # Tool abuse: only close tickets in same tenant; cross-tenant denied.
        for r in list(tickets_tool.dataset):
            if policy.is_allowed(user, "ticket:write", r.tenant_id):
                before = r.data.get("status")
                tickets_tool.close_ticket(r.record_id)
                after = r.data.get("status")
                if before != after and r.tenant_id != user.tenant_id:
                    metrics.unauthorized_state_change_count += 1
        metrics.unauthorized_document_exposure_count = 0
        metrics.pii_token_exposure_count = 0

    return metrics
