# exp-llm-sec-011-ci-benchmarks-v1

This is a self-contained, offline Python 3.11+ experiment project for:

> **Chapter 11 – Security Testing, Benchmarking, and Continuous Assurance**  
> Experiment: `exp-llm-sec-011-ci-benchmarks-v1`

The goal is to simulate integrating an LLM security attack harness into CI/CD with variance-aware metrics, benchmarking, and clear evidence artifacts. Since this sandbox is offline and cannot call real model APIs, we use a deterministic **simulated model harness** that mimics different security behaviors for a baseline vs. treatment configuration.

The project focuses on:

- 11.1 Where LLM security testing fits in the SDLC
- 11.2 Expanding the attack harness into a CI/CD gate
- 11.3 Defining metrics and KPIs for prompt injection and jailbreak defense
- 11.4 Benchmarking defenses across models and vendors
- 11.5 Handling non-determinism and variance in test results
- 11.6 Incident response playbooks for LLM security failures
- 11.7 Feedback loops from incidents to models and policies

## What this experiment does

- Implements a **minimal attack harness** over a tiny synthetic corpus resembling
  `prompt_injection_suite_v1` and `jailbreak_suite_v1`.
- Simulates two variants:
  - **Baseline**: manual/ad-hoc testing, single run per test, no CI gating logic.
  - **Treatment**: CI-style runner with repetitions, variance-aware aggregation, and a simple gate.
- Measures simple numeric metrics (e.g., *attack_success_rate*) from actual code execution
  using a deterministic simulated model.
- Writes evidence to `/evidence/results.json` (or `$BOOKMAS_EVIDENCE_DIR/results.json`),
  conforming to the runtime contract required by the book tooling.

The implementation is deliberately small and deterministic, but structured to mirror how a
larger CI-integrated harness would be organized.

## Repository layout

- `run.py` – Main entrypoint. Runs both baseline and treatment variants, for all workloads,
  and writes `results.json` to the evidence directory.
- `llm_sec_harness/`
  - `__init__.py` – Package marker.
  - `attack_corpus.py` – Defines in-memory synthetic attack suites and workloads.
  - `model_sim.py` – Simulated LLM "models" and defense profiles.
  - `metrics.py` – Metric computations, including simple binomial proportion CI width.
  - `runner.py` – Baseline and treatment runners producing comparable metrics.
- `tests/test_experiment.py` – Unittests that validate:
  - Evidence schema for `/evidence/results.json` (shape, types, variants, workloads).
  - Deterministic behavior and correct metric calculation.

## Running the experiment

From the project root:

```bash
python run.py
```

This will:

1. Determine the evidence directory:
   - `$BOOKMAS_EVIDENCE_DIR` if defined, otherwise `/evidence`.
2. Execute baseline and treatment runs for each configured workload.
3. Write `results.json` with content matching:

```json
{
  "chapter": 11,
  "experiment_id": "exp-llm-sec-011-ci-benchmarks-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "...",
      "run_id": "...",
      "success": true,
      "metrics": {"attack_success_rate": 0.0}
    },
    {
      "variant": "treatment",
      "workload_id": "...",
      "run_id": "...",
      "success": true,
      "metrics": {
        "attack_success_rate": 0.0,
        "attack_success_rate_ci_width": 0.0
      }
    }
  ],
  "notes": "..."
}
```

The exact numeric values will depend on the simulated model logic but are fully
deterministic for a given code version.

## Workloads in this experiment

We provide small synthetic analogues to the spec's workloads:

1. `prompt_injection_suite_v1`
2. `jailbreak_suite_v1`
3. `variance_sensitivity_workload`

For each workload we:

- Run a **baseline** variant: single attempt per test case, no variance analysis.
- Run a **treatment** variant: multiple attempts per test case (3 repetitions in this
  simplified experiment), and compute a simple 95% confidence interval width to
  represent variance handling.

The `cross_model_benchmark_matrix` is represented implicitly by having two simulated
model behaviors (less secure vs. more secure) behind baseline vs. treatment. In a
real system this matrix would be driven by config files and multiple providers.

## How metrics are computed

We use simple, reproducible metrics implemented in `llm_sec_harness.metrics`:

- `attack_success_rate` – fraction of attempts where the simulated model is judged
  to have violated security expectations.
- `attack_success_rate_ci_width` – width of a 95% confidence interval around the
  success rate, approximated with a normal-based binomial CI; treatment only.

All metrics are computed directly from actual in-memory execution of the attack
corpora against the simulated model(s). No metrics are invented.

## Tests

Run tests with:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests validate:

- That running `run.py` produces `/evidence/results.json` with:
  - `chapter == 11`
  - `experiment_id == "exp-llm-sec-011-ci-benchmarks-v1"`
  - At least one **baseline** and one **treatment** run for each workload.
  - All metrics values are finite numbers.
- That the metrics module behaves as expected on simple synthetic inputs.

## Offline and dependency constraints

- This project uses **only the Python standard library** at runtime.
- `requirements.txt` is intentionally empty of third-party packages.
- No network access, subprocesses, or shell commands are used.
- The only filesystem locations written are inside the project and `/evidence` (or
  `$BOOKMAS_EVIDENCE_DIR`).

## Relation to the chapter text

This toy harness mirrors the chapter concepts:

- **CI/CD Gate:** The treatment runner decides a `success` flag based on whether
  `attack_success_rate` stays below a simple threshold, representing CI pass/fail.
- **Variance Handling:** Repeated runs per test case and CI width estimates mirror
  variance-aware aggregation for non-deterministic models.
- **Benchmarking & KPIs:** Even though the models are simulated, we compute KPIs
  that are structurally similar to those for real vendors and configurations.
- **Continuous Assurance Evidence:** The generated `results.json` serves as an
  evidence artifact that an external system (such as the book's validator) can
  inspect to confirm that security tests are actually being run.
