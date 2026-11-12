import json
import os
import unittest
from pathlib import Path


class TestExperimentEvidenceSchema(unittest.TestCase):
    def setUp(self) -> None:
        # Use a temporary evidence directory under /tmp to avoid collisions.
        self.evidence_dir = Path("/tmp/bookmas_ch13_evidence_test")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        os.environ["BOOKMAS_EVIDENCE_DIR"] = str(self.evidence_dir)

        # Run the experiment
        import run as experiment_run  # noqa: F401

        # Reload to ensure main() is not executed on import during testing
        from importlib import reload

        reload(experiment_run)
        experiment_run.main()

        self.results_path = self.evidence_dir / "results.json"
        self.assertTrue(self.results_path.exists(), "results.json was not created")

        with self.results_path.open("r", encoding="utf-8") as f:
            self.data = json.load(f)

    def test_top_level_fields(self):
        d = self.data
        self.assertIn("chapter", d)
        self.assertIn("experiment_id", d)
        self.assertIn("environment", d)
        self.assertIn("runs", d)

        self.assertEqual(d["chapter"], 13)
        self.assertEqual(d["experiment_id"], "ch13-endtoend-casestudies-v1")
        self.assertIsInstance(d["environment"], dict)
        self.assertIsInstance(d["runs"], list)

    def test_runs_schema(self):
        runs = self.data["runs"]
        self.assertGreaterEqual(len(runs), 6)  # 3 workloads * 2 variants

        workload_variants = {}
        for run in runs:
            self.assertIn("variant", run)
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIn("metrics", run)

            self.assertIn(run["variant"], ("baseline", "treatment"))
            self.assertIsInstance(run["workload_id"], str)
            self.assertIsInstance(run["run_id"], str)
            self.assertIsInstance(run["success"], bool)

            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)
            # All metric values must be numbers
            for name, value in metrics.items():
                self.assertIsInstance(
                    value,
                    (int, float),
                    msg=f"Metric {name} must be numeric, got {type(value)}",
                )

            key = run["workload_id"]
            workload_variants.setdefault(key, set()).add(run["variant"])

        # Ensure each workload has at least one baseline and one treatment run
        expected_workloads = {
            "workload_13_2_internal_knowledge_assistant",
            "workload_13_3_customer_support_bot",
            "workload_13_4_code_assistant",
        }
        self.assertTrue(expected_workloads.issubset(set(workload_variants.keys())))
        for wid in expected_workloads:
            variants = workload_variants.get(wid, set())
            self.assertIn("baseline", variants)
            self.assertIn("treatment", variants)

    def test_metric_ranges(self):
        # Ensure main metrics look like probabilities in [0,1]
        for run in self.data["runs"]:
            metrics = run["metrics"]
            for key in [
                "successful_attack_rate",
                "benign_task_success_rate",
                "policy_block_rate",
            ]:
                self.assertIn(key, metrics)
                val = metrics[key]
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 1.0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
