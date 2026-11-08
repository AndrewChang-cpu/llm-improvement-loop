import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import view_experiment as viewer


class ViewerTests(unittest.TestCase):
    def test_candidates_use_round_input_and_preserve_partial_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'settings.json').write_text(json.dumps({'task': {'id': 'example'}}))
            for number, spec in [(1, 'First proposal\n'), (2, 'Second proposal\n')]:
                candidate = root / 'round-01' / f'candidate-{number:02d}'
                candidate.mkdir(parents=True)
                (candidate / 'current-specification.md').write_text('Shared incumbent\n')
                (candidate / 'candidate-specification.md').write_text(spec)
                run = candidate / 'run-00'
                run.mkdir()
                (run / 'verdict.json').write_text(json.dumps({'criteria': [
                    {'criterion': key, 'passed': number == 1} for key in viewer.CRITERIA
                ]}))
            first = root / 'round-01/candidate-01'
            (first / 'batch.json').write_text('{}')
            (first / 'decision.json').write_text(json.dumps({'accepted': True}))

            result = viewer.load_simplification(root)
            retained, partial = result['revisions']
            self.assertEqual(retained['status'], 'Retained')
            self.assertEqual((retained['passes'], retained['judged']), (1, 1))
            self.assertTrue(retained['complete'])
            self.assertEqual(partial['label'], 'R1 C2')
            self.assertEqual(partial['status'], 'Pending')
            self.assertEqual((partial['passes'], partial['judged']), (0, 1))
            self.assertFalse(partial['complete'])
            self.assertIn('-Shared incumbent', partial['changes'])
            self.assertNotIn('-First proposal', partial['changes'])

    def test_report_includes_both_phases_and_exact_specification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'results/example/revision-00'
            source.mkdir(parents=True)
            spec = 'Allow values < 10; never render </script> as markup.\n'
            (source / 'specification.md').write_text(spec)
            shortened = root / 'simplification'
            candidate = shortened / 'round-01/candidate-01'
            candidate.mkdir(parents=True)
            (shortened / 'settings.json').write_text(json.dumps({'task': {'id': 'example'}}))
            (candidate / 'candidate-specification.md').write_text(spec)
            (candidate / 'current-specification.md').write_text('Original\n')
            with patch('sys.argv', ['view_experiment.py', str(root), '--simplification', str(shortened)]):
                viewer.main()
            html = (root / 'evaluation.html').read_text()
            payload = html.split('<script id="data" type="application/json">')[1].split('</script>')[0]
            data = json.loads(payload)
            self.assertEqual(len(data['tasks']), 2)
            self.assertEqual(data['tasks'][1]['revisions'][0]['spec'], spec)
            self.assertNotIn('</script>', payload)


if __name__ == '__main__':
    unittest.main()
