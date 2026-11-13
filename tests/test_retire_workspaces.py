from pathlib import Path
import tempfile
import unittest

import run_experiment as runner
import retire_workspaces


class RetireWorkspacesTests(unittest.TestCase):
    def test_only_judged_runs_lose_repository_copies(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / "tasks/fixture/base"
            base.mkdir(parents=True)
            (base / "feature.py").write_text("value = 0\n")
            output = root / "results/fixture"
            runner.write_json(output / "settings.json", {"task": {"base": str(base)}})
            runs = {}
            for name, judged in (("run-00", True), ("run-01", False)):
                run = output / "revision-00" / name
                runner.fresh_workspace(base, run / "generated")
                (run / "generated/feature.py").write_text("value = 1\n")
                runner.command(["git", "add", "-A"], run / "generated", runner.clean_env())
                (run / "patch.diff").write_text(runner.command(
                    ["git", "diff", "--cached", "--binary"], run / "generated", runner.clean_env()))
                (run / "evaluation").mkdir()
                runner.write_json(run / "checks.json", {})
                if judged:
                    runner.write_json(run / "verdict.json", {})
                runs[name] = run
            for task, run in retire_workspaces.judged_runs(root):
                retire_workspaces.retire(task, run, root / "log.jsonl")
            self.assertFalse((runs["run-00"] / "generated").exists())
            self.assertFalse((runs["run-00"] / "evaluation").exists())
            self.assertTrue((runs["run-01"] / "generated").exists())
            self.assertTrue((runs["run-01"] / "evaluation").exists())
            self.assertTrue((base / "feature.py").exists())
            self.assertIn('"generated": "rebuilt"', (root / "log.jsonl").read_text())


if __name__ == "__main__":
    unittest.main()
