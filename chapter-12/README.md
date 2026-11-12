# Chapter 12 Experiment: Vendor Architectures, Managed Services, and OSS Models

This project implements a **self-contained, offline simulation** of the experiment described in the specification for chapter 12:

> "Vendor Architectures, Managed Services, and Open Source Models"

The goal is to demonstrate a **vendor-agnostic content firewall** fronting multiple LLM providers (OpenAI, Anthropic, Azure/OpenAI, and an OSS HTTP API) and to compare a **baseline** architecture (direct app-to-vendor) with a **treatment** architecture (via content firewall).

Because this environment is offline and must not make network calls, the vendors are **simulated** with deterministic behavior that mimics differing safety profiles. The **firewall implementation and policy engine are real**, enforcing simple but concrete rules on the same workloads for both baseline and treatment.

## Layout

- `run.py` — Main entrypoint. Runs both baseline and treatment, aggregates metrics, and writes evidence JSON.
- `firewall/__init__.py` — Package marker.
- `firewall/policy_engine.py` — Simple rule-based policy engine implementing chapter-style security policies.
- `firewall/adapters/__init__.py` — Vendor adapter package marker.
- `firewall/adapters/base.py` — Common request/response dataclasses and adapter interface.
- `firewall/adapters/openai_adapter.py` — Simulated OpenAI-like vendor behavior.
- `firewall/adapters/anthropic_adapter.py` — Simulated Anthropic-like vendor behavior.
- `firewall/adapters/azure_openai_adapter.py` — Simulated Azure OpenAI behavior.
- `firewall/adapters/oss_adapter.py` — Simulated OSS model HTTP gateway behavior (weak native safety).
- `experiments/exp12/__init__.py` — Package marker.
- `experiments/exp12/workloads.py` — Workload definitions `wl-12-001` through `wl-12-005` and helpers.
- `experiments/exp12/runner.py` — Baseline and treatment execution logic, metric calculation, and vendor wiring.
- `tests/test_experiment.py` — Unittests validating schema and basic behavior of the experiment.
- `requirements.txt` — No external runtime dependencies.

## Conceptual Architecture

### Baseline

Simulated architecture:

- Client -> Application -> Direct Vendor Adapter (no firewall) -> Simulated Model
- Each vendor applies only its **native safety** (simulated heuristics inside each adapter).

### Treatment

Simulated architecture:

- Client -> Application -> **Content Firewall** (policy engine + vendor selector) -> Vendor Adapter -> Model
- Firewall applies **pre-request** and **post-response** policies based on the unified rules.
- Vendors still apply their native safety, but firewall is the primary control.

## Workloads

The workloads mirror the chapter specification:

- `wl-12-001` — Direct PII exfiltration prompt injection.
- `wl-12-002` — Indirect RAG prompt injection from untrusted context.
- `wl-12-003` — Jailbreak to produce disallowed content (self-harm / malware).
- `wl-12-004` — Benign enterprise Q&A (baseline for utility and overblocking).
- `wl-12-005` — Agentic tool-call simulation for data export to untrusted destination.

Each workload is run against all four simulated vendors in both baseline and treatment.

## Metrics and Evidence Contract

The validator expects `results.json` to live in `/evidence` or `$BOOKMAS_EVIDENCE_DIR`. The file must conform to this schema:

```jsonc
{
  "chapter": 12,
  "experiment_id": "exp-12-vendor-integration-firewall-001",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline" | "treatment",
      "workload_id": "wl-12-001",        // etc.
      "run_id": "unique-string",
      "success": true | false,
      "metrics": {
        "blocked_malicious_requests": 1,  // numeric only
        "missed_malicious_requests": 0,
        "benign_request_overblocks": 0
      },
      // extra non-metric fields allowed here if needed
      "vendor": "openai"
    }
  ],
  "notes": "optional text"
}
```

**Every value in `metrics` must be a JSON number**. No strings, booleans, arrays, or objects are allowed inside `metrics`. Additional descriptive data (e.g., logs, reasoning, notes) must live **outside** the `metrics` object.

The tests in `tests/test_experiment.py` assert this schema and basic sanity of the recorded metrics.

## How Metrics Are Computed

Given that this is a simulation, all metrics are derived deterministically from the internal representations of each run:

- For malicious workloads (`wl-12-001`, `wl-12-002`, `wl-12-003`, `wl-12-005`):
  - `blocked_malicious_requests` is incremented when the **final decision** for that run is to block or transform the unsafe request.
  - `missed_malicious_requests` is incremented when a run is classified as malicious by the workload definition but the final decision is to allow.

- For benign workloads (`wl-12-004`):
  - `benign_request_overblocks` is incremented when the run is benign but the final decision is to block.

We also record a simple scalar metric `decision_code` per run to enable a shared, numeric indicator of final disposition:

- `0` — Allowed
- `1` — Blocked
- `2` — Transformed/sanitized

This keeps the metrics numeric-only while still reflecting firewall decisions.

## Running the Experiment

From the project root:

```bash
python run.py
```

This will:

1. Discover the execution environment (OS, Python version).
2. Run all workloads for the **baseline** variant.
3. Run all workloads for the **treatment** variant.
4. Write `results.json` to:
   - the directory pointed to by `$BOOKMAS_EVIDENCE_DIR`, if set, otherwise
   - `/evidence`.

## Running Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests validate that:

- The experiment can be executed without error.
- `results.json` exists where expected.
- The evidence file conforms to the required schema and value constraints.

## Notes

- No external libraries are used; all logic relies on the Python standard library.
- No network, subprocess, or shell access is performed; vendor calls are entirely simulated.
- The content firewall and workloads are structured so they can be mapped conceptually to real-world deployments described in the chapter.
