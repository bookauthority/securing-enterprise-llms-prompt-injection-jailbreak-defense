# Chapter 8 Experiment: Securing Agentic Workflows and Tool Use

This is a self-contained Python 3.11+ experiment project implementing a simplified, offline version of the specification:

- **Experiment ID**: `exp-ch08-secure-agentic-workflows-v1`
- **Chapter**: 8
- **Title**: Securing Agentic Workflows and Tool Use

The goal is to compare a **naive baseline agentic workflow** against a **secure, least-privilege, policy-driven tool orchestrator**. Since this sandbox is offline and cannot call real LLMs or network services, we simulate the agent and tools deterministically while preserving the *structural* ideas:

- Baseline exposes all tools directly to the agent with minimal mediation.
- Treatment uses explicit tool contracts, per-request scoping, a policy layer, and human-in-the-loop approvals for high-risk tools.

The experiment produces evidence under `/evidence/results.json` (or a custom path via `BOOKMAS_EVIDENCE_DIR`) that follows the required schema.

## Layout

- `run.py` — main entrypoint. Runs the experiment for all workloads and both variants and writes evidence.
- `experiment/core.py` — core experiment engine, abstractions for tools, policies, orchestrators, workloads, and metrics.
- `experiment/workloads.py` — deterministic workloads (benign and adversarial prompts and their classification).
- `experiment/agents.py` — naive baseline "agent" and secure orchestrator behavior.
- `experiment/metrics.py` — metric computation from logged runs.
- `tests/test_experiment.py` — unit tests that validate the evidence schema and basic behavior.
- `requirements.txt` — intentionally empty of runtime dependencies (standard library only).

## What is Simulated vs. Real

Given offline and dependency constraints:

- **No real LLM calls** occur. Instead, we use simple deterministic rule-based logic to decide which tools would be "proposed" or "executed" under both baseline and treatment. The logic is designed to mimic likely behaviors in benign and adversarial prompts.
- **Tools** are mocked as pure Python classes with no I/O outside process memory. They simulate possible unsafe actions (like exfiltration, high-risk CI triggers, cross-tenant access) via flags rather than real side effects.
- **Policies & contracts**: The treatment orchestrator enforces schemas and safety rules. Baseline mostly passes everything through.
- **Human approval** is simulated via deterministic rules (e.g., reject clearly out-of-scope high-risk requests, allow safe ones).

Despite these simplifications, the experiment retains:

- Two variants (baseline, treatment) evaluated on identical workloads.
- Unsafe vs. safe tool invocations determined by a consistent offline labeler.
- Comparable metrics, at least one shared numeric metric per run.

## Running the Experiment

```bash
# From the repository root (directory containing run.py)
python run.py
```

This will:

1. Execute all defined workloads for both baseline and treatment.
2. For each `(variant, workload)` pair, produce at least one run.
3. Compute simple numeric metrics per run (e.g., number of unsafe tool actions, total tool invocations).
4. Write evidence JSON to `${BOOKMAS_EVIDENCE_DIR:-/evidence}/results.json` with the required top-level structure.

If `/evidence` does not exist, `run.py` will create it. You can override the evidence directory:

```bash
BOOKMAS_EVIDENCE_DIR=/tmp/evidence python run.py
```

## Running Tests

Tests assume Python 3.11+ and no external packages.

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests verify that:

- The experiment runs end-to-end and produces a valid evidence file.
- The evidence file adheres to the required schema (field types, required fields, etc.).
- There is at least one baseline and one treatment run for each workload.
- All metric values are numeric (no nulls, strings, or nested structures).

## Metrics

The original spec defines many metrics, several of which depend on real timing or complex behaviors that are not measurable in this offline sandbox. Here we implement a safe subset that can be measured deterministically from our simulation:

- `successful_unsafe_tool_actions` (integer)
- `unsafe_tool_action_rate` (float)
- `blocked_unsafe_tool_attempts` (integer)
- `missed_unsafe_actions` (integer)
- `tool_invocations_per_request` (float)

Other metrics like latency percentiles or human approval load, which would require real wall-clock measurements or asynchronous interactions, are omitted from the `metrics` objects to avoid fabricating data. The omission is documented in the `notes` field of the evidence file.

## Design Overview

### Baseline (Naive Agent)

- Single agent logic that, given a prompt and the list of available tools, chooses tool invocations based on simple keyword matching.
- All tools are always in scope for every request.
- No explicit contracts or argument validation; any proposed call is executed.
- No input/output mediation.
- No human approvals, even for high-risk tools.
- An offline labeler marks some invocations as unsafe (e.g., cross-tenant CRM access, high-risk CI triggers to forbidden environments, or ticket updates for other users).

### Treatment (Secure Orchestrator)

- Per-workload scoping limits which tools are exposed for a given prompt (e.g., in low-risk doc workload, only doc and formatting tools are available).
- Each tool has a contract (Python dataclasses + simple checks) defining risk level and allowed argument patterns.
- A central policy engine inspects proposed tool invocations and may:
  - Allow safe actions.
  - Block unsafe or out-of-scope attempts.
  - Require human approval for high-risk actions.
- A human approval simulator makes deterministic decisions.
- Unsafe invocations are preferentially **blocked**, so treatment should observe fewer `successful_unsafe_tool_actions` and a lower `unsafe_tool_action_rate` than baseline.

### Workloads

We implement four workloads matching the spec identifiers:

1. `wl-01-low-risk-internal-assistant`
2. `wl-02-ticketing-and-crm-automation`
3. `wl-03-code-assistant-with-repo-and-ci-tools`
4. `wl-04-human-approval-stress-test`

Each workload defines a list of prompts and which prompts are benign or adversarial. The simple agent logic will behave more aggressively (attempt more tools, including unsafe combinations) on adversarial prompts.

## Reproducibility

- All logic is deterministic and driven by fixed data structures. No randomness is used.
- No external services or environment-dependent behaviors beyond OS and Python version.

## Limitations

- No real LLM behavior is modeled; we use simple keyword heuristics instead.
- Latency, rate limiting, and other runtime-dependent metrics are not measured.
- Tools and policies are simplified, focusing on relative behavior between baseline and treatment rather than realistic enterprise state.

These limitations are explicitly mentioned in the evidence `notes` field so consumers of the evidence understand which metrics are reliable.
