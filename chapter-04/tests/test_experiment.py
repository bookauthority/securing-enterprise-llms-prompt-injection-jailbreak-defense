import json
import os
import shutil
import tempfile
import unittest


class ExperimentSchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        # Create a temporary evidence directory for this test run.
        self.temp_dir = tempfile.mkdtemp(prefix="evidence_")
        self.prev_env = os.environ.get("BOOKMAS_EVIDENCE_DIR")
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.temp_dir

        # Execute the experiment script by importing run.py and calling main().
        import importlib

        run_module = importlib.import_module("run")
        run_module.main()

        self.results_path = os.path.join(self.temp_dir, "results.json")

    def tearDown(self) -> None:
        if self.prev_env is None:
            os.environ.pop("BOOKMAS_EVIDENCE_DIR", None)
        else:
            os.environ["BOOKMAS_EVIDENCE_DIR"] = self.prev_env
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _load_results(self) -> dict:
        self.assertTrue(os.path.isfile(self.results_path), "results.json not found")
        with open(self.results_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_results_file_exists_and_is_json(self) -> None:
        data = self._load_results()
        self.assertIsInstance(data, dict)

    def test_top_level_fields(self) -> None:
        data = self._load_results()

        # Check chapter and experiment_id
        self.assertEqual(data.get("chapter"), 4)
        self.assertEqual(data.get("experiment_id"), "exp-ch04-attack-harness-v1")

        # Check environment object
        env = data.get("environment")
        self.assertIsInstance(env, dict)
        self.assertIsInstance(env.get("os"), str)
        self.assertTrue(env.get("os"))
        self.assertIsInstance(env.get("python"), str)
        self.assertTrue(env.get("python"))

        # Check notes presence (optional string but should exist in our impl)
        notes = data.get("notes")
        self.assertIsInstance(notes, str)

    def test_runs_schema_and_metrics(self) -> None:
        data = self._load_results()

        runs = data.get("runs")
        self.assertIsInstance(runs, list)
        self.assertGreater(len(runs), 0)

        coverage = {}

        for run in runs:
            self.assertIn("variant", run)
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIn("metrics", run)

            variant = run["variant"]
            workload_id = run["workload_id"]
            run_id = run["run_id"]
            success = run["success"]
            metrics = run["metrics"]

            self.assertIn(variant, ("baseline", "treatment"))
            self.assertIsInstance(workload_id, str)
            self.assertIsInstance(run_id, str)
            self.assertIsInstance(success, bool)
            self.assertIsInstance(metrics, dict)

            for key, value in metrics.items():
                self.assertIsInstance(
                    value,
                    (int, float),
                    msg=f"Metric {key} should be numeric, got {type(value)}",
                )
                self.assertTrue(
                    value == value and value not in (float("inf"), float("-inf")),
                    msg=f"Metric {key} has non-finite value {value}",
                )

            coverage.setdefault(workload_id, set()).add(variant)

        # Ensure each workload has at least one baseline and one treatment run
        for workload_id, variants in coverage.items():
            self.assertIn("baseline", variants, msg=f"No baseline run for {workload_id}")
            self.assertIn("treatment", variants, msg=f"No treatment run for {workload_id}")

    def test_shared_metric_attack_success_rate_present(self) -> None:
        data = self._load_results()

        runs = data.get("runs")
        has_attack_success_rate = False
        for run in runs:
            metrics = run.get("metrics", {})
            if "attack_success_rate" in metrics:
                has_attack_success_rate = True
                self.assertIsInstance(metrics["attack_success_rate"], (int, float))
        self.assertTrue(has_attack_success_rate, "attack_success_rate metric missing from all runs")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
