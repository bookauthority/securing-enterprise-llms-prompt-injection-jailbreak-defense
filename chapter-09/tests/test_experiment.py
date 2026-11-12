import json
import os
import tempfile
import unittest
from pathlib import Path

import run as experiment_run
from experiment.core import WORKLOAD_IDS, run_all_workloads_for_variant


class TestCoreLogic(unittest.TestCase):
    def test_run_all_workloads_for_variant_baseline(self) -> None:
        results = run_all_workloads_for_variant("baseline")
        self.assertIsInstance(results, dict)
        self.assertEqual(set(results.keys()), set(WORKLOAD_IDS))
        for wid, metrics in results.items():
            self.assertIn("jailbreak_success_rate", metrics)
            self.assertIn("harm_severity_score_mean", metrics)
            self.assertIsInstance(metrics["jailbreak_success_rate"], (int, float))
            self.assertIsInstance(metrics["harm_severity_score_mean"], (int, float))

    def test_run_all_workloads_for_variant_treatment(self) -> None:
        results = run_all_workloads_for_variant("treatment")
        self.assertEqual(set(results.keys()), set(WORKLOAD_IDS))


class TestEvidenceSchema(unittest.TestCase):
    def test_run_produces_valid_results_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["BOOKMAS_EVIDENCE_DIR"] = tmpdir
            experiment_run.main()

            path = Path(tmpdir) / "results.json"
            self.assertTrue(path.exists(), "results.json should be created")

            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Top-level keys
            self.assertEqual(data.get("chapter"), 9)
            self.assertEqual(data.get("experiment_id"), "exp-ch09-advanced-jailbreak-defense-v1")
            self.assertIn("environment", data)
            self.assertIn("runs", data)

            env = data["environment"]
            self.assertIsInstance(env.get("os"), str)
            self.assertIsInstance(env.get("python"), str)

            runs = data["runs"]
            self.assertIsInstance(runs, list)
            self.assertGreaterEqual(len(runs), 1)

            # Validate each run record and check required metrics properties
            seen = {(r["variant"], r["workload_id"]) for r in runs}
            for wid in WORKLOAD_IDS:
                self.assertIn(("baseline", wid), seen)
                self.assertIn(("treatment", wid), seen)

            for r in runs:
                self.assertIn(r["variant"], ("baseline", "treatment"))
                self.assertIn(r["workload_id"], WORKLOAD_IDS)
                self.assertIsInstance(r.get("run_id"), str)
                self.assertIsInstance(r.get("success"), bool)
                metrics = r.get("metrics")
                self.assertIsInstance(metrics, dict)
                # Ensure numeric metrics and no nulls for reported metrics
                for key in ["jailbreak_success_rate", "harm_severity_score_mean"]:
                    self.assertIn(key, metrics)
                    val = metrics[key]
                    self.assertIsInstance(val, (int, float))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
