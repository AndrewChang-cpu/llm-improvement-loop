#!/usr/bin/env python3
"""Simplify saved specifications, retaining only reductions of at least 10% that pass 10/10."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import sys

from analyze_specifications import counts, load_experiment
import run_experiment as runner


EDIT_SCHEMA = runner.object_schema({"specification": runner.TEXT, "changes": runner.TEXT})


def word_count(specification):
    return len(specification.split())


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def simplify(value, output, executable="codex"):
    directory, source, original_settings, specification, historical = load_experiment(value)
    specification = specification.strip()
    categories = runner.categories_from_docs()
    settings = {
        "source": str(source), "source_settings_sha256": file_hash(source / "settings.json"),
        "source_specification_sha256": hashlib.sha256(specification.encode()).hexdigest(),
        "model": original_settings["model"], "codex": executable,
        "task": original_settings["task"], "categories": categories,
        "runs": 10, "required_passes": 10, "confirmation": False,
        "minimum_reduction_percent": 10, "word_count": "whitespace-separated, including headings",
        "stop_on_first_unsuccessful_attempt": True,
        "runner_sha256": file_hash(Path(runner.__file__)),
        "simplifier_sha256": file_hash(Path(__file__)),
    }
    output.mkdir(parents=True, exist_ok=True)
    if (output / "settings.json").exists() and runner.read_json(output / "settings.json") != settings:
        raise ValueError(f"Simplification inputs changed: use a new output directory for {directory.name}")
    runner.write_json(output / "settings.json", settings)
    if (output / "result.json").exists():
        print(f"Skipping completed simplification: {directory.name}", flush=True)
        return runner.read_json(output / "result.json")

    task = settings["task"]
    agent = runner.Codex(settings["model"], executable)
    initial_words = word_count(specification)
    (output / "starting-specification.md").write_text(specification + "\n")
    print(f"{directory.name}: checking starting specification ({initial_words} words)", flush=True)
    # Historical convergence may use 9/10; qualify the starting point with fresh runs.
    verdicts = runner.evaluate_batch(task, output / "starting-batch", agent, specification)
    starting_results = counts(verdicts)
    accepted = []

    def finish(reason, last_attempt=None):
        qualified = starting_results["full_passes"] == 10
        if qualified:
            (output / "simplified-specification.md").write_text(specification + "\n")
        result = {
            "experiment": directory.name, "task_id": task["id"],
            "status": "complete" if qualified else "starting_specification_failed",
            "stop_reason": reason, "historical_results": historical,
            "starting_results": starting_results, "initial_words": initial_words,
            "final_words": word_count(specification) if qualified else None,
            "reduction_percent": 100 * (1 - word_count(specification) / initial_words) if qualified else None,
            "accepted_attempts": accepted, "last_attempt": last_attempt,
        }
        runner.write_json(output / "result.json", result)
        print(f"{directory.name}: {reason}; {len(accepted)} accepted reductions", flush=True)
        return result

    if starting_results["full_passes"] != 10:
        return finish("starting_batch_below_10_of_10")

    attempt = 1
    while True:
        current_words = word_count(specification)
        target = current_words * 9 // 10
        destination = output / f"attempt-{attempt:02d}"
        context = destination / "editor-context"
        context.mkdir(parents=True, exist_ok=True)
        current_file = destination / "current-specification.md"
        current_file.write_text(specification + "\n")
        feedback_file = context / "feedback.json"
        runner.write_json(feedback_file, {
            "current_specification": specification, "current_words": current_words,
            "maximum_candidate_words": target, "categories": categories,
            "original": task["base"], "reference": task["reference"],
            "requirements": task["requirements"], "runs": verdicts,
        })
        prompt = (
            "Read feedback.json, the current specification, and relevant original, reference, and generated code. "
            "Revise this passing specification to make it at least 10% shorter without reducing its ability "
            "to guide a correct implementation. The reference implementation defines required behavior, "
            "public contracts, and architecture. Read inherited reference methods where relevant. "
            f"The specification contains {current_words} whitespace-separated words, including headings. "
            f"Your revision must contain no more than {target} words. The script verifies this count. "
            "First remove repeated instructions and explanations that do not help implement the feature. "
            "Then shorten wording where the same requirement can be expressed more directly. You may "
            "rewrite or remove multiple sections. Use only the approved subsection names as section headings; "
            "parent categories only group the inventory. Preserve required behavior, contracts, and "
            "implementation constraints. Keep instructions clear and explicit. Do not use cryptic "
            "abbreviations, artificial word joining, omitted conditions, or actual implementation code "
            "to meet the length target. Do not supply programming-language bodies, executable examples, "
            "or code-form declarations or signatures. API contracts can use non-code formats; clearly "
            "labeled pseudocode is allowed. Do not copy reference code into the specification. "
            "Explain what you removed or rewrote and why the remaining instructions are sufficient. "
            "A reduction below 10% is unsuccessful, even if the resulting code would pass. "
            "Do not modify any files, run another agent, or access the network. Return only the revised "
            "specification and change explanation in the requested JSON response."
        )
        response = agent.run("simplify", prompt, context, destination / "editing", EDIT_SCHEMA,
                             readable=[task["base"], task["reference"]] + [v["generated"] for v in verdicts],
                             protected=[current_file, feedback_file])
        candidate = response["specification"].strip()
        if not candidate or not response["changes"].strip():
            raise ValueError("Simplification response needs a specification and change explanation")
        candidate_words = word_count(candidate)
        (destination / "candidate-specification.md").write_text(candidate + "\n")
        runner.write_json(destination / "proposal.json", response)
        decision = {"attempt": attempt, "previous_words": current_words,
                    "maximum_candidate_words": target, "candidate_words": candidate_words,
                    "length_passed": candidate_words <= target, "accepted": False,
                    "artifact_directory": str(destination)}
        if not decision["length_passed"]:
            # Do not spend twenty model calls evaluating an ineligible reduction.
            runner.write_json(destination / "decision.json", decision)
            return finish("reduction_below_10_percent", decision)
        print(f"{directory.name}: attempt {attempt}, {current_words} -> {candidate_words} words", flush=True)
        candidate_verdicts = runner.evaluate_batch(task, destination, agent, candidate)
        decision["results"] = counts(candidate_verdicts)
        decision["accepted"] = decision["results"]["full_passes"] == 10
        runner.write_json(destination / "decision.json", decision)
        if not decision["accepted"]:
            return finish("candidate_below_10_of_10", decision)
        # A rejected candidate never replaces the last passing specification.
        accepted.append(decision)
        specification, verdicts = candidate, candidate_verdicts
        (output / "simplified-specification.md").write_text(specification + "\n")
        print(f"{directory.name}: accepted attempt {attempt} (10/10)", flush=True)
        attempt += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiments", nargs="+", help="Existing completed experiment names or directories")
    parser.add_argument("--output", type=Path, required=True, help="New validation output directory")
    parser.add_argument("--codex", default="codex")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with (output / "simplification.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        summary_file = output / "summary.json"
        summary = runner.read_json(summary_file) if summary_file.exists() else {}
        for experiment in args.experiments:
            name = Path(experiment).name
            summary[name] = simplify(experiment, output / name, args.codex)
            runner.write_json(summary_file, summary)
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
