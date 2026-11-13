#!/usr/bin/env python3
"""Search three independent 10–30% reductions per round, retaining the shortest 10/10 candidate."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import sys

from analyze_specifications import counts, load_experiment
import run_experiment as runner


EDIT_SCHEMA = runner.object_schema({
    "status": {"type": "string", "enum": ["revised", "blocked"]},
    "specification": runner.TEXT, "changes": runner.TEXT,
})


def word_count(specification):
    return len(specification.split())


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def simplify(value, output, executable=None, effort=None):
    directory, source, original_settings, specification, historical = load_experiment(value)
    specification = specification.strip()
    categories = runner.categories_from_docs()
    settings = {
        "source": str(source), "source_settings_sha256": file_hash(source / "settings.json"),
        "source_specification_sha256": hashlib.sha256(specification.encode()).hexdigest(),
        "model": original_settings["model"], "codex": executable,
        "backend": original_settings.get("backend", "codex"), "effort": effort or original_settings.get("effort", "low"),
        "task": original_settings["task"], "categories": categories, "judge_effort": "high",
        "runs": 10, "required_passes": 10, "confirmation": False,
        "minimum_reduction_percent": 10, "maximum_reduction_percent": 30,
        "candidates_per_round": 3, "word_count": "whitespace-separated, including headings",
        "stop_on_first_unsuccessful_round": True,
        "runner_sha256": file_hash(Path(runner.__file__)),
        "simplifier_sha256": file_hash(Path(__file__)),
    }
    output.mkdir(parents=True, exist_ok=True)
    saved = runner.read_json(output / "settings.json") if (output / "settings.json").exists() else None
    # The per-experiment locking change did not alter simplification behavior.
    if saved and saved.get("simplifier_sha256") in {"3a279283849a3c0cc8766e10f4ee11db8f693bd4f91d3039abcebe97f2031667",
                                                   "6baee10bc354aa65fb1ec6a87e50be15aa04443036621ae9592cbb1135224566",
                                                   "2e5404831f465f87cd21cb8bb59bfb00e196b0a74dadd0974e04bef8cb4e9fca",
                                                   "029af23d6cf6c5ad0e3d76f728427eb322f0182bd200098f740f223134f1528d",
                                                   "6696991c7b33b11ddb99e66bfeb9b72c63c67f537ecc74c9d1373c5add5d0e4b"}:
        saved["simplifier_sha256"] = settings["simplifier_sha256"]
    # Deleting judged repository copies did not alter results. Resuming the source experiment
    # rewrites its settings with only the new runner hash, so accept that source change too.
    if saved and saved.get("runner_sha256") in {"6df0fd0d512307adff72d59a1abbf16181d12eeafc164aa4dc471dbaf7364c40",
                                                "35a0e92f2c4437fa4f742de72b5be40d2c9bfab938e8ad1ee1b8a9a6c6a2dba6",
                                                "b492afa421aa2bfe07706d2f2276c1fe00921d35881b398e22d5985d328b883d"}:
        previous_source = dict(runner.read_json(source / "settings.json"), runner_sha256=saved["runner_sha256"])
        if (hashlib.sha256((json.dumps(previous_source, indent=2) + "\n").encode()).hexdigest()
                == saved["source_settings_sha256"]):
            saved["source_settings_sha256"] = settings["source_settings_sha256"]
        saved["runner_sha256"] = settings["runner_sha256"]
    if saved is not None and saved != settings:
        raise ValueError(f"Simplification inputs changed: use a new output directory for {directory.name}")
    runner.write_json(output / "settings.json", settings)
    if (output / "result.json").exists():
        print(f"Skipping completed simplification: {directory.name}", flush=True)
        return runner.read_json(output / "result.json")

    task = settings["task"]
    agent = runner.Codex(settings["model"], executable, settings["backend"], settings["effort"])
    initial_words = word_count(specification)
    (output / "starting-specification.md").write_text(specification + "\n")
    if (original_settings.get("required_passes") == 10 and original_settings.get("confirmation") is False
            and original_settings.get("effort") == settings["effort"]
            and original_settings.get("judge_effort", original_settings.get("effort", "high")) == "high"):
        # Reuse the qualifying batch instead of reintroducing a confirmation requirement.
        revision = runner.read_json(source / "result.json")["revision"]
        batch = source / f"revision-{revision:02d}" / "batch.json"
        verdicts = runner.read_json(batch)["runs"]
        if not runner.converged([v["passed"] for v in verdicts]):
            raise ValueError("Source specification did not pass its recorded 10/10 batch")
        runner.write_json(output / "starting-batch-source.json", {"batch": str(batch)})
        print(f"{directory.name}: using qualifying batch ({initial_words} words, 10/10)", flush=True)
    else:
        print(f"{directory.name}: checking starting specification ({initial_words} words)", flush=True)
        # Historical convergence may use 9/10; qualify those specifications with fresh runs.
        verdicts = runner.evaluate_batch(task, output / "starting-batch", agent, specification)
    starting_results = counts(verdicts)
    accepted = []

    def finish(reason, last_round=None):
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
            "accepted_rounds": accepted, "last_round": last_round,
        }
        runner.write_json(output / "result.json", result)
        print(f"{directory.name}: {reason}; {len(accepted)} accepted reductions", flush=True)
        return result

    if starting_results["full_passes"] != 10:
        return finish("starting_batch_below_10_of_10")

    round_number = 1
    while True:
        current_words = word_count(specification)
        target = current_words * 9 // 10
        minimum = (current_words * 7 + 9) // 10
        round_directory = output / f"round-{round_number:02d}"
        proposals = []
        # Every editor sees the same incumbent and feedback, never another proposal.
        for number in range(1, 4):
            destination = round_directory / f"candidate-{number:02d}"
            context = destination / "editor-context"
            context.mkdir(parents=True, exist_ok=True)
            current_file = destination / "current-specification.md"
            current_file.write_text(specification + "\n")
            feedback_file = context / "feedback.json"
            runner.write_json(feedback_file, {
                "current_specification": specification, "current_words": current_words,
                "minimum_candidate_words": minimum, "maximum_candidate_words": target,
                "categories": categories, "original": task["base"], "reference": task["reference"],
                "requirements": task["requirements"], "runs": verdicts,
            })
            prompt = (
                f"Use your shell tool to read {feedback_file.resolve()} first. "
                "It contains the current specification and paths to the relevant original, reference, and generated code. "
                "Read-only shell commands are allowed; the restriction on modifying files does not prohibit reading them. "
                "Independently revise this passing specification to make it between 10% and 30% shorter "
                "without reducing its ability to guide a correct implementation. Do not inspect other "
                "proposals, sibling candidate directories, or results from other simplification candidates. "
                "The reference implementation defines required behavior, public contracts, and architecture. "
                "Read inherited reference methods where relevant. "
                f"The specification contains {current_words} whitespace-separated words, including headings. "
                f"Your revision must contain between {minimum} and {target} words inclusive. "
                "The script verifies this count. First remove repeated instructions and explanations that "
                "do not help implement the feature. Then shorten wording where the same requirement can "
                "be expressed more directly. You may rewrite or remove multiple sections. Use only the "
                "approved subsection names as section headings; parent categories only group the inventory. "
                "Preserve required behavior, contracts, and implementation constraints. Keep instructions "
                "clear and explicit. Do not use cryptic abbreviations, artificial word joining, omitted "
                "conditions, or actual implementation code to meet the length target. Do not supply "
                "programming-language bodies, executable examples, or code-form declarations or signatures. "
                "API contracts can use non-code formats; clearly labeled pseudocode is allowed. Do not "
                "copy reference code into the specification. Explain what you removed or rewrote and why "
                "the remaining instructions are sufficient. A reduction outside 10–30% is unsuccessful, "
                "even if the resulting code would pass. Do not modify any files, run another agent, or "
                "access the network. Return only the revised specification and change explanation in "
                "the requested JSON response, with status revised. If an actual tool or file-access failure "
                "prevents revision, return status blocked and explain the failure in changes. "
                "Do not put a refusal in the specification field and label it revised."
            )
            rebuild = [] if (destination / "editing/complete.json").exists() else verdicts
            with runner.materialized(task, rebuild):
                response = agent.run("simplify", prompt, context, destination / "editing", EDIT_SCHEMA,
                                     readable=[task["base"], task["reference"]] + [v["generated"] for v in verdicts],
                                     protected=[current_file, feedback_file])
            if response["status"] != "revised":
                raise RuntimeError(f"Simplification editor blocked: {response['changes']}. Logs: {destination / 'editing'}")
            candidate = response["specification"].strip()
            if not candidate or not response["changes"].strip():
                raise ValueError("Simplification response needs a specification and change explanation")
            candidate_words = word_count(candidate)
            (destination / "candidate-specification.md").write_text(candidate + "\n")
            runner.write_json(destination / "proposal.json", response)
            proposals.append({"candidate": number, "previous_words": current_words,
                              "minimum_candidate_words": minimum, "maximum_candidate_words": target,
                              "candidate_words": candidate_words,
                              "length_passed": minimum <= candidate_words <= target,
                              "qualified": False, "accepted": False,
                              "artifact_directory": str(destination)})

        evaluated = {}
        for decision in proposals:
            destination = Path(decision["artifact_directory"])
            if decision["length_passed"]:
                candidate = (destination / "candidate-specification.md").read_text().strip()
                print(f"{directory.name}: round {round_number}, candidate {decision['candidate']}, "
                      f"{current_words} -> {decision['candidate_words']} words", flush=True)
                evaluated[decision["candidate"]] = runner.evaluate_batch(task, destination, agent, candidate)
                decision["results"] = counts(evaluated[decision["candidate"]])
                decision["qualified"] = decision["results"]["full_passes"] == 10
            # Out-of-range drafts never consume generation or evaluation calls.
            runner.write_json(destination / "decision.json", decision)
        passing = [decision for decision in proposals if decision["qualified"]]
        selected = min(passing, key=lambda d: (d["candidate_words"], d["candidate"])) if passing else None
        round_result = {"round": round_number, "previous_words": current_words,
                        "candidates": proposals, "selected_candidate": selected["candidate"] if selected else None}
        if selected:
            selected["accepted"] = True
            runner.write_json(Path(selected["artifact_directory"]) / "decision.json", selected)
        runner.write_json(round_directory / "round.json", round_result)
        if not selected:
            return finish("no_qualifying_candidate", round_result)
        # Only the shortest qualifying candidate replaces the incumbent.
        accepted.append(round_result)
        specification = (Path(selected["artifact_directory"]) / "candidate-specification.md").read_text().strip()
        verdicts = evaluated[selected["candidate"]]
        (output / "simplified-specification.md").write_text(specification + "\n")
        print(f"{directory.name}: accepted round {round_number}, candidate {selected['candidate']} "
              f"({selected['candidate_words']} words, 10/10)", flush=True)
        round_number += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiments", nargs="+", help="Existing completed experiment names or directories")
    parser.add_argument("--output", type=Path, required=True, help="New validation output directory")
    parser.add_argument("--codex")
    parser.add_argument("--effort", choices=["low", "medium", "high"], help="Generator/simplifier effort; defaults to source effort. Judges always use high")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Lock each experiment for its whole simplification, and the shared summary only while updating it.
    for experiment in args.experiments:
        name = Path(experiment).name
        with (output / f"{name}.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = simplify(experiment, output / name, args.codex, args.effort)
        with (output / "simplification.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            summary_file = output / "summary.json"
            summary = runner.read_json(summary_file) if summary_file.exists() else {}
            summary[name] = result
            runner.write_json(summary_file, summary)
        print(json.dumps({name: result}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
