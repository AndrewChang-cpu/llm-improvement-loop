#!/usr/bin/env python3
"""Render saved experiment results as a standalone HTML page (no model calls)."""
import argparse
import difflib
import json
from pathlib import Path

from run_experiment import CRITERIA


ROOT = Path(__file__).resolve().parent


def resolve_loop(name):
    for path in (Path(name), ROOT / '.experiments' / name):
        if path.is_dir():
            return path.resolve()
    # A task name alone works when it identifies exactly one saved loop.
    matches = list((ROOT / '.experiments').glob(f'*/results/{name}'))
    if len(matches) == 1:
        return matches[0].resolve()
    raise ValueError('Loop not found or ambiguous; supply its directory path.')


def load_counts(folder):
    counts = dict.fromkeys(CRITERIA, 0)
    judged = full_passes = 0
    # Unfinished runs are not failures.
    for verdict_path in sorted(folder.glob('run-*/verdict.json')):
        verdict = json.loads(verdict_path.read_text())
        outcomes = {item['criterion']: item['passed'] for item in verdict['criteria']}
        judged += 1
        for criterion in counts:
            counts[criterion] += outcomes.get(criterion) is True
        full_passes += all(outcomes.get(key) is True for key in CRITERIA)
    return {'counts': counts, 'judged': judged, 'passes': full_passes,
            'complete': (folder / 'batch.json').exists()}


def load_task(path):
    revisions = []
    previous = ''
    for folder in sorted(path.glob('revision-*')):
        spec_path = folder / 'specification.md'
        if not spec_path.exists():
            continue
        spec = spec_path.read_text()
        revisions.append({
            'number': int(folder.name.split('-')[-1]), 'spec': spec,
            'label': f'Revision {int(folder.name.split("-")[-1])}',
            'words': len(spec.split()),
            **load_counts(folder),
            'changes': ''.join(difflib.unified_diff(
                previous.splitlines(keepends=True), spec.splitlines(keepends=True),
                fromfile='Previous specification', tofile=folder.name)) if revisions else '',
        })
        previous = spec
    return {'name': path.name, 'revisions': revisions}


def load_simplification(path):
    settings = json.loads((path / 'settings.json').read_text())
    candidates = []
    for folder in sorted(path.glob('round-*/candidate-*')):
        decision_path = folder / 'decision.json'
        if not decision_path.exists():
            continue
        decision = json.loads(decision_path.read_text())
        if not decision.get('accepted'):
            continue
        spec_path = folder / 'candidate-specification.md'
        if not spec_path.exists():
            continue
        spec = spec_path.read_text()
        current = (folder / 'current-specification.md').read_text()
        round_number = int(folder.parent.name.split('-')[-1])
        candidates.append({
            'number': len(candidates) + 1,
            'label': f'Simplify {round_number}',
            'spec': spec, **load_counts(folder),
            'words': len(spec.split()),
            'input_words': len(current.split()),
            # Sibling proposals share an input; compare each against that input.
            'changes': ''.join(difflib.unified_diff(
                current.splitlines(keepends=True), spec.splitlines(keepends=True),
                fromfile='Round input specification', tofile=folder.name)),
        })
    return {'name': settings['task']['id'], 'revisions': candidates}


def load_tasks(directory):
    results = directory / 'results' if (directory / 'results').is_dir() else directory
    paths = [results] if list(results.glob('revision-*')) else sorted(results.iterdir())
    tasks = []
    for path in paths:
        if not path.is_dir():
            continue
        if (path / 'results').is_dir():
            tasks.extend(load_tasks(path))
        else:
            task = load_task(path)
            if task['revisions']:
                tasks.append(task)
    return tasks


