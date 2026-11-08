"""Resume saved Seaborn refinement, then use the approved three-candidate search."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import run_experiment as runner


def snapshot_hash(directory):
    digest = hashlib.sha256()
    for folder, dirs, files in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache'})
        for name in sorted(files):
            path = Path(folder) / name
            digest.update(str(path.relative_to(directory)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


experiment = Path(__file__).resolve().parent / 'seaborn-restart'
source = experiment / 'results/mwaskom__seaborn-3063'
settings = runner.read_json(source / 'settings.json')
task = settings['task']
before = runner.read_json(experiment / 'snapshot-integrity-before.json')
current = {role: snapshot_hash(Path(task[role])) for role in before}
if current != before:
    raise RuntimeError('Frozen Seaborn inputs changed during pause')
# Completed lane verdicts are reused; no manual judge replacement or retry.
result = runner.run_task(task, source, runner.Codex(settings['model']), runner.categories_from_docs())
runner.write_json(experiment / 'resumed-refinement-result.json', result)
if result['status'] == 'converged':
    subprocess.run([sys.executable, str(ROOT / 'simplify_specifications.py'), str(experiment),
                    '--output', str(ROOT / '.experiments/simplification-three-candidates-2026-11-07')], check=True)
after = {role: snapshot_hash(Path(task[role])) for role in before}
runner.write_json(experiment / 'snapshot-integrity-after.json', after)
if before != after:
    raise RuntimeError('Frozen Seaborn inputs changed')
print('Seaborn finished.', flush=True)
