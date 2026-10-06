"""Pause between phases so the supervising Codex session can inspect artifacts."""
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import run_experiment as runner

storage = Path(__file__).resolve().parent


def checkpoint(directory, phase):
    request = directory / (phase + "-review.json")
    approval = directory / (phase + "-review-approved.json")
    runner.write_json(request, {"phase": phase, "artifacts": str(directory)})
    print("REVIEW " + str(request), flush=True)
    while not approval.exists():
        time.sleep(1)
    if not runner.read_json(approval)["approved"]:
        raise RuntimeError("Supervising session rejected this phase; stop for correction.")


evaluate = runner.evaluate_batch


def reviewed_batch(task, output, agent, specification):
    results = evaluate(task, output, agent, specification)
    checkpoint(output, "batch")
    return results


runner.evaluate_batch = reviewed_batch


class SupervisedCodex(runner.Codex):
    def run(self, role, prompt, cwd, output, schema, **kwargs):
        response = super().run(role, prompt, cwd, output, schema, **kwargs)
        if role == "edit":
            checkpoint(output, "editor")
        return response


agent = SupervisedCodex()
for task in runner.read_json(ROOT / "experiments/pilot.json"):
    prepared = runner.prepare_task(task, storage)
    result = runner.run_task(prepared, storage / "results" / task["id"], agent,
                             runner.categories_from_docs())
    print(json.dumps(result), flush=True)
    if result["status"] != "converged":
        break
runner.make_audit(storage)
