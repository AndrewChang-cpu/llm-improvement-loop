import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import view_experiment as viewer


class ViewerTests(unittest.TestCase):
    def test_only_accepted_candidates_use_their_round_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'settings.json').write_text(json.dumps({'task': {'id': 'example'}}))
            for round_number, candidate_number, accepted, current, spec in [
                (1, 1, True, 'Original\n', 'First winner\n'),
                (1, 2, False, 'Original\n', 'Rejected proposal\n'),
                (1, 3, None, 'Original\n', 'Pending proposal\n'),
                (2, 1, True, 'First winner\n', 'Second winner\n'),
            ]:
                candidate = root / f'round-{round_number:02d}' / f'candidate-{candidate_number:02d}'
                candidate.mkdir(parents=True)
                (candidate / 'current-specification.md').write_text(current)
                (candidate / 'candidate-specification.md').write_text(spec)
                if accepted is not None:
                    (candidate / 'decision.json').write_text(json.dumps({'accepted': accepted}))
                run = candidate / 'run-00'
                run.mkdir()
                (run / 'verdict.json').write_text(json.dumps({'criteria': [
                    {'criterion': key, 'passed': True} for key in viewer.CRITERIA
                ]}))
                (candidate / 'batch.json').write_text('{}')

            result = viewer.load_simplification(root)
            first, second = result['revisions']
            self.assertEqual([row['label'] for row in result['revisions']], ['Simplify 1', 'Simplify 2'])
            self.assertEqual((first['passes'], first['judged']), (1, 1))
            self.assertIn('-First winner', second['changes'])
            self.assertNotIn('Rejected proposal', second['changes'])
            self.assertEqual(second['spec'], 'Second winner\n')

    def test_one_report_combines_features_and_preserves_specification_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = 'Allow values < 10; never render </script> as markup.\n'
            batch = root / 'batch'
            for name in ['first', 'second']:
                source = batch / name / 'results' / name / 'revision-00'
                source.mkdir(parents=True)
                (source / 'specification.md').write_text(spec)
            shortened = root / 'simplification'
            candidate = shortened / 'round-01/candidate-01'
            candidate.mkdir(parents=True)
            (shortened / 'settings.json').write_text(json.dumps({'task': {'id': 'second'}}))
            (candidate / 'candidate-specification.md').write_text(spec)
            (candidate / 'current-specification.md').write_text('Original\n')
            (candidate / 'decision.json').write_text(json.dumps({'accepted': True}))
            with patch('sys.argv', ['view_experiment.py', str(batch), '--simplification', str(shortened)]):
                viewer.main()
            html = (batch / 'evaluation.html').read_text()
            payload = html.split('<script id="data" type="application/json">')[1].split('</script>')[0]
            data = json.loads(payload)
            self.assertEqual([task['name'] for task in data['tasks']], ['first', 'second'])
            rows = data['tasks'][1]['revisions']
            self.assertEqual([row['label'] for row in rows], ['Revision 0', 'Simplify 1'])
            self.assertEqual([row['number'] for row in rows], [0, 1])
            self.assertEqual(rows[1]['spec'], spec)
            self.assertEqual(rows[0]['judged'], 0)
            self.assertFalse(rows[0]['complete'])
            self.assertNotIn('</script>', payload)


if __name__ == '__main__':
    unittest.main()