HTML = r'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Specification loop evaluation</title>
<style>
:root{font:16px 'Segoe UI',Arial,sans-serif;color:#192b40;background:#f5f8fc}
body{max-width:1200px;margin:32px auto;padding:0 24px}h1{font-size:28px;margin-bottom:8px}
h2{font-size:21px}p{color:#50627a}section{margin:28px 0;background:white;padding:24px;border:1px solid #d5dfec}
select,button{font:inherit;padding:8px 12px;border:1px solid #a5b5c9;background:white;border-radius:4px}
button{cursor:pointer}button:disabled{opacity:.4;cursor:default}button:focus-visible,select:focus-visible{outline:3px solid #315dcc}
.controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap}.chart{overflow-x:auto}
svg{display:block;width:100%;min-width:650px;height:auto}svg text{font:13px 'Segoe UI',Arial,sans-serif;fill:#50627a}
#legend{display:flex;flex-wrap:wrap;gap:8px 18px;margin:12px 0}#legend label{font-size:14px;cursor:pointer}
.swatch{display:inline-block;width:12px;height:12px;margin:0 5px;border-radius:50%}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.65 Consolas,Menlo,monospace;background:#f5f8fc;padding:20px;border:1px solid #d5dfec}
table{border-collapse:collapse;font-size:14px;width:100%}th,td{text-align:left;padding:7px;border-bottom:1px solid #e2e9f1}th{font-weight:600}
details{margin-top:16px}summary{cursor:pointer;color:#315dcc}#status{margin:12px 0}#changes{color:#32465c}
@media(max-width:600px){body{padding:0 12px}section{padding:16px}}
</style>
<h1>Specification loop evaluation</h1>
<div class="controls"><label for="task">Feature</label><select id="task"></select></div>
<section><h2>Passes by evaluation category</h2>
<p id="chart-note"></p>
<div class="chart"><svg id="chart" viewBox="0 0 1100 360" role="img" aria-label="Category passes by revision"></svg></div>
<div id="legend"></div><details><summary>Show exact counts</summary><div id="counts"></div></details></section>
<section><h2>Input specifications</h2><div class="controls">
<button id="previous">Previous</button><label for="revision">Step</label><select id="revision"></select><button id="next">Next</button>
<label><input id="diff" type="checkbox"> Show changes from previous specification</label></div>
<p id="status"></p><pre id="spec"></pre></section>
<script id="data" type="application/json">__DATA__</script>
<script>
const data=JSON.parse(document.getElementById('data').textContent);
const $=id=>document.getElementById(id), keys=Object.keys(data.criteria);
const colors=['#275dcc','#c43e45','#258044','#9b4eaf','#c07800','#147f91','#745337','#d04c93','#697820','#565cba','#53677b'];
const visible=new Set(keys);let task;
const label=key=>key.replaceAll('_',' ').replace(/^./,c=>c.toUpperCase());
const entryLabel=r=>r.label||`Revision ${r.number}`;
function svg(tag,attrs={},text){const el=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v]of Object.entries(attrs))el.setAttribute(k,v);if(text!==undefined)el.textContent=text;return el;}
function draw(){
 const chart=$('chart');chart.replaceChildren();const rows=task.revisions;
 const maxY=Math.max(10,...rows.map(r=>r.judged)),first=rows[0].number,last=rows.at(-1).number;
 const x=n=>75+(last===first?465:(n-first)/(last-first)*930),y=n=>300-n/maxY*260;
 for(let n=0;n<=maxY;n++){const yy=y(n);chart.append(svg('line',{x1:75,x2:1005,y1:yy,y2:yy,stroke:'#e2e9f1'}),svg('text',{x:60,y:yy+4,'text-anchor':'end'},n));}
 chart.append(svg('text',{x:75,y:20},'Number of passes'),svg('text',{x:540,y:353,'text-anchor':'middle'},'Refinement → accepted simplifications'));
 for(const r of rows)chart.append(svg('text',{x:x(r.number),y:324,'text-anchor':'middle'},r.label||r.number));
 keys.forEach((key,i)=>{if(!visible.has(key))return;
  // Partial batches are hollow points, so fewer judgments stay visible.
  chart.append(svg('polyline',{points:rows.filter(r=>r.judged).map(r=>`${x(r.number)},${y(r.counts[key])}`).join(' '),fill:'none',stroke:colors[i],'stroke-width':2}));
  for(const r of rows){if(!r.judged)continue;const dot=svg('circle',{cx:x(r.number),cy:y(r.counts[key]),r:4,stroke:colors[i],fill:r.complete?colors[i]:'white','stroke-width':2});
   dot.append(svg('title',{},`${label(key)} — ${entryLabel(r)}: ${r.counts[key]}/${r.judged} judged runs${r.complete?'':' (partial batch)'}`));chart.append(dot);}
 });
}
function showSpec(){const index=Number($('revision').value),r=task.revisions[index];
 $('spec').textContent=$('diff').checked?(r.changes|| (index===0?'Baseline: no previous specification.':'No changes.')):r.spec;
 $('status').textContent=`${entryLabel(r)}: ${r.passes}/${r.judged} judged runs pass every category. ${r.words} words. `+(r.complete?'Batch complete.':'Batch incomplete; counts include only saved judgments.');
 $('previous').disabled=index===0;$('next').disabled=index===task.revisions.length-1;
}
function selectTask(){task=data.tasks[Number($('task').value)];
 $('revision').replaceChildren(...task.revisions.map((r,i)=>new Option(`${entryLabel(r)} — ${r.words} words${r.complete?'':' (partial)'}`,i)));
 $('chart-note').textContent='Refinement revisions followed by accepted simplifications. Rejected proposals are omitted. Counts use saved judge verdicts.';
 const table=document.createElement('table'),head=table.createTHead().insertRow();
 for(const text of ['Step','Words','Judged','All pass',...keys.map(label)]){const cell=document.createElement('th');cell.textContent=text;head.append(cell);}
 for(const r of task.revisions){const row=table.insertRow();for(const value of [entryLabel(r),r.words,r.judged,r.passes,...keys.map(k=>r.counts[k])])row.insertCell().textContent=value;}
 $('counts').replaceChildren(table);draw();showSpec();
}
data.tasks.forEach((t,i)=>$('task').add(new Option(t.name,i)));
keys.forEach((key,i)=>{const row=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.checked=true;
 const swatch=document.createElement('span');swatch.className='swatch';swatch.style.background=colors[i];row.append(check,swatch,document.createTextNode(label(key)));row.title=data.criteria[key];
 check.onchange=()=>{check.checked?visible.add(key):visible.delete(key);draw();};$('legend').append(row);});
$('task').onchange=selectTask;$('revision').onchange=showSpec;$('diff').onchange=showSpec;
$('previous').onclick=()=>{$('revision').selectedIndex--;showSpec();};$('next').onclick=()=>{$('revision').selectedIndex++;showSpec();};selectTask();
</script></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('loop', nargs='+', help='Loop names or directories; a batch directory includes all its features')
    parser.add_argument('--output', type=Path, help='HTML output (default: first LOOP/evaluation.html)')
    parser.add_argument('--simplification', type=Path, action='append', default=[],
                        help='Simplification task or batch directory; may be repeated')
    args = parser.parse_args()
    try:
        directories = [resolve_loop(name) for name in args.loop]
        tasks = [task for directory in directories for task in load_tasks(directory)]
        if not tasks:
            raise ValueError('No saved revision specifications found.')
        by_name = {task['name']: task for task in tasks}
        if len(by_name) != len(tasks):
            raise ValueError('Multiple refinement runs for the same feature; select one per feature.')
        for directory in args.simplification:
            paths = ([directory] if (directory / 'settings.json').exists() else
                     sorted(path for path in directory.iterdir() if (path / 'settings.json').exists()))
            if not paths:
                raise ValueError(f'No simplification tasks found in {directory}.')
            for path in paths:
                simplified = load_simplification(path)
                if simplified['name'] not in by_name:
                    raise ValueError('Simplification task does not match the refinement results.')
                by_name[simplified['name']]['revisions'].extend(simplified['revisions'])
        # Graph positions follow the combined sequence, not the original revision numbers.
        for task in tasks:
            for number, row in enumerate(task['revisions']):
                row['number'] = number
        # Escape HTML delimiters in embedded JSON; render specs using textContent.
        payload = json.dumps({'criteria': CRITERIA, 'tasks': tasks}).replace('<', '\\u003c')
        output = args.output or directories[0] / 'evaluation.html'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(HTML.replace('__DATA__', payload), encoding='utf-8')
        print(output.resolve())
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
