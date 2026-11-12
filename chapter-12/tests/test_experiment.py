import json
import os
import unittest
from pathlib import Path


class ExperimentSchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure evidence directory is clean and predictable for tests.
        # Use a temporary directory under the test working dir instead of /evidence
        self.tmp_evidence_dir = Path("./.test_evidence")
        if self.tmp_evidence_dir.exists():
            # Clean up previous runs
            for p in self.tmp_evidence_dir.iterdir():
                if p.is_file():
                    p.unlink()
        else:
            self.tmp_evidence_dir.mkdir(parents=True, exist_ok=True)
        os.environ["BOOKMAS_EVIDENCE_DIR"] = str(self.tmp_evidence_dir)

    def test_run_produces_valid_results(self) -> None:
        # Import run after setting env so it picks up the test evidence dir
        import run as experiment_run  # type: ignore

        # Execute the experiment main
        experiment_run.main()

        results_path = self.tmp_evidence_dir / "results.json"
        self.assertTrue(results_path.exists(), "results.json must be created in evidence dir")

        with results_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level required fields
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("chapter"), 12)
        self.assertEqual(data.get("experiment_id"), "exp-12-vendor-integration-firewall-001")
        self.assertIn("environment", data)
        self.assertIn("runs", data)

        env = data["environment"]
        self.assertIsInstance(env.get("os"), str)
        self.assertIsInstance(env.get("python"), str)

        runs = data["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreater(len(runs), 0, "There must be at least one run recorded")

        # Track presence of baseline and treatment for each workload
        variants_by_workload = {}

        for run in runs:
            # required run fields
            self.assertIn(run["variant"], ("baseline", "treatment"))
            self.assertIsInstance(run.get("workload_id"), str)
            self.assertIsInstance(run.get("run_id"), str)
            self.assertIsInstance(run.get("success"), bool)
            self.assertIsInstance(run.get("vendor"), str)

            wl_id = run["workload_id"]
            variants_by_workload.setdefault(wl_id, set()).add(run["variant"])

            metrics = run.get("metrics")
            self.assertIsInstance(metrics, dict)

            # metrics must be numeric only
            for key, value in metrics.items():
                self.assertIsInstance(
                    value,
                    (int, float),
                    msg=f"Metric {key} must be a number, got {type(value)}",
                )

            # required metrics
            for key in [
                "blocked_malicious_requests",
                "missed_malicious_requests",
                "benign_request_overblocks",
                "decision_code",
            ]:
                self.assertIn(key, metrics)

        # Ensure at least one baseline and one treatment run per workload
        for wl_id, variants in variants_by_workload.items():
            self.assertIn("baseline", variants, f"Workload {wl_id} missing baseline run")
            self.assertIn("treatment", variants, f"Workload {wl_id} missing treatment run")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
