"""Supplemental validation of candidate-owned tests before gold-test overlay."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys

storage = Path(__file__).resolve().parent
task = json.loads((storage / "tasks" / sys.argv[1] / "prepared.json").read_text())["task"]
batch = Path(sys.argv[2]).resolve()


def validate(run):
    candidate = run / "generated"
    changed = subprocess.check_output(["git", "diff", "--cached", "--name-only"],
                                      cwd=candidate, text=True).splitlines()
    # Include original targeted modules and every changed candidate test module.
    paths = task["checks"][0][4:] + [path for path in changed
            if path.startswith("tests/") and Path(path).name.startswith("test_") and path.endswith(".py")]
    tests = sorted({path for path in paths if (candidate / path.split("::")[0]).exists()})
    env = os.environ.copy()
    env.update(PYTHONPATH=str(candidate), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", MPLBACKEND="Agg")
    args = [task["generator_python"], "-m", "pytest", "-q", "--basetemp",
            str(run / "candidate-test-tmp")] + tests
    result = subprocess.run(args, cwd=candidate, env=env, text=True, capture_output=True)
    record = {"command": args, "returncode": result.returncode,
              "output": result.stdout + result.stderr}
    (run / "candidate-test-validation.json").write_text(json.dumps(record, indent=2) + "\n")
    return {"run": run.name, "returncode": result.returncode,
            "summary": "\n".join(record["output"].splitlines()[-3:])}


with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(validate, sorted(batch.glob("run-*"))))
print(json.dumps(results, indent=2))
sys.exit(0 if all(result["returncode"] == 0 for result in results) else 1)
