from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest

import run as experiment_run


class TestExperimentEvidenceSchema(unittest.TestCase):
    def setUp(self) -> None:
        # Create a temporary directory to hold evidence.
        self.temp_dir = tempfile.mkdtemp(prefix="evidence_")
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.temp_dir

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        if "BOOKMAS_EVIDENCE_DIR" in os.environ:
            del os.environ["BOOKMAS_EVIDENCE_DIR"]

    def test_run_generates_valid_evidence(self) -> None:
        # Execute main experiment.
        experiment_run.main()

        out_path = os.path.join(self.temp_dir, "results.json")
        self.assertTrue(os.path.exists(out_path), "results.json must be created")

        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level keys
        self.assertIn("chapter", data)
        self.assertIn("experiment_id", data)
        self.assertIn("environment", data)
        self.assertIn("runs", data)

        self.assertIsInstance(data["chapter"], int)
        self.assertEqual(data["chapter"], 6)
        self.assertEqual(data["experiment_id"], "chap6-direct-prompt-injection-mitigations-v1")

        self.assertIsInstance(data["environment"], dict)
        self.assertIn("os", data["environment"])
        self.assertIn("python", data["environment"])

        runs = data["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreater(len(runs), 0)

        # Track variants per workload to ensure coverage.
        workload_variants = {}

        for run in runs:
            self.assertIn("variant", run)
            self.assertIn(run["variant"], {"baseline", "treatment"})
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIsInstance(run["success"], bool)

            self.assertIn("metrics", run)
            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)
            # Required metrics
            for key in ["attack_success_count", "total_prompts", "attack_success_rate"]:
                self.assertIn(key, metrics)
                value = metrics[key]
                # All metrics must be numeric types
                self.assertIsInstance(value, (int, float), msg=f"Metric {key} must be numeric")

            wid = run["workload_id"]
            workload_variants.setdefault(wid, set()).add(run["variant"])

        # Ensure each workload has at least one baseline and one treatment run.
        for wid, variants in workload_variants.items():
            self.assertIn("baseline", variants, msg=f"Workload {wid} missing baseline run")
            self.assertIn("treatment", variants, msg=f"Workload {wid} missing treatment run")


if __name__ == "__main__":
    unittest.main()
