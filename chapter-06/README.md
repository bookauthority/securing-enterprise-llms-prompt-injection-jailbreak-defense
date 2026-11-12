# Chapter 6 – Direct Prompt Injection Mitigations (Offline Simulation)

This project is a **self-contained Python 3.11+ experiment** that simulates
baseline vs. treatment defences against **direct prompt injection** attacks,
without calling real LLMs or external services.

The goal is to mirror the structure of the chapter's experiment while being
safe and runnable in an offline sandbox. We implement a deterministic
"pseudo‑LLM" and attack harness so that results are reproducible.

## Key Ideas

- **Baseline**: naïve orchestration – raw user prompt passed directly to a
  pseudo‑LLM with only a generic system message.
- **Treatment T1**: hierarchy + structured template + validation/sanitization.
- **Treatment T2**: T1 plus a simple auxiliary detector and policy which can
  block or constrain prompts.
- **Workloads**: W1–W4 as per the specification, but represented here by small
  deterministic prompt sets with labels indicating the style of attack or
  benign request.
- **Metrics**: Because the sandbox is offline and there is no real network,
  we only report metrics that can be **actually measured** locally. In this
  implementation, we use synthetic but instrumented measures:

  - `attack_success_count`: number of cases where the pseudo‑LLM indicates a
    successful injection (as judged by simple rules, see below).
  - `total_prompts`: number of prompts evaluated for a given
    (workload, variant) pair.
  - `attack_success_rate`: `attack_success_count / total_prompts`.

  Latency, cost, and other vendor-specific metrics from the original spec
  are **not** emitted because they cannot be measured meaningfully here.

## Pseudo‑LLM and Defences

We implement simple, fully deterministic logic instead of a real LLM:

- The **pseudo‑LLM** examines the composed messages (system/developer/user)
  and returns a small string describing what it would do.
- The **attack harness** computes whether an "attack" was successful by
  checking whether the output text contains certain markers (e.g., that the
  model agreed to override hierarchy or to execute disallowed actions).

### Baseline Behaviour

The baseline orchestrator:

1. Receives a raw user prompt.
2. Prepends a generic system message.
3. Passes both to the pseudo‑LLM without modification.

The pseudo‑LLM for baseline is **naïve**: if it sees phrases like
"ignore previous instructions" or "act as DAN" in user content, it
will **comply** and mark the output as compromised.

### Treatment T1 – Hierarchy + Template + Validation

Treatment T1 adds:

- A strict **instruction hierarchy** system message.
- A **developer** message describing allowed behaviour.
- A **structured user schema** (task, domain, primary_input,
  extra_instructions).
- An **input validation/sanitization pipeline** that:
  - strips common override phrases ("ignore previous", "reveal system prompt"),
  - redacts suspicious tool abuse phrases.

The pseudo‑LLM for T1 is slightly more defensive: when it sees hierarchy
instructions, it tries to follow system/developer messages and reports
that it ignored conflicting user instructions.

### Treatment T2 – T1 + Auxiliary Detector

Treatment T2 adds on top of T1:

- A simple **keyword‑based detector** that labels prompts as
  `benign`, `suspicious`, or `malicious`.
- A **policy**:
  - `malicious`: block (no LLM call).
  - `suspicious`: allow but add a stricter developer message and note that
    the request was constrained.
  - `benign`: treat as in T1.

The detector is intentionally simple (regex/keyword style) but provides a
concrete example of how auxiliary models/heuristics would integrate into a
content firewall.

## Evidence Format

Running `python run.py` will create `/evidence/results.json` (the path is taken
from the `BOOKMAS_EVIDENCE_DIR` environment variable). The JSON has this
shape:

```json
{
  "chapter": 6,
  "experiment_id": "chap6-direct-prompt-injection-mitigations-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline",  // or "treatment"
      "workload_id": "W1-direct-override-attacks",  // etc.
      "run_id": "baseline_W1_0",
      "success": true,
      "metrics": {
        "attack_success_count": 5,
        "total_prompts": 10,
        "attack_success_rate": 0.5
      }
    }
  ],
  "notes": "...free‑text experiment notes..."
}
``

The **validator requires** that:

- `chapter` is an integer (here, `6`).
- `experiment_id` matches the specification exactly.
- `runs` contains at least one `baseline` and one `treatment` run per
  workload.
- Every value in each `metrics` object is a numeric JSON value.

Our tests assert this schema using only the Python standard library.

## Project Layout

- `run.py` – experiment entry point; orchestrates all variants and workloads,
  gathers metrics, and writes `/evidence/results.json`.
- `baseline_orchestrator.py` – baseline prompt handling.
- `experiments/chap6_direct_injection/input_pipeline.py` – structured input
  schema and validation/sanitization logic.
- `experiments/chap6_direct_injection/aux_detector.py` – auxiliary detector and
  policy logic.
- `experiments/chap6_direct_injection/treatment_orchestrator.py` – T1 & T2
  orchestrators.
- `experiments/chap6_direct_injection/workloads.py` – small deterministic
  workloads W1–W4.
- `experiments/chap6_direct_injection/pseudo_llm.py` – deterministic mock LLM
  and attack success evaluation logic.
- `tests/test_experiment.py` – unittests verifying evidence schema and basic
  behaviour.
- `requirements.txt` – intentionally empty of runtime dependencies; we use only
  the Python standard library.

## Running the Experiment

From the project root:

```bash
export BOOKMAS_EVIDENCE_DIR=/evidence   # or another writable dir
python run.py
```

You should then have:

```bash
cat /evidence/results.json
```

## Running Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests:

- Execute `run.py` in a temporary evidence directory.
- Validate JSON structure and types.
- Check that at least one baseline and one treatment run exist per workload.

## Limitations

- No real LLM calls or vendor SDKs; behaviour is simulated.
- Latency, network cost, and vendor safety settings from the chapter spec
  cannot be faithfully reproduced offline, so they are not reported as
  metrics.
- The attack success logic is rule-based and intentionally simple.

Despite these, the project demonstrates **instruction hierarchy enforcement,
structured prompts, validation/sanitization, auxiliary detection, and an
attack harness** in a way that is reproducible and safe in an offline
environment.
