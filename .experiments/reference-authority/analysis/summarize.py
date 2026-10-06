"""Summarize recorded pilot outcomes without changing experimental judgments."""
import collections
import json
from pathlib import Path
import re

storage = Path(__file__).resolve().parents[1]
project = storage.parents[1]
summaries = []
for path in sorted((storage / "results").glob("*/revision-*/**/batch.json")):
    batch = json.loads(path.read_text())
    criteria, tests, errors = (collections.Counter() for _ in range(3))
    for verdict in batch["runs"]:
        criteria.update(row["criterion"] for row in verdict["criteria"] if not row["passed"])
        checks = json.loads((Path(verdict["generated"]).parent / "checks.json").read_text())
        for command in checks["commands"]:
            tests.update(re.findall(r"^FAILED (\S+)", command["output"], re.M))
            errors.update(re.findall(r"^ERROR (\S+)", command["output"], re.M))
    summary = {"batch": str(path.parent.relative_to(storage / "results")),
               "full_passes": batch["passes"], "criterion_failures": dict(criteria),
               "test_failures": dict(tests), "collection_errors": dict(errors)}
    summaries.append(summary)
destination = storage / "analysis/revision-summary.json"
destination.write_text(json.dumps(summaries, indent=2) + "\n")
document = project / "docs/pilot-results.md"
prefix = document.read_text().split("\n## Batch outcomes\n", 1)[0]
lines = [prefix.rstrip(), "", "## Batch outcomes", ""]
for summary in summaries:
    lines += ["### " + summary["batch"], "", f"Full passes: **{summary['full_passes']}/10**.", ""]
    for label, key in (("Judge-reported criterion failures", "criterion_failures"),
                       ("Observed executable test failures", "test_failures"),
                       ("Observed collection errors", "collection_errors")):
        lines += [label + ":", ""]
        if not summary[key]:
            lines += ["None.", ""]
            continue
        lines += ["| Item | Failed runs |", "| --- | ---: |"]
        lines += [f"| `{name}` | {count}/10 |" for name, count in summary[key].items()]
        lines += [""]
document.write_text("\n".join(lines) + "\n")
print(json.dumps(summaries[-1:] or {"status": "first batch pending"}, indent=2))
