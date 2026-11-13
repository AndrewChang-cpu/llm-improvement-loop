"""Restart the two approved PRs, then simplify each qualifying specification."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import run_experiment as runner
import simplify_specifications as simplifier

OUTPUT = Path(__file__).resolve().parent
PAIRS = [('sphinx-heading-reru', 'sphinx-doc__sphinx-11989'),
         ('seaborn-heading-run', 'mwaskom__seaborn-3063')]


def snapshot_hash(directory):
    digest = hashlib.sha256()
    for folder, dirs, files in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache'})
        for name in sorted(files):
            path = Path(folder) / name
            digest.update(str(path.relative_to(directory)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


summary = {}
for previous, task_id in PAIRS:
    experiment = OUTPUT / previous.replace('-heading-reru', '-restart').replace('-heading-run', '-restart')
    source = ROOT / '.experiments' / previous / 'results' / task_id / 'settings.json'
    task = runner.read_json(source)['task']
    before = {role: snapshot_hash(Path(task[role])) for role in ['base', 'reference']}
    runner.write_json(experiment / 'snapshot-integrity-before.json', before)
    # Reuse the frozen environments, but validate the reference before spending model calls.
    env = runner.clean_env()
    env.update(PYTHONPATH=task['reference'], PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
               MPLBACKEND='Agg', PYTHONDONTWRITEBYTECODE='1')
    preflight = []
    for command in task['checks']:
        result = subprocess.run(command, cwd=task['reference'], env=env, capture_output=True, text=True)
        preflight.append({'command': command, 'returncode': result.returncode,
                          'output': result.stdout + result.stderr})
    runner.write_json(experiment / 'reference-preflight.json', preflight)
    if any(check['returncode'] for check in preflight):
        raise RuntimeError(f'Reference environment failed: {task_id}')
    print(f'Starting {task_id} from PR baseline', flush=True)
    result = runner.run_task(task, experiment / 'results' / task_id,
                             runner.Codex(), runner.categories_from_docs())
    summary[task_id] = {'experiment': str(experiment), 'refinement': result}
    if before != {role: snapshot_hash(Path(task[role])) for role in before}:
        raise RuntimeError(f'Frozen snapshot changed: {task_id}')
    if result['status'] == 'converged':
        summary[task_id]['simplification'] = simplifier.simplify(
            str(experiment), experiment / 'simplification')
    after = {role: snapshot_hash(Path(task[role])) for role in before}
    runner.write_json(experiment / 'snapshot-integrity-after.json', after)
    if before != after:
        raise RuntimeError(f'Frozen snapshot changed: {task_id}')
    runner.write_json(OUTPUT / 'summary.json', summary)
    print(json.dumps(summary[task_id], indent=2), flush=True)
print('Both approved experiments finished.', flush=True)
