# Chapter 9 – Advanced Jailbreak Defense and Response (Offline Simulation)

This mini-project implements a **self-contained, offline experiment** for:

> **Experiment ID:** `exp-ch09-advanced-jailbreak-defense-v1`  
> **Chapter:** 9 – Advanced Jailbreak Defense and Response

Because the execution environment is offline and cannot reach real LLM APIs,
this project **simulates**:

- A **primary LLM** with vendor safety settings.
- A **guard model** that classifies responses for policy violations.
- A **content firewall** with:
  - Static vs. dynamic policies.
  - Multi-layer output filtering.
  - User-context–aware decisions.
  - Throttling and graceful degradation.

The simulation is deterministic and uses only the Python standard library.
No external network, API keys, or third-party libraries are required.

The goal is to:

1. Provide a reproducible harness that clearly separates **baseline** and
   **treatment** variants.
2. Implement realistic **policy and throttling logic** in code.
3. Produce **measured numeric metrics** from actual execution.
4. Emit evidence in the exact JSON format required by the runtime contract.

## Layout

- `run.py` – Entry point that runs the experiment and writes `/evidence/results.json`.
- `experiment/__init__.py` – Package marker.
- `experiment/core.py` – Core primitives: simulated LLMs, guard model, policies,
  throttling, workloads, and metric computation.
- `tests/test_experiment.py` – Unit tests, including schema checks for
  `results.json`.
- `requirements.txt` – Intentionally empty of runtime dependencies (standard
  library only).

## Baseline vs. Treatment (Simulated)

To match the long-form experiment spec, we model two variants:

### Baseline

- Single **primary LLM** with baked-in vendor safety.
- No custom guard model.
- No dynamic policies (ignores user tier / use case).
- No throttling beyond the simulated model behavior.

### Treatment

- Same primary LLM simulation.
- Additional **guard model** classifier over outputs.
- **Dynamic policies** varying by:
  - `user_tier` (`anonymous`, `internal_employee`, `privileged_analyst`).
  - `use_case` (e.g., `general_chat`, `code_assistant`, etc.).
- **Throttling** and degradation modes:
  - `none`
  - `S1_strict` – stricter classification thresholds.
  - `S2_read_only_safe` – only safe, generic responses allowed.
  - `S3_lockdown` – requests blocked for this session.

## Workloads

We construct three small, deterministic simulated workloads mirroring the
specification:

1. `w1_multi_corpus_jailbreak_attacks`
2. `w2_context_aware_jailbreak_scenarios`
3. `w3_repeated_attacker_simulation`

Each workload produces a list of prompt records with user context. For
repeat-attacker sessions, we explicitly model sessions and track throttling.

## Metrics

Due to the offline nature, we cannot measure latency or call any real vendor.
Instead, we focus on **content-based metrics** that can be computed locally:

- `jailbreak_success_rate` – Simulated proportion of harmful responses.
- `harm_severity_score_mean` – Average severity score from 0–1.

Additional metrics from the spec (e.g., latency, disagreement rate) are **not
reported** because they cannot be meaningfully measured in this sandbox.
We do not fabricate any numbers.

## Evidence File Contract

`run.py` writes a JSON file at:

```text
${BOOKMAS_EVIDENCE_DIR}/results.json
```

Structure:

```json
{
  "chapter": 9,
  "experiment_id": "exp-ch09-advanced-jailbreak-defense-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline" | "treatment",
      "workload_id": "...",  // shared between baseline and treatment
      "run_id": "...",        // unique within workload+variant
      "success": true | false,
      "metrics": {
        "jailbreak_success_rate": <number>,
        "harm_severity_score_mean": <number>
      }
    },
    ...
  ],
  "notes": "... optional text ..."
}
```

- All metric values are **numbers**, never strings, `null`, or nested objects.
- At least one baseline and one treatment run are included **per workload**.

## Running the Experiment

From the project root:

```bash
python -m unittest discover -s tests -p "test_*.py"

# Then run the experiment
export BOOKMAS_EVIDENCE_DIR=/evidence
python run.py
```

After running, inspect `/evidence/results.json`.

## Limitations

- The primary and guard LLMs are **rule-based simulators**. They approximate
  jailbreak dynamics rather than providing real model behavior.
- Latency, cost, or real-vendor safety settings are not modeled.
- Harm categories and scores are simplistic heuristic classifiers.

Even with these limitations, the structure of the experiment—including
baseline vs. treatment, policy layers, throttling, and metric computation—closely
mirrors a real deployment, and the experiment is fully reproducible within
this offline sandbox.