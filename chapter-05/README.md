# Chapter 5 Experiment: Baseline vs Content Firewall

This project is a **self-contained, offline Python 3.11+ experiment** for:

- **Chapter**: 5
- **Experiment ID**: `exp-ch5-content-firewall-baseline-v1`
- **Title**: *Foundational Defenses: Guardrails, Policies, and Content Firewalls*

It simulates:

1. A **baseline** LLM integration that relies only on vendor safety features.
2. A **treatment** variant that routes requests through a **content firewall**
   implementing a simple, declarative policy engine.

Because this repository must run fully offline and without third‑party
dependencies, the LLM, workloads, and vendor safety signals are all **mocked**
with deterministic, in-memory components.

The experiment computes a small set of **numeric metrics** from actual
execution and writes them into an evidence file matching the required schema.

## Layout

- `run.py` – Main entrypoint; runs workloads through baseline and treatment,
  collects metrics, and writes `/evidence/results.json`.
- `firewall/policy_schemas.py` – Typed representations of policies and rules.
- `firewall/policy_engine.py` – Simple policy engine to evaluate input/output
  envelopes against policies.
- `firewall/firewall_logger.py` – Minimal structured logger for firewall
  decisions (writes to in-memory structures, not files).
- `firewall/content_firewall_server.py` – In-process content firewall service
  that mediates between app and mock LLM client.
- `apps/sample_enterprise_assistant/common/llm_client_baseline.py` – Baseline
  mock "vendor" client, including simulated safety flags.
- `apps/sample_enterprise_assistant/common/llm_client_wrapped.py` – Treatment
  client that uses the content firewall.
- `apps/sample_enterprise_assistant/baseline_app/app_server_baseline.py` –
  Baseline app using the direct LLM client.
- `apps/sample_enterprise_assistant/firewalled_app/app_server_firewalled.py` –
  App using the content firewall client.
- `experiments/ch5_firewall_baseline/workloads.py` – Synthetic, deterministic
  workloads matching the spec at a reduced scale.
- `experiments/ch5_firewall_baseline/experiment_runner.py` – Orchestrates
  workloads for baseline and treatment, returns metrics.
- `tests/test_experiment.py` – Unit tests that:
  - run the experiment,
  - assert the **exact evidence schema** for `results.json`, and
  - verify that both baseline and treatment runs exist for each workload.

## Running the Experiment

From the repository root:

```bash
python run.py
```

This will:

1. Create the evidence directory given by `BOOKMAS_EVIDENCE_DIR` or `/evidence`.
2. Execute all workloads in both **baseline** and **treatment** variants.
3. Compute metrics and write them to `/evidence/results.json`.

The evidence file has the required structure:

```json
{
  "chapter": 5,
  "experiment_id": "exp-ch5-content-firewall-baseline-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "wl-benign-enterprise-queries",
      "run_id": "...",
      "success": true,
      "metrics": {
        "mean_latency_ms": 1.23,
        "blocked_fraction": 0.1
      }
    },
    {
      "variant": "treatment",
      "workload_id": "wl-benign-enterprise-queries",
      "run_id": "...",
      "success": true,
      "metrics": {
        "mean_latency_ms": 2.34,
        "blocked_fraction": 0.2
      }
    }
  ],
  "notes": "..."
}
```

All metric values are **numbers**. Non-numeric contextual information is stored
in `notes` or additional top-level fields, never under `metrics`.

## Running Tests

From the repository root:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests will:

- Run `run.py` to generate `/evidence/results.json`.
- Validate its schema against the required contract.
- Ensure there is at least one baseline and one treatment result per workload.

## Limitations vs. Full Chapter Spec

- There is **no real networked LLM**; vendor integrations and safety signals
  are mocked.
- Workload sizes are **dramatically reduced** (a few requests per workload)
  to keep runtime fast and bounded.
- Many chapter-level metrics (e.g., p95 latency, vendor_safety_dependency_ratio)
  are conceptually demonstrated but not fully aligned with real production
  semantics.

Despite these constraints, the structure of the code mirrors the chapter’s
architectural ideas: guardrails vs. policies vs. content firewalls, input and
output mediation, rule-based decisioning, and structured logging suitable for
later evidence analysis.
