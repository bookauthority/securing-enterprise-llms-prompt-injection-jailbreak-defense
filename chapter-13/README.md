# Chapter 13 End-to-End Case Studies – Offline Simulation Experiment

This project provides a **self-contained, offline Python 3.11+ experiment** for:

- **Chapter:** 13
- **Experiment ID:** `ch13-endtoend-casestudies-v1`
- **Title:** *Case Studies: Securing Enterprise LLM Deployments End-to-End*

It **simulates** three enterprise LLM applications (internal knowledge assistant, customer support bot, and code assistant) under two variants:

- **Baseline:** minimally secured, relying on default safety only.
- **Treatment:** hardened architecture with a content firewall, RAG hardening, and secure tool orchestration, in spirit of Chapters 4–12.

Because this sandbox is fully offline and cannot call real LLMs or external services, the experiment uses **deterministic, rule-based simulators** to:

- Emulate baseline vs. treatment behavior.
- Generate **numeric metrics** from actual code paths.
- Produce evidence in a standardized JSON format for later analysis.

The design mirrors the full experiment specification while remaining safe and fast to run in a restricted environment.

---

## Project Layout

- `run.py` – Main entry point; runs all workloads for baseline and treatment and writes evidence JSON.
- `experiment/
  - __init__.py
  - simulation.py` – Core logic for workloads, baseline/treatment defenses, and metric computation.
- `tests/test_experiment.py` – Unit tests that validate the evidence schema and basic properties.
- `requirements.txt` – Only standard-library placeholder (no extra dependencies).

No external data, databases, LLMs, or Docker are required. All data is generated in memory.

---

## Running the Experiment

1. **Ensure Python 3.11+ is available.**

2. **Set evidence directory (optional):**

   By default, evidence is written to `/evidence/results.json`.

   To override the directory:

   ```bash
   export BOOKMAS_EVIDENCE_DIR=/tmp/evidence
   mkdir -p "$BOOKMAS_EVIDENCE_DIR"
   ```

3. **Run the experiment:**

   ```bash
   python run.py
   ```

   This will:

   - Execute all three workloads for **both baseline and treatment**.
   - Collect deterministic metrics for each `(workload, variant)` pair.
   - Write evidence to `{BOOKMAS_EVIDENCE_DIR}/results.json`.

4. **Inspect the evidence:**

   Example (assuming default path):

   ```bash
   cat /evidence/results.json
   ```

   The file follows this contract:

   ```json
   {
     "chapter": 13,
     "experiment_id": "ch13-endtoend-casestudies-v1",
     "environment": {"os": "...", "python": "..."},
     "runs": [
       {
         "variant": "baseline",
         "workload_id": "workload_13_2_internal_knowledge_assistant",
         "run_id": "...",
         "success": true,
         "metrics": {
           "successful_attack_rate": 0.42,
           "benign_task_success_rate": 0.9
         }
       },
       {
         "variant": "treatment",
         "workload_id": "workload_13_2_internal_knowledge_assistant",
         "run_id": "...",
         "success": true,
         "metrics": {
           "successful_attack_rate": 0.09,
           "benign_task_success_rate": 0.88
         }
       }
       // ... other workloads ...
     ],
     "notes": "..."
   }
   ```

   All metric values are **numbers** (no strings, booleans, lists, or nulls).

---

## Running Tests

Run unit tests via:

```bash
python -m unittest discover -s tests -p "test_*.py"
``

The tests verify that:

- `run.py` generates `results.json` in the expected schema.
- Required top-level fields exist (`chapter`, `experiment_id`, `environment`, `runs`).
- Each run contains valid `variant`, `workload_id`, `run_id`, `success`, and numeric `metrics`.
- There is at least one baseline and one treatment run **per workload**.

---

## Simulation Design

To stay faithful to the chapter’s end-to-end narrative while fully offline, we implement the following abstractions:

### Workloads

We simulate three workloads matching the specification:

1. `workload_13_2_internal_knowledge_assistant`
2. `workload_13_3_customer_support_bot`
3. `workload_13_4_code_assistant`

Each workload defines a fixed number of **benign** and **adversarial** synthetic requests. Adversarial categories reflect the spec (e.g., direct injection, tool abuse, CI weakening), but are implemented via local rule-based labeling.

### Baseline vs. Treatment Simulation

For each synthetic request, we simulate whether an “attack” succeeds and whether a “benign task” is completed successfully.

- **Baseline behavior:**
  - **Higher** probability that adversarial inputs lead to policy-violating outcomes (e.g., successful attacks).
  - **Slightly higher** benign success rate (less friction from security layers).

- **Treatment behavior:**
  - **Lower** probability of successful attacks (e.g., content firewall and orchestrator blocking/mitigating requests) in a way that qualitatively matches the chapter’s goals.
  - Slightly **lower** benign success rate (some false positives / stricter defenses).

To keep the results **deterministic and reproducible**, we:

- Use a fixed pseudo-random sequence (`random.Random` with frozen seeds per workload & variant).
- Use only standard library logic—no external models.

### Metrics

For each `(workload, variant)` pair we compute numeric metrics that are meaningfully derived from the simulated runs:

- `successful_attack_rate` – Fraction of adversarial requests marked as successful.
- `benign_task_success_rate` – Fraction of benign requests marked as successful.
- `policy_block_rate` – Fraction of all requests that were “blocked” by simulated defenses.

These are intentionally minimal but aligned with the fuller metric set in the specification. We omit metrics we cannot credibly simulate offline (e.g., latency in ms or tool usage volume tied to real systems) rather than fabricate them.

The implementation can be extended by readers to add richer offline simulations, but the current experiment is deliberately simple and fast.

---

## Extending the Experiment

To adapt this experiment:

- Add new workloads or request classes in `experiment/simulation.py`.
- Adjust the baseline/treatment probability tables to explore different tradeoffs.
- Extend metrics to include, for example, per-class attack success rates or simulated latency.

Be sure to:

- Preserve the evidence schema written by `run.py`.
- Keep metrics as **numeric values** only.
- Update tests if you change the schema or add invariants.

---

## Limitations

- No real LLMs, tools, RAG, or databases are used; behavior is simulated.
- Metrics do **not** reflect real security posture; they illustrate how one might measure differences between baseline and treatment in a controlled experiment.
- The experiment is optimized for reproducibility and offline execution rather than realism.

These limitations are explicitly surfaced in the `notes` field of the generated evidence.
