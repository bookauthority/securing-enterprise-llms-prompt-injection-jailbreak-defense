import json
import os
import unittest
import tempfile
import shutil


class ExperimentEvidenceSchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        # Run the experiment into a temporary evidence dir.
        self.tmpdir = tempfile.mkdtemp(prefix="evidence-")
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.tmpdir

        # Import run after setting env var so it picks up the right dir.
        import run as experiment_run  # type: ignore

        # Execute main() to generate results.json
        experiment_run.main()

        self.results_path = os.path.join(self.tmpdir, "results.json")
        self.assertTrue(os.path.exists(self.results_path), "results.json was not created")

        with open(self.results_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        os.environ.pop("BOOKMAS_EVIDENCE_DIR", None)

    def test_top_level_schema(self) -> None:
        d = self.data
        self.assertIsInstance(d, dict)
        self.assertEqual(d.get("chapter"), 11)
        self.assertEqual(d.get("experiment_id"), "exp-llm-sec-011-ci-benchmarks-v1")

        env = d.get("environment")
        self.assertIsInstance(env, dict)
        self.assertIn("os", env)
        self.assertIn("python", env)

        self.assertIn("runs", d)
        self.assertIsInstance(d["runs"], list)
        self.assertGreaterEqual(len(d["runs"]), 2)

    def test_runs_schema_and_metrics(self) -> None:
        runs = self.data["runs"]

        # Collect workload/variant pairs to ensure coverage
        seen = {}
        for run in runs:
            self.assertIsInstance(run, dict)
            variant = run.get("variant")
            workload_id = run.get("workload_id")
            run_id = run.get("run_id")
            self.assertIn(variant, ("baseline", "treatment"))
            self.assertIsInstance(workload_id, str)
            self.assertIsInstance(run_id, str)

            key = (workload_id, variant)
            seen[key] = True

            # success must be bool
            self.assertIn("success", run)
            self.assertIsInstance(run["success"], bool)

            # metrics must exist and contain only numeric values
            metrics = run.get("metrics")
            self.assertIsInstance(metrics, dict)
            self.assertGreaterEqual(len(metrics), 1)
            for m_name, m_value in metrics.items():
                self.assertIsInstance(
                    m_value,
                    (int, float),
                    msg=f"Metric {m_name} must be numeric, got {type(m_value)}",
                )

        # Expected workloads from the harness
        expected_workloads = {
            "prompt_injection_suite_v1",
            "jailbreak_suite_v1",
            "variance_sensitivity_workload",
        }

        for wid in expected_workloads:
            self.assertIn((wid, "baseline"), seen, f"Missing baseline run for {wid}")
            self.assertIn((wid, "treatment"), seen, f"Missing treatment run for {wid}")


class MetricsModuleTest(unittest.TestCase):
    def test_attack_rate_and_ci_width_simple(self) -> None:
        from llm_sec_harness.metrics import attack_rate_and_ci_width

        # All failures -> rate 0.0, width 0.0
        rate, width = attack_rate_and_ci_width([False, False, False])
        self.assertAlmostEqual(rate, 0.0)
        self.assertAlmostEqual(width, 0.0)

        # All successes -> rate 1.0, width 0.0
        rate, width = attack_rate_and_ci_width([True, True, True])
        self.assertAlmostEqual(rate, 1.0)
        self.assertAlmostEqual(width, 0.0)

        # Mixed outcomes
        rate, width = attack_rate_and_ci_width([True, False, True, False])
        self.assertAlmostEqual(rate, 0.5)
        self.assertGreater(width, 0.0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
