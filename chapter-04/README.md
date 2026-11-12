# Chapter 4 Experiment: Red-Teaming Enterprise LLMs – Offline Attack Harness Simulation

This mini-project implements a **self-contained, offline simulation** of an LLM red-team attack harness for:

- Baseline vs treatment comparison
- Workload/suite-driven execution
- Structured evidence logging
- Deterministic, reproducible metrics

Because the execution environment is **offline** and cannot access real LLM providers, this harness uses a small, deterministic **simulated model** to mimic:

- Prompt injection & jailbreak behaviors
- A simple defense layer ("treatment" variant)
- Stable metrics for regression and comparison

The goal is to demonstrate the **architecture and experimental method**, not to exercise real APIs.

## Layout

- `run.py` – Main entry point that runs the experiment and writes results to `/evidence/results.json`.
- `harness/__init__.py` – Package marker.
- `harness/core.py` – Core data models, harness logic, and evidence emission.
- `harness/simulation.py` – Simulated LLM and simple defense pipeline.
- `harness/experiment_config.py` – Hard-coded experiment configuration mirroring the specification.
- `tests/test_experiment.py` – Unit tests verifying the evidence schema and basic behaviors.

## Running the Experiment

From the project root (where `run.py` is located):

```bash
python run.py
```

The harness will:

1. Enumerate configured workloads and scenarios.
2. Run each scenario for both **baseline** and **treatment** variants.
3. Collect simple metrics (e.g., number of successful attacks, latency).
4. Write a JSON evidence file following the required contract.

### Evidence Output Contract

The experiment writes to a file at:

- Path: `$BOOKMAS_EVIDENCE_DIR/results.json`
- If `BOOKMAS_EVIDENCE_DIR` is not set, it defaults to `/evidence`.

The JSON structure is:

```json
{
  "chapter": 4,
  "experiment_id": "exp-ch04-attack-harness-v1",
  "environment": {
    "os": "...",
    "python": "..."
  },
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "wl-direct-jailbreak-basic",
      "run_id": "wl-direct-jailbreak-basic-baseline-run",
      "success": true,
      "metrics": {
        "attack_success_count": 10.0,
        "attack_total_count": 10.0,
        "attack_success_rate": 1.0,
        "total_elapsed_ms": 0.123
      }
    }
  ],
  "notes": "...optional explanatory text..."
}
```

(The concrete numeric values will be determined by actual execution in this offline harness; the schema and field types are fixed.)

**Constraints enforced by tests:**

- `chapter` is integer `4`.
- `experiment_id` is exactly `"exp-ch04-attack-harness-v1"`.
- `environment.os` and `environment.python` are non-empty strings.
- `runs` contains at least **one baseline** and **one treatment** run **per workload**.
- `metrics` values are all **numbers** (no strings, booleans, `null`, lists, or dicts).
- Additional non-metric information (stdout, notes, evidence) is **not** placed in `metrics`.
- Every declared workload is executed for both baseline and treatment variants.

## What Gets Simulated

We implement three workloads corresponding to the specification:

1. `wl-direct-jailbreak-basic` – direct jailbreak prompts.
2. `wl-direct-prompt-injection-basic` – direct prompt injection.
3. `wl-indirect-prompt-injection-simulated-rag` – indirect prompt injection via retrieved docs.

Each workload contains several **scenarios**, and each scenario is instantiated multiple times with different synthetic prompts. Our simulation uses deterministic rules to decide whether an attack would be classified as a **success** and to create per-test execution evidence matching the `evidence_schema` in the chapter specification (kept in-memory for this minimal BookMAS artifact).

### Baseline vs Treatment

- **Baseline**: raw simulated model – no defenses. It responds to attack prompts and is relatively easy to exploit.
- **Treatment**: same underlying simulated model wrapped in a simple **defense pipeline** that:
  - Scans the prompt for dangerous keywords.
  - Refuses certain requests with a standard denial message.
  - Is imperfect for some indirect injection scenarios, allowing partial success.

This yields different `attack_success_rate` values between baseline and treatment, exercising the A/B comparison logic. The harness preserves whatever attack success rate is actually observed; a fully executed baseline with `attack_success_rate == 0.0` is still marked `success: true`.

## Reproducibility and Determinism

- A fixed random seed (`42`) is used for all harness-side randomness.
- The simulated LLM is fully deterministic given its inputs.
- Each run creates **stable metrics** so rerunning `python run.py` with the same code yields identical JSON output values.

## Requirements

This project deliberately avoids external dependencies and uses only the Python standard library.

- Python **3.11+** (compatible with the requirement of 3.10+, but designed for 3.11).
- No third-party packages are required at runtime.

Install nothing beyond Python itself.

## Running Tests

From the project root:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests will:

- Execute `run.py` to produce `/evidence/results.json` in a temporary evidence directory.
- Validate that the JSON matches the exact schema requirements mandated by the prompt.
- Check baseline/treatment coverage and numeric metrics.

## Extending the Harness (Conceptually)

Although this version uses a simulation, the structure is intentionally close to a real enterprise harness:

- `harness/core.py` includes abstractions that could be hooked up to real LLM providers.
- `harness/experiment_config.py` mirrors the chapter's richer spec: workloads, scenarios, variants.
- `harness/simulation.py` is the only part you'd swap out when moving from offline simulation to real models and defenses.

In a real deployment, you would:

1. Replace the simulated model client with actual HTTP clients (OpenAI, Anthropic, etc.).
2. Add external logging per test execution, as described in the `evidence_schema` of the chapter (separate from this BookMAS-specific `results.json` file).
3. Plug in real defense pipelines (gateways, content firewalls, etc.).
4. Expand the analytics layer to track the full metrics set (attack success, policy violation, data exfiltration, tool misuse, costs, and labeler disagreement).

This experiment provides a **minimal, executable baseline** that still demonstrates:

- Harness structure
- Baseline vs treatment flows
- Deterministic metrics and offline latency measurements
- Schema validation and regression testing
