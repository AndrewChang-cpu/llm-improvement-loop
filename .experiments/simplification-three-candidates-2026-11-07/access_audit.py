"""Screen saved tool commands for forbidden inputs; flags require manual inspection."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import run_experiment as runner

folder = Path(__file__).resolve().parent
sessions = []
for request_path in sorted(folder.rglob('request.json')):
    request = runner.read_json(request_path)
    role = request.get('role')
    if role not in {'generate', 'judge', 'edit', 'simplify'}:
        continue
    command = request['command']
    cwd = command[command.index('-C') + 1]
    events = request_path.with_name('events.jsonl')
    if not events.exists():
        continue
    row = {'session': str(request_path.parent.relative_to(folder)), 'role': role,
           'complete': request_path.with_name('complete.json').exists(),
           'events_sha256': hashlib.sha256(events.read_bytes()).hexdigest(),
           'commands': 0, 'flags': [], 'file_changes': []}
    for number, line in enumerate(events.read_text().splitlines(), 1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get('type') != 'item.completed':
            continue
        item = event.get('item', {})
        if item.get('type') == 'file_change' and role != 'generate':
            row['file_changes'].append({'line': number, 'changes': item.get('changes')})
        if item.get('type') != 'command_execution':
            continue
        row['commands'] += 1
        if role != 'generate':
            continue
        text = item.get('command', '').replace(cwd, '<WORKSPACE>')
        # Prepared Python paths are allowed; sibling code and feedback are not.
        text = re.sub(r'/[^\s\"\']*/generator-venv', '<ENVIRONMENT>', text)
        if re.search(r'/(?:reference|source\.git)(?:/|[\s\"\'])|reference\.diff|feedback\.json|comprehensive-specification\.md|starting-specification\.md|batch\.json|verdict\.json|\.\./|\.experiments/', text):
            row['flags'].append({'line': number, 'command': item.get('command'),
                                 'exit_code': item.get('exit_code')})
    sessions.append(row)
report = {'scope': 'Command screening and non-generator file-change events; not enforced filesystem isolation.',
          'sessions': sessions,
          'totals': {'sessions': len(sessions), 'commands': sum(s['commands'] for s in sessions),
                     'generator_flags': sum(len(s['flags']) for s in sessions),
                     'non_generator_file_changes': sum(len(s['file_changes']) for s in sessions)}}
runner.write_json(folder / 'access-audit.json', report)
print(json.dumps(report['totals']))
for s in sessions:
    if s['flags'] or s['file_changes']:
        print(s['session'], json.dumps(s['flags'] + s['file_changes'])[:2200])
