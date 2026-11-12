import json
import os
import unittest
from pathlib import Path


class TestExperimentEvidenceSchema(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure evidence file exists; if not, this test suite expects
        # that run.py has been executed before running tests.
        self.evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
        self.evidence_path = Path(self.evidence_dir) / "results.json"

    def test_evidence_file_exists(self) -> None:
        self.assertTrue(
            self.evidence_path.exists(),
            msg=(
                "Evidence file /evidence/results.json does not exist. "
                "Run `python run.py` before running tests."
            ),
        )

    def _load_evidence(self):
        with self.evidence_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def test_top_level_schema(self) -> None:
        data = self._load_evidence()
        self.assertIsInstance(data, dict)
        self.assertIn("chapter", data)
        self.assertEqual(data["chapter"], 10)
        self.assertIn("experiment_id", data)
        self.assertEqual(
            data["experiment_id"],
            "exp-10-architecting-least-privilege-blast-radius-reduction",
        )
        self.assertIn("environment", data)
        self.assertIsInstance(data["environment"], dict)
        self.assertIn("os", data["environment"])
        self.assertIn("python", data["environment"])
        self.assertIn("runs", data)
        self.assertIsInstance(data["runs"], list)

    def test_runs_have_required_fields_and_numeric_metrics(self) -> None:
        data = self._load_evidence()
        runs = data["runs"]
        self.assertGreaterEqual(len(runs), 1)

        for run in runs:
            self.assertIn("variant", run)
            self.assertIn(run["variant"], ("baseline", "treatment"))
            self.assertIn("workload_id", run)
            self.assertIsInstance(run["workload_id"], str)
            self.assertIn("run_id", run)
            self.assertIsInstance(run["run_id"], str)
            self.assertIn("success", run)
            self.assertIsInstance(run["success"], bool)
            self.assertIn("metrics", run)
            self.assertIsInstance(run["metrics"], dict)
            # All metric values must be numbers
            for key, value in run["metrics"].items():
                with self.subTest(metric=key):
                    self.assertIsInstance(
                        value,
                        (int, float),
                        msg=f"Metric {key} is not numeric: {type(value)}",
                    )

    def test_at_least_one_baseline_and_treatment_per_workload(self) -> None:
        data = self._load_evidence()
        runs = data["runs"]
        workloads = {}
        for run in runs:
            wid = run["workload_id"]
            var = run["variant"]
            workloads.setdefault(wid, set()).add(var)

        # Expect all four workloads present
        expected_ids = {
            "wl1-honest-support-agent-queries",
            "wl2-cross-tenant-data-exfiltration",
            "wl3-sensitive-field-exfiltration-same-tenant",
            "wl4-tool-abuse-and-stateful-compromise",
        }
        self.assertTrue(expected_ids.issubset(set(workloads.keys())))

        for wid in expected_ids:
            self.assertIn(wid, workloads)
            variants = workloads[wid]
            self.assertIn("baseline", variants)
            self.assertIn("treatment", variants)


if __name__ == "__main__":
    unittest.main()
