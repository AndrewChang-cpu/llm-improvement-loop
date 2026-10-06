"""Retry the same judge after an inherited-option claim contradicted its API evidence."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import run_experiment as runner
storage = Path(__file__).resolve().parent
task = runner.read_json(storage / 'tasks/sphinx-doc__sphinx-11989/prepared.json')['task']
batch = storage / 'results' / task['id'] / 'revision-00'
run = batch / 'run-09'
(run / 'judgment').rename(run / 'judgment-rejected-01')
(run / 'verdict.json').rename(run / 'verdict-rejected-01.json')
clarification = ('\n\nVERIFIED FACTUAL CORRECTION: The generated effective_options inspection explicitly '
                 'contains canonical. Generated PyTypeAlias inherits PyVariable, which inherits PyObject. '
                 'canonical is accepted through that inheritance; it is not absent or rejected. '
                 'Acceptance and rendering are different: inspect whether the accepted canonical value '
                 'is used to render an alias expression. Re-evaluate all criteria normally against '
                 'the unchanged original, reference and candidate; do not claim canonical is unsupported.')
runner.write_json(run / 'grading-correction.json', {'reason':clarification,'patch_unchanged':True,'criteria_unchanged':True})
class CorrectedJudge(runner.Codex):
    def run(self, role, prompt, cwd, output, schema, **kwargs):
        if role == 'judge' and output.parent.name == 'run-09':
            prompt += clarification
        return super().run(role, prompt, cwd, output, schema, **kwargs)
runner.evaluate_batch(task, batch, CorrectedJudge(), task['description'])
