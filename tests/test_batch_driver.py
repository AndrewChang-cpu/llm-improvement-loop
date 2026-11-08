import fcntl
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import batch_driver
import run_experiment as runner


PRECHECK = Path(__file__).resolve().parents[1] / ".experiments/batch-100/automation_precheck.py"
spec = importlib.util.spec_from_file_location("automation_precheck", PRECHECK)
automation_precheck = importlib.util.module_from_spec(spec)
spec.loader.exec_module(automation_precheck)


class BatchDriverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_manifest_rejects_duplicate_and_pilot_ids(self):
        tasks = [{"id": f"new-{number}"} for number in range(100)]
        batch_driver.validate_manifest(tasks)
        with self.assertRaises(ValueError):
            batch_driver.validate_manifest(tasks[:-1] + [tasks[0]])
        with self.assertRaises(ValueError):
            batch_driver.validate_manifest(tasks[:-1] + [{"id": "mwaskom__seaborn-3063"}])

    def test_precheck_skips_active_work_and_recovers_stale_setup(self):
        state = self.root / "checkpoint.json"
        lock_path = self.root / "batch.lock"
        def write(status, heartbeat):
            state.write_text(json.dumps({"automation_enabled": True, "status": status,
                                         "heartbeat_epoch": heartbeat}))
        write("setup", time.time())
        self.assertFalse(automation_precheck.should_run(state, lock_path))
        write("setup", time.time() - 7201)
        self.assertTrue(automation_precheck.should_run(state, lock_path))
        write("waiting_quota", time.time())
        self.assertTrue(automation_precheck.should_run(state, lock_path))
        with lock_path.open("a") as active:
            fcntl.flock(active, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertFalse(automation_precheck.should_run(state, lock_path))
            fcntl.flock(active, fcntl.LOCK_UN)

    def test_driver_refuses_a_second_batch_while_lock_is_held(self):
        tasks = [{"id": f"new-{number}"} for number in range(100)]
        runner.write_json(self.root / "runner-manifest.json", tasks)
        lock_path = self.root / "batch.lock"
        with lock_path.open("a") as active, \
             patch.object(batch_driver, "BATCH", self.root), \
             patch.object(batch_driver, "install_read_only_github_auth"), \
             patch("sys.argv", ["batch_driver.py"]):
            fcntl.flock(active, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(batch_driver.main(), 2)
            fcntl.flock(active, fcntl.LOCK_UN)

    def test_preparation_failure_is_persisted_separately(self):
        checkpoint = {"automation_enabled": True, "status": "setup"}
        (self.root / "checkpoint.json").write_text(json.dumps(checkpoint))
        with patch.object(batch_driver, "BATCH", self.root), \
             patch.object(runner, "prepare_task", side_effect=RuntimeError("invalid base commit")):
            state = batch_driver.run_task({"id": "fixture"}, runner.Codex(executable="unused"), {})
        self.assertEqual(state["status"], "prep_failed_permanent")
        saved = json.loads((self.root / "task-state/fixture/state.json").read_text())
        self.assertEqual(saved["status"], "prep_failed_permanent")
        self.assertIn("invalid base commit", saved["failures"][0]["error"])

    def test_quota_failure_is_retryable(self):
        task_logs = self.root / "results/fixture"
        task_logs.mkdir(parents=True)
        (task_logs / "stderr.log").write_text("The usage limit has been reached")
        result = batch_driver.failure_kind(RuntimeError("Codex failed (1)"), "experiment", task_logs)
        self.assertEqual(result, "waiting_quota")

    def test_completed_lanes_reuse_saved_verdicts(self):
        output = self.root / "batch"
        expected = []
        for number in range(10):
            run = output / f"run-{number:02d}"
            run.mkdir(parents=True)
            verdict = {"passed": number % 2 == 0, "lane": number}
            runner.write_json(run / "verdict.json", verdict)
            expected.append(verdict)

        class NoCalls:
            def run(self, *args, **kwargs):
                raise AssertionError("completed lane was rerun")

        actual = runner.evaluate_batch({}, output, NoCalls(), "specification")
        self.assertEqual(actual, expected)
        self.assertEqual(json.loads((output / "batch.json").read_text())["passes"], 5)
