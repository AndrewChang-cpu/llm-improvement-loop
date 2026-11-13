import fcntl
from datetime import datetime
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import batch_driver
import run_experiment as runner


PRECHECK = Path(__file__).resolve().parents[1] / ".experiments/batch-100/automation_precheck.py"
spec = importlib.util.spec_from_file_location("automation_precheck", PRECHECK)
automation_precheck = importlib.util.module_from_spec(spec)
spec.loader.exec_module(automation_precheck)


def concurrent_fixture(task, batch, model, codex, auto_retry, backend="codex"):
    os.setsid()
    batch_driver.BATCH = batch
    batch_driver.WORKER_TASK = task["id"]
    started = time.time()
    batch_driver.write_checkpoint("running", task["id"])
    time.sleep(0.3)
    runner.write_json(batch / "task-state" / task["id"] / "state.json", {
        "status": task.get("status", "converged"), "started": started, "finished": time.time()})


def command_fixture(folder):
    os.setsid()
    marker = str(folder / "terminated")
    ready = str(folder / "ready")
    script = ("import signal,time,pathlib,sys; "
              f"signal.signal(signal.SIGTERM, lambda *args: (pathlib.Path({marker!r}).touch(), sys.exit(0))); "
              f"pathlib.Path({ready!r}).touch(); time.sleep(60)")
    child = subprocess.Popen([sys.executable, "-c", script])
    child.wait()


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

    def test_test_output_instruction_preserves_legacy_prompts(self):
        for concise in (False, True):
            for phase in ("refinement", "simplification"):
                root = self.root / str(concise) / phase
                runner.write_json(root / "settings.json", {
                    "task": {"concise_test_output": True} if concise else {}})
                for role in ("generate", "judge", "edit", "simplify"):
                    output = root / "round-01" / role
                    def fake_run(*args, **kwargs):
                        runner.write_json(output / "response.json", {})
                        return SimpleNamespace(returncode=0)
                    with patch.object(runner.subprocess, "run", side_effect=fake_run):
                        batch_driver.BatchCodex().run(role, "original prompt", root, output, {})
                    prompt = runner.read_json(output / "request.json")["prompt"]
                    if concise:
                        self.assertIn("last 40 lines", prompt)
                        self.assertIn("exit status", prompt)
                        self.assertIn("mktemp", prompt)
                    else:
                        self.assertEqual(prompt, "original prompt")

    def test_precheck_skips_active_work_and_recovers_stale_setup(self):
        state = self.root / "checkpoint.json"
        lock_path = self.root / "batch.lock"
        def write(status, heartbeat):
            state.write_text(json.dumps({"automation_enabled": True, "status": status,
                                         "heartbeat_epoch": heartbeat}))
        write("setup", time.time())
        self.assertFalse(automation_precheck.should_run(state, lock_path))
        write("setup", time.time() - 3601)
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
        task_logs = self.root / "simplification/fixture/generation"
        task_logs.mkdir(parents=True)
        (task_logs / "events.jsonl").write_text(json.dumps({
            "type": "turn.failed", "error": {"message": "Usage limit; try again at 6:49 AM."}}) + "\n")
        error = RuntimeError(f"Codex failed (1); Logs: {task_logs}")
        result = batch_driver.failure_kind(error, "experiment")
        self.assertEqual(result, "waiting_quota")
        self.assertIn("6:49 AM", batch_driver.failure_details(error))

    def test_unrelated_old_quota_logs_do_not_hide_configuration_errors(self):
        (self.root / "stderr.log").write_text("usage limit")
        self.assertEqual(batch_driver.failure_kind(ValueError("Cached request differs"),
                                                  "prepare", self.root), "experiment_error")

    def test_quota_wait_uses_reset_time_with_buffer_and_midnight_rollover(self):
        now = datetime(2026, 11, 8, 6, 47).timestamp()
        self.assertEqual(batch_driver.quota_delay("try again at 6:49 AM.", now), 180)
        now = datetime(2026, 11, 8, 23, 59).timestamp()
        self.assertEqual(batch_driver.quota_delay("try again at 12:03 AM.", now), 300)
        self.assertEqual(batch_driver.quota_delay("usage limit", now), 3600)

    def test_network_backoff_is_persisted_and_sleep_is_interruptible(self):
        runner.write_json(self.root / "checkpoint.json", {"status": "waiting_retry"})
        for retry, seconds in [(0, 60), (1, 300), (2, 900), (5, 900)]:
            with self.subTest(retry=retry), \
                 patch.object(batch_driver, "BATCH", self.root), \
                 patch.object(batch_driver.time, "time", return_value=1000), \
                 patch.object(batch_driver.time, "sleep", side_effect=KeyboardInterrupt) as sleep:
                with self.assertRaises(KeyboardInterrupt):
                    batch_driver.wait_for_retry({"id": "fixture", "status": "waiting_retry"}, retry)
                checkpoint = runner.read_json(self.root / "checkpoint.json")
                self.assertEqual(checkpoint["retry_at_epoch"], 1000 + seconds)
                sleep.assert_called_once_with(60)

    def test_auto_retry_resumes_same_task_and_stops_on_unexpected_errors(self):
        tasks = [{"id": f"new-{number}"} for number in range(100)]
        runner.write_json(self.root / "runner-manifest.json", tasks)
        paused = {"id": "new-0", "status": "waiting_quota",
                  "failures": [{"details": "usage limit"}]}
        with patch.object(batch_driver, "BATCH", self.root), \
             patch.object(batch_driver, "install_read_only_github_auth"), \
             patch.object(batch_driver, "update_html") as html, \
             patch.object(batch_driver, "wait_for_retry") as wait, \
             patch.object(batch_driver, "run_task", side_effect=[paused, {"status": "converged"}]) as run, \
             patch("sys.argv", ["batch_driver.py", "--auto-retry", "--one-task"]):
            self.assertEqual(batch_driver.main(), 0)
            self.assertEqual(run.call_count, 2)
            self.assertEqual(run.call_args_list[0].args[0], run.call_args_list[1].args[0])
            wait.assert_called_once_with(paused, 0)
            self.assertEqual(html.call_count, 2)
        for status in ["waiting_auth", "experiment_error"]:
            with self.subTest(status=status), \
                 patch.object(batch_driver, "BATCH", self.root), \
                 patch.object(batch_driver, "install_read_only_github_auth"), \
                 patch.object(batch_driver, "update_html"), \
                 patch.object(batch_driver, "wait_for_retry") as wait, \
                 patch.object(batch_driver, "run_task", return_value={"status": status}), \
                 patch("sys.argv", ["batch_driver.py", "--auto-retry", "--parallel-prs", "1"]):
                self.assertEqual(batch_driver.main(), 1)
                wait.assert_not_called()

    def test_ctrl_c_saves_paused_checkpoint_without_reenabling_automation(self):
        runner.write_json(self.root / "runner-manifest.json", [{"id": f"new-{i}"} for i in range(100)])
        with patch.object(batch_driver, "BATCH", self.root), \
             patch.object(batch_driver, "install_read_only_github_auth"), \
             patch.object(batch_driver, "update_html"), \
             patch.object(batch_driver, "run_task", side_effect=KeyboardInterrupt), \
             patch("sys.argv", ["batch_driver.py", "--auto-retry", "--parallel-prs", "1"]):
            self.assertEqual(batch_driver.main(), 130)
        checkpoint = runner.read_json(self.root / "checkpoint.json")
        self.assertEqual(checkpoint["status"], "paused")
        self.assertFalse(checkpoint["automation_enabled"])

    def test_parallel_scheduler_limits_concurrency_and_skips_saved_tasks(self):
        tasks = [{"id": f"fixture-{i}"} for i in range(5)]
        runner.write_json(self.root / "task-state/fixture-0/state.json", {"status": "converged"})
        args = SimpleNamespace(parallel_prs=2, model="unused", codex="unused", auto_retry=True, backend="codex")
        with patch.object(batch_driver, "BATCH", self.root), \
             patch.object(batch_driver, "run_worker", concurrent_fixture), \
             patch.object(batch_driver, "update_html"):
            self.assertEqual(batch_driver.run_parallel(tasks, args), 0)
        self.assertFalse((self.root / "task-state/fixture-0/checkpoint.json").exists())
        events = []
        for task in tasks[1:]:
            state = runner.read_json(self.root / "task-state" / task["id"] / "state.json")
            events += [(state["started"], 1), (state["finished"], -1)]
            checkpoint = runner.read_json(self.root / "task-state" / task["id"] / "checkpoint.json")
            self.assertEqual(checkpoint["active_task"], task["id"])
        count = maximum = 0
        for _, change in sorted(events):
            count += change
            maximum = max(maximum, count)
        self.assertEqual(maximum, 2)
        self.assertEqual(runner.read_json(self.root / "checkpoint.json")["status"], "complete")

    def test_worker_retries_without_writing_global_checkpoint(self):
        runner.write_json(self.root / "checkpoint.json", {"status": "parent-owned"})
        paused = {"status": "waiting_retry", "id": "fixture"}
        with patch.object(batch_driver, "BATCH", self.root), \
             patch.object(batch_driver, "WORKER_TASK", None), \
             patch.object(batch_driver.os, "setsid"), \
             patch.object(batch_driver, "run_task", side_effect=[paused, {"status": "converged"}]), \
             patch.object(batch_driver, "wait_for_retry") as wait:
            batch_driver.run_worker({"id": "fixture"}, self.root, "unused", "unused", True)
            wait.assert_called_once_with(paused, 0)
            batch_driver.write_checkpoint("running", "fixture")
        self.assertEqual(runner.read_json(self.root / "checkpoint.json")["status"], "parent-owned")
        self.assertEqual(runner.read_json(self.root / "task-state/fixture/checkpoint.json")["status"], "running")

    def test_parallel_scheduler_pauses_on_error_without_starting_more_tasks(self):
        tasks = [{"id": f"fixture-{i}", "status": "experiment_error"} for i in range(4)]
        args = SimpleNamespace(parallel_prs=2, model="unused", codex="unused", auto_retry=True, backend="codex")
        with patch.object(batch_driver, "BATCH", self.root), \
             patch.object(batch_driver, "run_worker", concurrent_fixture), \
             patch.object(batch_driver, "update_html"):
            self.assertEqual(batch_driver.run_parallel(tasks, args), 1)
        self.assertFalse((self.root / "task-state/fixture-2").exists())
        self.assertEqual(runner.read_json(self.root / "checkpoint.json")["status"], "paused")

    def test_stop_workers_stops_descendant_commands(self):
        process = multiprocessing.get_context("spawn").Process(target=command_fixture, args=(self.root,))
        process.start()
        try:
            deadline = time.monotonic() + 10
            while not (self.root / "ready").exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue((self.root / "ready").exists())
            batch_driver.stop_workers({"fixture": process})
            self.assertFalse(process.is_alive())
            self.assertTrue((self.root / "terminated").exists())
        finally:
            batch_driver.stop_workers({"fixture": process})

    def test_parallel_ctrl_c_stops_workers_and_saves_pause(self):
        tasks = [{"id": f"fixture-{i}"} for i in range(3)]
        args = SimpleNamespace(parallel_prs=2, model="unused", codex="unused", auto_retry=True, backend="codex")
        original_children = {child.pid for child in multiprocessing.active_children()}
        with patch.object(batch_driver, "BATCH", self.root), \
             patch.object(batch_driver, "run_worker", concurrent_fixture), \
             patch.object(batch_driver.time, "sleep", side_effect=KeyboardInterrupt):
            self.assertEqual(batch_driver.run_parallel(tasks, args), 130)
        checkpoint = runner.read_json(self.root / "checkpoint.json")
        self.assertEqual(checkpoint["status"], "paused")
        self.assertEqual(checkpoint["active_tasks"], [])
        self.assertEqual({child.pid for child in multiprocessing.active_children()}, original_children)

    def test_partial_generated_code_is_archived_before_retry(self):
        lane = self.root / "results/fixture/revision-01/run-00"
        generated = lane / "generated"
        generated.mkdir(parents=True)
        (generated / "existing.py").write_text("old\n")
        runner.initialize_git(generated)
        (generated / "existing.py").write_text("changed\n")
        (generated / "new.py").write_text("partial feature\n")
        call = lane / "generation"
        call.mkdir()
        (call / "events.jsonl").write_text('{"type":"turn.failed"}\n')
        with patch.object(batch_driver, "BATCH", self.root):
            batch_driver.archive_partial_generations("fixture")
        archive = call / "incomplete-attempts/attempt-001"
        self.assertIn(b"+changed", (archive / "partial-patch.diff").read_bytes())
        self.assertEqual((archive / "untracked/new.py").read_text(), "partial feature\n")
        self.assertTrue((archive / "events.jsonl").exists())
        self.assertFalse((call / "events.jsonl").exists())

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
