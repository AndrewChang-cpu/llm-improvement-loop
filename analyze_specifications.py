#!/usr/bin/env python3
"""Remove each final-specification section independently and reuse the experiment evaluator."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import fcntl
import hashlib
from pathlib import Path
import re
import sys

import run_experiment as runner


def fingerprint(value):
    return hashlib.sha256(value).hexdigest()


def section_variants(specification, allowed):
    headings, offset, fence = [], 0, None
    for line in specification.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        elif fence is None:
            match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
            if match:
                headings.append((offset, len(match[1]), match[2]))
        offset += len(line)
    sections = [heading for heading in headings if heading[2] in allowed]
    if not sections or len({s[2] for s in sections}) != len(sections):
        raise ValueError("Specification needs unique approved section headings")
    level = sections[0][1]
    if any(s[1] != level for s in sections):
        raise ValueError("Specification sections must use the same heading level")
    if any(h[1] == level and h[2] not in allowed for h in headings):
        raise ValueError("Specification contains an unapproved section heading")
    variants = {}
    for start, depth, name in sections:
        end = next((pos for pos, d, _ in headings if pos > start and d <= depth), len(specification))
        # Leave every other section, including repeated requirements, byte-for-byte intact.
        variants[name] = specification[:start] + specification[end:]
    return variants


def counts(verdicts):
    return {"runs": len(verdicts), "full_passes": sum(v["passed"] for v in verdicts),
            "criterion_pass_counts": {name: sum(next(c["passed"] for c in v["criteria"]
                                                       if c["criterion"] == name) for v in verdicts)
                                      for name in runner.CRITERIA}}


def aggregate(experiments):
    completed = [e for e in experiments.values() if e["status"] == "complete"]
    sections = {}
    for name in sorted({s for e in completed for s in e["sections"]}):
        entries = [e for e in completed if name in e["sections"]]
        ablations = [e["ablations"][name] for e in entries]
        sections[name] = {
            "present_in_experiments": len(entries),
            "experiments_with_all_ablation_runs_passing": sum(
                a["full_passes"] == len(a["runs"]) for a in ablations),
            "ablation_runs": sum(len(a["runs"]) for a in ablations),
            "ablation_full_passes": sum(a["full_passes"] for a in ablations),
            "criterion_pass_counts": {c: sum(a["criterion_pass_counts"][c] for a in ablations)
                                      for c in runner.CRITERIA},
            # Average within-experiment rate changes so each PR has equal weight.
            "mean_criterion_pass_rate_change": {
                c: sum(e["ablations"][name]["criterion_pass_counts"][c] /
                       len(e["ablations"][name]["runs"]) -
                       e["full_spec_results"]["criterion_pass_counts"][c] /
                       e["full_spec_results"]["runs"] for e in entries) / len(entries)
                for c in runner.CRITERIA},
            "mean_full_pass_rate_change": sum(
                e["ablations"][name]["full_passes"] / len(e["ablations"][name]["runs"]) -
                e["full_spec_results"]["full_passes"] / e["full_spec_results"]["runs"]
                for e in entries) / len(entries),
        }
    return {"completed_experiments": len(completed), "sections": sections}


def load_experiment(value):
    directory = Path(value).resolve()
    if not directory.is_dir():
        directory = (runner.ROOT / ".experiments" / value).resolve()
    candidates = list((directory / "results").glob("*/comprehensive-specification.md"))
    if len(candidates) != 1:
        raise ValueError(f"Expected one completed task in {directory}")
    source = candidates[0].parent
    result = runner.read_json(source / "result.json")
    settings = runner.read_json(source / "settings.json")
    if result["status"] != "converged":
        raise ValueError(f"Experiment has not converged: {directory}")
    revision = source / f"revision-{result['revision']:02d}"
    specification = candidates[0].read_text()
    if specification != (revision / "specification.md").read_text():
        raise ValueError("Final specification differs from its evaluated revision")
    saved = []
    for batch in (revision / "batch.json", revision / "confirmation/batch.json"):
        saved.extend(runner.read_json(batch)["runs"])
    for verdict in saved:
        if runner.validate_verdict(verdict) != verdict["passed"]:
            raise ValueError("Saved verdict is inconsistent")
    # Reuse the original environments and snapshots; never expose reference paths to generation.
    task = settings["task"]
    for key in ("base", "reference", "generator_python"):
        if not Path(task[key]).exists():
            raise ValueError(f"Missing prepared input: {task[key]}")
    return directory, source, settings, specification, counts(saved)


def analyze(value, database, shared_file, artifacts, repetitions, executable):
    directory, source, original_settings, specification, full_results = load_experiment(value)
    name = directory.name
    settings = {"model": original_settings["model"], "repetitions": repetitions, "codex": executable,
                "runner_version": fingerprint(Path(runner.__file__).read_bytes()),
                "analysis_version": fingerprint(Path(__file__).read_bytes()),
                "source_settings_hash": fingerprint((source / "settings.json").read_bytes())}
    spec_hash = fingerprint(specification.encode())
    existing = database["experiments"].get(name)
    if existing:
        if existing["spec_hash"] != spec_hash or existing["settings"] != settings or existing["source_directory"] != str(directory):
            raise ValueError(f"Analysis inputs changed for {name}; use a different --output file")
        if existing["status"] == "complete":
            print(f"Skipping completed analysis: {name}", flush=True)
            return
    variants = section_variants(specification, {s for values in runner.categories_from_docs().values() for s in values})
    record = existing or {"task_id": original_settings["task"]["id"], "source_directory": str(directory),
                          "spec_hash": spec_hash, "settings": settings, "sections": list(variants),
                          "full_spec_results": full_results, "ablations": {}, "status": "in_progress"}
    database["experiments"][name] = record
    destination = artifacts / name / fingerprint((spec_hash + str(settings)).encode())[:16]
    destination.mkdir(parents=True, exist_ok=True)

    def save():
        database["aggregate"] = aggregate(database["experiments"])
        runner.write_json(shared_file, database)

    def evaluate(section):
        output = destination / f"section-{list(variants).index(section):02d}"
        output.mkdir(parents=True, exist_ok=True)
        (output / "specification.md").write_text(variants[section])
        print(f"{name}: removing {section}", flush=True)
        verdicts = runner.evaluate_batch(original_settings["task"], output,
                                        runner.Codex(settings["model"], executable), variants[section],
                                        runs=repetitions)
        summary = counts(verdicts)
        return {"runs": [{"index": i, "artifact_directory": str(output / f"run-{i:02d}"),
                          "passed_all": v["passed"],
                          "criteria": {c["criterion"]: {k: c[k] for k in ("passed", "evidence", "deficiency")}
                                       for c in v["criteria"]}} for i, v in enumerate(verdicts)],
                "criterion_pass_counts": summary["criterion_pass_counts"], "full_passes": summary["full_passes"]}

    save()
    # Keep at most ten generation/evaluation lanes active, matching the experiment runner.
    with ThreadPoolExecutor(max_workers=max(1, 10 // min(10, repetitions))) as pool:
        futures = {pool.submit(evaluate, section): section for section in variants if section not in record["ablations"]}
        for future in as_completed(futures):
            section = futures[future]
            record["ablations"][section] = future.result()
            save()
            print(f"{name}: {section} = {record['ablations'][section]['full_passes']}/{repetitions} full passes", flush=True)
    record["status"] = "complete"
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiments", nargs="+", help="Experiment names under .experiments, or directory paths")
    parser.add_argument("--runs", type=int, default=1, help="Fresh generations per removed section (default: 1)")
    parser.add_argument("--output", type=Path, default=runner.ROOT / ".experiments/ablation-analysis.json")
    parser.add_argument("--artifacts", type=Path, default=runner.ROOT / ".experiments/ablations")
    parser.add_argument("--codex", default="codex")
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be positive")
    shared_file = args.output.resolve()
    shared_file.parent.mkdir(parents=True, exist_ok=True)
    # One writer owns the shared database; completed sections survive interrupted execution.
    with shared_file.with_suffix(".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        database = runner.read_json(shared_file) if shared_file.exists() else {"experiments": {}, "aggregate": {}}
        for value in args.experiments:
            analyze(value, database, shared_file, args.artifacts.resolve(), args.runs, args.codex)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
