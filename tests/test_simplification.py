from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_experiment as runner
import simplify_specifications as simplification


def verdicts(passes):
    return [{"passed": i < passes, "generated": "generated",
             "criteria": [{"criterion": c, "passed": i < passes,
                           "evidence": ["feature.py:1"],
                           "deficiency": "" if i < passes else "Missing behavior"}
                          for c in runner.CRITERIA]} for i in range(10)]


class SimplificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "historical"
        self.source.mkdir()
        runner.write_json(self.source / "settings.json", {})
        self.settings = {"model": "fake", "task": {
            "id": "fixture", "base": "original", "reference": "reference",
            "requirements": dict(runner.CRITERIA)}}
        self.input = (self.root / "example", self.source, self.settings,
                      "word " * 100, {"runs": 20, "full_passes": 18})
        loader = patch.object(simplification, "load_experiment", return_value=self.input)
        loader.start()
        self.addCleanup(loader.stop)
        categories = patch.object(runner, "categories_from_docs", return_value={"Purpose": ["Goals"]})
        categories.start()
        self.addCleanup(categories.stop)
        self.output = self.root / "output"

    def test_accepts_exact_ten_percent_then_stops_on_regression_and_keeps_incumbent(self):
        with patch.object(runner, "Codex") as factory, patch.object(
                runner, "evaluate_batch", side_effect=[verdicts(10), verdicts(10), verdicts(9)]) as evaluate:
            factory.return_value.run.side_effect = [
                {"specification": "word " * 90, "changes": "Removed repetition"},
                {"specification": "word " * 81, "changes": "Shortened instructions"}]
            result = simplification.simplify("example", self.output)
            self.assertEqual(result["stop_reason"], "candidate_below_10_of_10")
            self.assertEqual(result["final_words"], 90)
            self.assertEqual(len(result["accepted_attempts"]), 1)
            self.assertEqual(evaluate.call_count, 3)
            self.assertEqual(simplification.word_count((self.output / "simplified-specification.md").read_text()), 90)
            self.assertTrue((self.output / "attempt-02/candidate-specification.md").exists())
            self.assertFalse((self.output / "confirmation").exists())
            evaluate.reset_mock()
            factory.return_value.run.reset_mock()
            self.assertEqual(simplification.simplify("example", self.output), result)
            evaluate.assert_not_called()
            factory.return_value.run.assert_not_called()
            self.settings["model"] = "changed"
            with self.assertRaisesRegex(ValueError, "inputs changed"):
                simplification.simplify("example", self.output)
            self.assertEqual(runner.read_json(self.output / "result.json"), result)

    def test_insufficient_reduction_stops_without_evaluating_candidate(self):
        with patch.object(runner, "Codex") as factory, patch.object(
                runner, "evaluate_batch", return_value=verdicts(10)) as evaluate:
            factory.return_value.run.return_value = {
                "specification": "word " * 91, "changes": "A small reduction"}
            result = simplification.simplify("example", self.output)
            self.assertEqual(result["stop_reason"], "reduction_below_10_percent")
            self.assertEqual(result["final_words"], 100)
            self.assertEqual(evaluate.call_count, 1)
            self.assertFalse((self.output / "attempt-01/batch.json").exists())

    def test_nine_pass_starting_batch_does_not_qualify_or_call_editor(self):
        with patch.object(runner, "Codex") as factory, patch.object(
                runner, "evaluate_batch", return_value=verdicts(9)) as evaluate:
            result = simplification.simplify("example", self.output)
            self.assertEqual(result["status"], "starting_specification_failed")
            self.assertIsNone(result["final_words"])
            factory.return_value.run.assert_not_called()
            self.assertEqual(evaluate.call_count, 1)
            self.assertFalse((self.output / "simplified-specification.md").exists())


if __name__ == "__main__":
    unittest.main()
