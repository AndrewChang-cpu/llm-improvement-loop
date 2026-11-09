from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import analyze_specifications as analysis
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

    def test_load_experiment_accepts_a_single_task_directory(self):
        task_dir = self.root / "direct-task"
        (task_dir / "revision-00").mkdir(parents=True)
        for name in ("base", "reference", "generator"):
            (task_dir / name).mkdir()
        specification = "# Purpose\nImplement the feature.\n"
        (task_dir / "comprehensive-specification.md").write_text(specification)
        (task_dir / "revision-00/specification.md").write_text(specification)
        rows = [{"criterion": criterion, "passed": True, "evidence": ["feature.py:1"],
                 "deficiency": ""} for criterion in runner.CRITERIA]
        runner.write_json(task_dir / "settings.json", {
            "confirmation": False,
            "task": {"id": "fixture", "base": str(task_dir / "base"),
                     "reference": str(task_dir / "reference"),
                     "generator_python": str(task_dir / "generator"),
                     "requirements": dict(runner.CRITERIA)},
            "model": "fake"})
        runner.write_json(task_dir / "result.json", {"status": "converged", "revision": 0})
        runner.write_json(task_dir / "revision-00/batch.json", {"runs": [
            {"passed": True, "criteria": rows} for _ in range(10)]})

        directory, source, _, loaded, historical = analysis.load_experiment(task_dir)

        self.assertEqual(directory, task_dir.resolve())
        self.assertEqual(source, task_dir.resolve())
        self.assertEqual(loaded, specification)
        self.assertEqual(historical["full_passes"], 10)

    def test_current_protocol_reuses_qualifying_batch_without_confirmation(self):
        self.settings.update(required_passes=10, confirmation=False, effort="low")
        runner.write_json(self.source / "result.json", {"revision": 2})
        runner.write_json(self.source / "revision-02/batch.json", {"runs": verdicts(10)})
        with patch.object(runner, "Codex") as factory, patch.object(runner, "evaluate_batch") as evaluate:
            factory.return_value.run.return_value = {
                "specification": "word " * 95, "changes": "Removed repetition"}
            result = simplification.simplify("example", self.output)
            self.assertEqual(result["stop_reason"], "no_qualifying_candidate")
            self.assertEqual(result["starting_results"]["full_passes"], 10)
            evaluate.assert_not_called()
            self.assertTrue((self.output / "starting-batch-source.json").exists())

    def test_effort_override_requires_fresh_qualifying_batch(self):
        self.settings.update(required_passes=10, confirmation=False, effort="low")
        with patch.object(runner, "Codex") as factory, patch.object(
                runner, "evaluate_batch", return_value=verdicts(9)) as evaluate:
            result = simplification.simplify("example", self.output, effort="medium")
            factory.assert_called_once_with("fake", None, "codex", "medium")
            evaluate.assert_called_once()
            self.assertEqual(result["stop_reason"], "starting_batch_below_10_of_10")
            self.assertEqual(runner.read_json(self.output / "settings.json")["effort"], "medium")

    def test_selects_shortest_passing_candidate_then_stops_and_resumes(self):
        with patch.object(runner, "Codex") as factory, patch.object(
                runner, "evaluate_batch", side_effect=[verdicts(n) for n in [10, 10, 9, 10, 9, 9, 9]]) as evaluate:
            factory.return_value.run.side_effect = [
                {"specification": "word " * n, "changes": "Removed repetition"}
                for n in [90, 70, 80, 72, 56, 60]]
            result = simplification.simplify("example", self.output)
            self.assertEqual(result["stop_reason"], "no_qualifying_candidate")
            self.assertEqual(result["final_words"], 80)
            self.assertEqual(len(result["accepted_rounds"]), 1)
            self.assertEqual(result["accepted_rounds"][0]["selected_candidate"], 3)
            self.assertEqual(evaluate.call_count, 7)
            self.assertEqual(simplification.word_count((self.output / "simplified-specification.md").read_text()), 80)
            self.assertFalse((self.output / "confirmation").exists())
            calls = factory.return_value.run.call_args_list
            self.assertEqual([call.args[1] for call in calls[:3]], [calls[0].args[1]] * 3)
            for i, call in enumerate(calls):
                feedback = runner.read_json(call.args[2] / "feedback.json")
                self.assertEqual(simplification.word_count(feedback["current_specification"]), 100 if i < 3 else 80)
            evaluate.reset_mock()
            factory.return_value.run.reset_mock()
            self.assertEqual(simplification.simplify("example", self.output), result)
            evaluate.assert_not_called()
            factory.return_value.run.assert_not_called()
            self.settings["model"] = "changed"
            with self.assertRaisesRegex(ValueError, "inputs changed"):
                simplification.simplify("example", self.output)
            self.assertEqual(runner.read_json(self.output / "result.json"), result)

    def test_both_out_of_range_bounds_skip_evaluation(self):
        with patch.object(runner, "Codex") as factory, patch.object(
                runner, "evaluate_batch", return_value=verdicts(10)) as evaluate:
            factory.return_value.run.side_effect = [
                {"specification": "word " * n, "changes": "A reduction"} for n in [91, 69, 65]]
            result = simplification.simplify("example", self.output)
            self.assertEqual(result["stop_reason"], "no_qualifying_candidate")
            self.assertEqual(result["final_words"], 100)
            self.assertEqual(evaluate.call_count, 1)
            self.assertFalse(any(c["length_passed"] for c in result["last_round"]["candidates"]))

    def test_word_bounds_round_inward(self):
        self.input = (*self.input[:3], "word " * 101, self.input[4])
        with patch.object(simplification, "load_experiment", return_value=self.input), patch.object(
                runner, "Codex") as factory, patch.object(
                runner, "evaluate_batch", side_effect=[verdicts(10), verdicts(9)]) as evaluate:
            factory.return_value.run.side_effect = [
                {"specification": "word " * n, "changes": "A reduction"} for n in [70, 91, 71]]
            result = simplification.simplify("example", self.output)
            self.assertEqual([c["length_passed"] for c in result["last_round"]["candidates"]], [False, False, True])
            self.assertEqual(evaluate.call_count, 2)

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
