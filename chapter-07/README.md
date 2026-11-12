# Experiment 7: Hardening Retrieval-Augmented Generation Against Indirect Prompt Injection

This self-contained Python 3.11+ project simulates a baseline and hardened RAG pipeline, focusing on how retrieval-time sanitization, provenance, and policy filtering can reduce indirect prompt injection.

The goal is not to call real LLMs or vector stores (the sandbox is offline) but to:

- Implement **deterministic simulators** for embedding, retrieval, and model behavior.
- Construct **poisoned vs. benign corpora** and **workloads** as described in the spec.
- Implement a **baseline RAG** and a **treatment (hardened) RAG**.
- Measure at least one **numeric metric** per run and write evidence to `/evidence/results.json` (or `$BOOKMAS_EVIDENCE_DIR/results.json`).

The implementation is kept small enough to run quickly but still mirrors the architecture and risk patterns from the specification.

## Contents

- `run.py` – Entry point. Runs all workloads for both baseline and treatment and writes evidence.
- `rag_simulation.py` – Core logic for corpus, retrieval, sanitization, policy engine, and simulated model behavior.
- `config.py` – Encodes experiment configuration, workloads, and experiment metadata.
- `tests/test_experiment.py` – Unit tests verifying schema compliance and basic behavior.
- `requirements.txt` – Empty of runtime dependencies (standard library only).

## Design Overview

### 1. Offline RAG Simulation

Because no external services are allowed, we:

- Implement a simple **bag-of-words embedding** using hashed token counts.
- Use **cosine similarity** over these vectors for retrieval.
- Represent documents and chunks as Python data structures with metadata:
  - `document_id`, `source_type`, `trust_tier`, `is_poisoned_ground_truth`, `injection_type`.
- Simulate **poisoned** chunks via their content and metadata.

### 2. Baseline vs. Treatment Pipelines

**Baseline**:

- Fixed-size chunking.
- Top-k similarity retrieval with **no sanitization** or metadata-based filtering.
- Model simulator that is easily influenced by poisoned instructions when such chunks are in context.

**Treatment**:

- Slightly smaller chunks and a simple section-aware heuristic (splits additionally at headings/markers).
- **Sanitization/classification** at ingestion:
  - Heuristics detect instruction-like or policy-changing text.
  - Classifier labels recorded as metadata.
- **Query-time filtering**:
  - Low-trust and instruction-like chunks excluded for non-admin, non-forensic queries.
- **Hardened model** that is much less likely to follow injection even when exposed.

Both pipelines share the same corpus and deterministic similarity model for fair comparison.

### 3. Workloads & Queries

We approximate the four workloads in the specification with synthetic queries and corpora:

1. `benign_qa_internal_kb`
2. `mixed_kb_with_poisoned_chunks_internal`
3. `web_and_partner_corpus_poisoned`
4. `sensitive_context_qa_with_poison`

Each workload has:

- A small set of documents and poi­soned chunks.
- A few synthetic queries designed to: trigger benign behavior; retrieve poisoned chunks; test decision boundaries.

For runtime and simplicity, we use far fewer than the hundreds of queries described in the full spec, but the structure is analogous.

### 4. Metrics and Evidence

The real spec defines many metrics that require human or complex automated scoring. In this offline sandbox we instead:

- Implement a **small subset** that can be computed automatically and deterministically.
- Ensure that **every metric reported** comes from actual execution, as required.

For each `(variant, workload)` pair we measure:

- `avg_indirect_injection_success` – fraction of queries where the simulated model behaved as if it followed poisoned instructions (when exposed).
- `avg_context_poison_inclusion` – fraction of queries where at least one poisoned chunk was in the final context.

These are numeric (floats) and stored in `metrics` for each run in the evidence file.

The evidence schema required by the book is a superset. We implement the minimal required fields and keep any non-metric information outside the `metrics` dict (in top-level fields or notes).

### 5. Evidence File Contract

`run.py` must write JSON to `${BOOKMAS_EVIDENCE_DIR:-/evidence}/results.json` with this structure:

```json
{
  "chapter": 7,
  "experiment_id": "exp-07-rag-indirect-injection-hardening-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline" | "treatment",
      "workload_id": "...",
      "run_id": "...",  
      "success": true,
      "metrics": {
        "avg_indirect_injection_success": 0.5,
        "avg_context_poison_inclusion": 0.75
      }
    }
  ],
  "notes": "... optional ..."
}
```

Constraints:

- At least **one baseline** and **one treatment** run per workload.
- **All metric values are numbers** (no booleans, strings, lists, dicts, or nulls).
- Text output, environment metadata, and explanatory notes must live **outside** `metrics`.

Our implementation runs **one run per (variant, workload)** for simplicity.

## How to Run

1. (Optional) Create a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
```

2. Install dependencies (none are strictly required beyond the standard library, but this satisfies the book’s process):

```bash
pip install -r requirements.txt
```

3. Ensure an evidence directory exists (in this sandbox it may be `/evidence`):

```bash
mkdir -p /evidence
```

Alternatively, set a custom evidence dir:

```bash
export BOOKMAS_EVIDENCE_DIR=/tmp/evidence
mkdir -p "$BOOKMAS_EVIDENCE_DIR"
```

4. Run the experiment:

```bash
python run.py
```

This will:

- Construct corpora and workloads.
- Run baseline and treatment pipelines on each workload.
- Compute metrics and write `/evidence/results.json` or `$BOOKMAS_EVIDENCE_DIR/results.json`.

5. Run tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests verify:

- Evidence file adheres to the required schema.
- There is at least one run per (variant, workload).
- Metrics are numeric.

## Mapping to the Specification

This minimal implementation reflects the spec as follows:

- **7.1 & 7.2** – Risk is encoded via `is_poisoned_ground_truth` and injection-like chunk contents in internal, web, and partner-style sources.
- **7.3** – Treatment uses chunk metadata (`trust_tier`, `classifier_labels`) and per-query policy to filter retrieval results.
- **7.4** – A heuristic classifier flags chunks containing instruction-like or policy-downgrade language.
- **7.5** – Isolation is simulated via `trust_tier` and rules that exclude or downgrade low-trust sources for sensitive queries.
- **7.6** – Poisoned corpora and query sets simulate different attack profiles; the scoring computes how often injections succeed.
- **7.7** – The internal knowledge assistant is approximated by the internal KB workloads.

In a real deployment you would replace the simulators in `rag_simulation.py` with calls to actual embedding models, vector stores, and LLMs, while keeping the same ingestion, classification, and policy logic.
