import json
import os
import unittest
from pathlib import Path

import run as experiment_run


class TestExperimentEvidenceSchema(unittest.TestCase):
    def setUp(self) -> None:
        # Use a temporary evidence directory under /tmp to avoid interfering
        # with any external paths. The harness, however, may still point to
        # /evidence; this test focuses on schema validation.
        self.temp_dir = Path("/tmp/evidence_test")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        os.environ["BOOKMAS_EVIDENCE_DIR"] = str(self.temp_dir)

        # Run the experiment to generate evidence.
        experiment_run.main()

        self.evidence_file = self.temp_dir / "results.json"
        self.assertTrue(self.evidence_file.exists(), "Evidence file was not created")

        with self.evidence_file.open("r", encoding="utf-8") as f:
            self.evidence = json.load(f)

    def test_top_level_structure(self) -> None:
        e = self.evidence
        self.assertIsInstance(e, dict)
        self.assertIn("chapter", e)
        self.assertIn("experiment_id", e)
        self.assertIn("environment", e)
        self.assertIn("runs", e)

        self.assertEqual(e["chapter"], 8)
        self.assertEqual(e["experiment_id"], "exp-ch08-secure-agentic-workflows-v1")

        env = e["environment"]
        self.assertIsInstance(env, dict)
        self.assertIn("os", env)
        self.assertIn("python", env)
        self.assertIsInstance(env["os"], str)
        self.assertIsInstance(env["python"], str)

    def test_runs_schema_and_variants(self) -> None:
        e = self.evidence
        runs = e["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreater(len(runs), 0)

        seen = {(r["variant"], r["workload_id"]) for r in runs}
        expected_workloads = {
            "wl-01-low-risk-internal-assistant",
            "wl-02-ticketing-and-crm-automation",
            "wl-03-code-assistant-with-repo-and-ci-tools",
            "wl-04-human-approval-stress-test",
        }
        for wid in expected_workloads:
            self.assertIn(("baseline", wid), seen)
            self.assertIn(("treatment", wid), seen)

        for r in runs:
            self.assertIn(r["variant"], ("baseline", "treatment"))
            self.assertIn(r["workload_id"], expected_workloads)
            self.assertIsInstance(r["run_id"], str)
            self.assertIsInstance(r["success"], bool)
            self.assertIn("metrics", r)
            metrics = r["metrics"]
            self.assertIsInstance(metrics, dict)

            # Check required numeric metrics
            numeric_keys = [
                "successful_unsafe_tool_actions",
                "unsafe_tool_action_rate",
                "blocked_unsafe_tool_attempts",
                "missed_unsafe_actions",
                "tool_invocations_per_request",
            ]
            for key in numeric_keys:
                self.assertIn(key, metrics)
                value = metrics[key]
                self.assertIsInstance(
                    value, (int, float), f"Metric {key} must be numeric"
                )

    def test_notes_present(self) -> None:
        e = self.evidence
        self.assertIn("notes", e)
        self.assertIsInstance(e["notes"], str)


if __name__ == "__main__":
    unittest.main()
