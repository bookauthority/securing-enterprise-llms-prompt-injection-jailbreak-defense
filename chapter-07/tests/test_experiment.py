from __future__ import annotations

"""Unit tests for experiment 7 offline RAG simulation.

Tests focus on:

- Evidence file schema compliance.
- Presence of baseline and treatment runs per workload.
- Metrics are numeric values.
"""

import json
import os
import tempfile
import unittest


class TestExperimentEvidence(unittest.TestCase):
    def setUp(self) -> None:
        # Use a temporary directory for evidence to avoid permission issues.
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.tmpdir.name

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        os.environ.pop("BOOKMAS_EVIDENCE_DIR", None)

    def _run_experiment(self) -> str:
        import run  # Local import to ensure env var is set

        run.main()
        evidence_path = os.path.join(self.tmpdir.name, "results.json")
        self.assertTrue(os.path.exists(evidence_path), "Evidence file not created")
        return evidence_path

    def test_evidence_schema_and_metrics(self) -> None:
        evidence_path = self._run_experiment()

        with open(evidence_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level required fields
        self.assertIn("chapter", data)
        self.assertIsInstance(data["chapter"], int)
        self.assertEqual(data["chapter"], 7)

        self.assertIn("experiment_id", data)
        self.assertIsInstance(data["experiment_id"], str)

        self.assertIn("environment", data)
        self.assertIsInstance(data["environment"], dict)
        self.assertIn("os", data["environment"])
        self.assertIn("python", data["environment"])

        self.assertIn("runs", data)
        self.assertIsInstance(data["runs"], list)
        self.assertGreater(len(data["runs"]), 0)

        # Collect workloads and variants
        by_workload = {}
        for run_record in data["runs"]:
            self.assertIn("variant", run_record)
            self.assertIn(run_record["variant"], ("baseline", "treatment"))
            self.assertIn("workload_id", run_record)
            self.assertIn("run_id", run_record)
            self.assertIn("success", run_record)
            self.assertIsInstance(run_record["success"], bool)
            self.assertIn("metrics", run_record)
            self.assertIsInstance(run_record["metrics"], dict)

            # Metrics must be numbers only
            for k, v in run_record["metrics"].items():
                self.assertIsInstance(
                    v,
                    (int, float),
                    msg=f"Metric {k} must be numeric, got {type(v)}",
                )

            wk = run_record["workload_id"]
            by_workload.setdefault(wk, set()).add(run_record["variant"])

        # Ensure each workload has both baseline and treatment
        for wk, variants in by_workload.items():
            self.assertIn("baseline", variants, msg=f"No baseline run for {wk}")
            self.assertIn("treatment", variants, msg=f"No treatment run for {wk}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
