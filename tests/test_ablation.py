import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import analyze_specifications as analysis
import run_experiment as runner


class AblationTests(unittest.TestCase):
    def test_removal_preserves_other_sections_and_ignores_pseudocode_headings(self):
        text = "# Feature\n\n## Goals\nPurpose.\n```text\n## API contracts\nnot a section\n```\n## API contracts\nContract.\n### Details\nKeep this.\n"
        variants = analysis.section_variants(text, {"Goals", "API contracts"})
        self.assertEqual(list(variants), ["Goals", "API contracts"])
        self.assertEqual(variants["Goals"], "# Feature\n\n## API contracts\nContract.\n### Details\nKeep this.\n")
        self.assertIn("Purpose.", variants["API contracts"])
        self.assertNotIn("Keep this.", variants["API contracts"])

    def test_duplicate_or_unapproved_sections_are_rejected(self):
        for text in ("## Goals\na\n## Goals\nb\n", "## Goals\na\n## Bespoke\nb\n"):
            with self.assertRaises(ValueError):
                analysis.section_variants(text, {"Goals"})

    def test_aggregate_weights_prs_equally_and_excludes_partial_experiments(self):
        def entry(n, passed, control_n, control_passed):
            return {"status": "complete", "sections": ["Goals"],
                    "full_spec_results": {"runs": control_n, "full_passes": control_passed,
                                          "criterion_pass_counts": {c: control_passed for c in runner.CRITERIA}},
                    "ablations": {"Goals": {"runs": [{}] * n, "full_passes": passed,
                                             "criterion_pass_counts": {c: passed for c in runner.CRITERIA}}}}
        result = analysis.aggregate({"a": entry(1, 0, 20, 20), "b": entry(4, 4, 10, 9),
                                     "partial": {"status": "in_progress"}})
        goals = result["sections"]["Goals"]
        self.assertEqual(result["completed_experiments"], 2)
        self.assertEqual(goals["ablation_runs"], 5)
        self.assertEqual(goals["experiments_with_all_ablation_runs_passing"], 1)
        self.assertAlmostEqual(goals["mean_full_pass_rate_change"], -.45)

    def test_completed_analysis_skips_calls_and_changed_inputs_do_not_overwrite(self):
        root = Path(__file__).resolve().parents[1]
        experiment = root / ".experiments/sphinx-heading-reru"
        if not experiment.exists():
            self.skipTest("Pilot fixture is not present")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "shared.json"
            data = {"experiments": {}, "aggregate": {}}
            verdict = {"passed": True, "criteria": [{"criterion": c, "passed": True,
                       "evidence": ["file.py:1"], "deficiency": ""} for c in runner.CRITERIA]}
            with patch.object(runner, "evaluate_batch", return_value=[verdict]) as evaluate:
                analysis.analyze(str(experiment), data, output, Path(temporary), 1, "codex")
                self.assertEqual(evaluate.call_count, 11)
                self.assertTrue(all(call.kwargs["runs"] == 1 for call in evaluate.call_args_list))
                evaluate.reset_mock()
                analysis.analyze(str(experiment), data, output, Path(temporary), 1, "codex")
                evaluate.assert_not_called()
                before = output.read_bytes()
                with self.assertRaises(ValueError):
                    analysis.analyze(str(experiment), data, output, Path(temporary), 2, "codex")
                self.assertEqual(output.read_bytes(), before)
            self.assertEqual(json.loads(output.read_text())["aggregate"]["completed_experiments"], 1)


if __name__ == "__main__":
    unittest.main()
