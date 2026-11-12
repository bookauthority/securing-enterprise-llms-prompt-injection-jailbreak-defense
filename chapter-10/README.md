# Chapter 10 – Architecting for Least Privilege and Blast Radius Reduction (Synthetic Experiment)

This is a **self-contained, offline Python 3.11+ experiment** that simulates
an LLM orchestration layer under two architectural variants:

- **Baseline** – coarse-grained authorization, no isolation, no redaction.
- **Treatment** – strict least-privilege, per-tenant isolation, and field-level
  redaction.

Because this environment is offline and has no access to real LLMs, databases,
vector stores, or identity providers, the experiment uses a **deterministic
simulator** that emulates how an LLM-driven agent would behave under various
prompt-injection and misuse scenarios.

The experiment is inspired by the provided chapter specification, including
workloads wl1–wl4, but is deliberately minimized and CPU-bounded to run inside
this sandbox.

## Key Ideas Mapped to the Chapter Sections

### 10.1 Zero Trust & Least Privilege

- Baseline treats all tool suggestions as trusted if the user has a coarse
  persona (e.g., `support_agent`).
- Treatment treats the LLM as untrusted. Every tool call is passed through a
  **policy engine** that checks tenant, persona, and action before execution.

### 10.2 Scoping Context & Data Access

- Data is modelled as simple Python lists of `Record` objects tagged with
  `tenant_id`, `sensitivity`, and `pii_fields`.
- Baseline can read **any record from any tenant**.
- Treatment only returns records that match the caller's `tenant_id`, allowed
  resource types, and allowed PII fields.

### 10.3 Per-Request Authorization for Tools & Data

- We model three tools:
  - `ToolCRM` – read CRM-like customer records.
  - `ToolTickets` – read/update ticket-like records.
  - `ToolRAG` – retrieve RAG-like documents.
- In the **baseline**, tools are invoked directly from the session logic.
- In the **treatment**, a `PolicyEngine` decides **allow/deny** for each
  proposed operation (e.g., `crm:read`, `ticket:update`, `rag:read`).

### 10.4 Isolation Patterns

- **Baseline**: single global dataset shared across tenants.
- **Treatment**: per-tenant filtering, plus simple per-session sandbox
  (represented by an in-memory dict) that cannot leak across sessions.

### 10.5 Redaction

- Some fields are labelled as PII (`ssn`, `card_number`, `email`).
- Baseline returns them unmodified.
- Treatment applies **field-level redaction** (e.g., mask all but last 4
  characters) before they reach the user.

### 10.6 Simulating Compromise & Blast Radius

We implement four synthetic workloads:

1. `wl1-honest-support-agent-queries` – benign queries.
2. `wl2-cross-tenant-data-exfiltration` – cross-tenant exfil attempts.
3. `wl3-sensitive-field-exfiltration-same-tenant` – PII exfil within tenant.
4. `wl4-tool-abuse-and-stateful-compromise` – unauthorized state changes.

Each workload is run under both baseline and treatment. The simulator uses
fixed seeds and deterministic logic to ensure reproducible results.

### 10.7 Compliance & Governance

The simulator records minimal metrics analogous to those in the full chapter:

- `unauthorized_document_exposure_count`
- `unauthorized_state_change_count`
- `pii_token_exposure_count`

These metrics are computed from the access-control and redaction logic and
written to `/evidence/results.json` in a fixed schema.

## Project Layout

- `run.py` – entrypoint; runs the experiment and writes evidence JSON.
- `experiment/core.py` – core data structures, policy engine, tools, and
  baseline vs. treatment implementations.
- `experiment/workloads.py` – definitions and synthetic generation of
  workloads wl1–wl4.
- `experiment/runner.py` – orchestration: runs workloads under both variants
  and computes metrics.
- `tests/test_experiment.py` – unit tests that:
  - validate the evidence file schema,
  - confirm at least one baseline and one treatment run per workload,
  - check that metrics are numeric.

## Running the Experiment

1. **Run the experiment**

```bash
python run.py
```

This will:

- Execute all four workloads under both baseline and treatment.
- Create `/evidence/results.json` (the directory is created if missing).

2. **Run tests**

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Tests assume that `run.py` has been executed at least once in the current
workspace so that `/evidence/results.json` exists.

## Evidence Output Contract

`run.py` must write a JSON object to `/evidence/results.json` of the form:

```json
{
  "chapter": 10,
  "experiment_id": "exp-10-architecting-least-privilege-blast-radius-reduction",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "wl1-honest-support-agent-queries",
      "run_id": "baseline-wl1-0",
      "success": true,
      "metrics": {
        "unauthorized_document_exposure_count": 5.0
      }
    }
  ],
  "notes": "optional string"
}
``

Constraints:

- `chapter` is the integer 10.
- `experiment_id` matches exactly the provided spec.
- `environment` includes at least the OS and Python version; both strings.
- `runs` contains **at least one baseline and one treatment run per
  workload**. This implementation generates multiple runs (one per workload
  per variant) with stable `workload_id` names.
- Each `metrics` value is a **finite JSON number** (no strings, objects,
  nulls, or booleans). If a quantity cannot be measured, it is **omitted**
  from `metrics`.

## Limitations vs. a Full System

- No network, databases, real LLMs, or identity providers are used; all
  behavior is simulated with pure Python data and deterministic rules.
- Many advanced metrics from the chapter spec (e.g., latency, redaction
  precision/recall) cannot be faithfully measured here and are therefore
  omitted from the `metrics` object.
- The goal is to demonstrate **relative differences** between baseline and
  treatment under consistent conditions, not to produce real security
  guarantees.

## Extending the Experiment

You can extend this skeleton by:

- Adding more detailed policy rules in `experiment/core.py`.
- Enriching simulated records with additional fields or sensitivity labels.
- Implementing additional metrics that are computable in an offline
  simulation.

The test suite is deliberately strict about the evidence schema; if you
change the output structure you will need to update the tests accordingly.
