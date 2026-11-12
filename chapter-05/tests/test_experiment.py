import json
import os
import unittest

import run as experiment_run


class TestExperimentEvidenceSchema(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure evidence directory is clean and run experiment
        self.evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
        os.makedirs(self.evidence_dir, exist_ok=True)
        self.results_path = os.path.join(self.evidence_dir, "results.json")
        if os.path.exists(self.results_path):
            os.remove(self.results_path)
        experiment_run.main()

    def test_results_file_exists(self) -> None:
        self.assertTrue(os.path.exists(self.results_path))

    def test_results_schema(self) -> None:
        with open(self.results_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level keys
        self.assertIsInstance(data, dict)
        self.assertIn("chapter", data)
        self.assertIn("experiment_id", data)
        self.assertIn("environment", data)
        self.assertIn("runs", data)

        self.assertEqual(data["chapter"], 5)
        self.assertEqual(data["experiment_id"], "exp-ch5-content-firewall-baseline-v1")

        env = data["environment"]
        self.assertIsInstance(env, dict)
        self.assertIn("os", env)
        self.assertIn("python", env)
        self.assertIsInstance(env["os"], str)
        self.assertIsInstance(env["python"], str)

        runs = data["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreaterEqual(len(runs), 2)

        # Track presence of baseline and treatment for each workload
        workload_variants = {}

        for run in runs:
            self.assertIsInstance(run, dict)
            self.assertIn("variant", run)
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIn("metrics", run)

            variant = run["variant"]
            workload_id = run["workload_id"]
            self.assertIn(variant, ("baseline", "treatment"))
            self.assertIsInstance(run["run_id"], str)
            self.assertIsInstance(run["success"], bool)

            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)

            # Ensure required numeric metrics exist and are numbers
            for key in ("mean_latency_ms", "blocked_fraction", "total_requests"):
                self.assertIn(key, metrics)
                self.assertIsInstance(metrics[key], (int, float))

            # Record variants per workload
            workload_variants.setdefault(workload_id, set()).add(variant)

        # Each workload must have at least one baseline and one treatment run
        for workload_id, variants in workload_variants.items():
            self.assertIn("baseline", variants, f"Missing baseline for {workload_id}")
            self.assertIn("treatment", variants, f"Missing treatment for {workload_id}")


if __name__ == "__main__":
    unittest.main()
