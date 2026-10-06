"""Re-evaluate one inconsistent convention judgment without changing its patch."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import run_experiment as runner

storage = Path(__file__).resolve().parent
prepared = runner.read_json(storage / 'tasks/sphinx-doc__sphinx-11989/prepared.json')
task = prepared['task']
batch = storage / 'results' / task['id'] / 'revision-01'
run = batch / 'run-04'
# Preserve the original model judgment and the reason for the bounded retry.
(run / 'judgment').rename(run / 'judgment-rejected-01')
(run / 'verdict.json').rename(run / 'verdict-rejected-01.json')
clarification = ('\n\nVERIFIED REPOSITORY CONVENTION EVIDENCE: Original doc/internals/contributing.rst '
                 'lines 117-118 and 145-146 require CHANGES.rst updates for non-trivial features; '
                 'lines 148-151 say new features should be documented. The merged reference changes '
                 'CHANGES.rst and doc/usage/domains/python.rst. This candidate patch changes only '
                 'sphinx/domains/python/__init__.py and tests/test_domains/test_domain_py.py; '
                 'it adds no user documentation or changelog. Inspect these sources and assess '
                 'convention_fit consistently with that existing repository policy. Evaluate '
                 'all other criteria normally; acceptance of code is not determined by matching '
                 'reference implementation text.')
runner.write_json(run / 'grading-correction.json', {'reason': clarification, 'patch_unchanged': True, 'criteria_unchanged': True})

class CorrectedJudge(runner.Codex):
    def run(self, role, prompt, cwd, output, schema, **kwargs):
        if role == 'judge' and output.parent.name == 'run-04':
            prompt += clarification
        return super().run(role, prompt, cwd, output, schema, **kwargs)

specification = runner.read_json(batch.parent / 'revision-00/editing/response.json')['specification']
runner.evaluate_batch(task, batch, CorrectedJudge(), specification)
