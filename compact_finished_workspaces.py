#!/usr/bin/env python3
"""Archive completed repository copies without removing experiment evidence."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile


SKIP = {".git", "source.git", "venv", "generator-venv", "base", "reference",
        "generated", "evaluation", "workspace", "__pycache__", "candidate-test-tmp",
        "test-tmp", "workspace-archives"}
TERMINAL = {"converged", "non_convergent", "complete", "starting_specification_failed"}


def candidates(root):
    finished, unfinished, workspaces = {}, set(), []
    for directory, dirs, files in os.walk(root):
        path = Path(directory)
        for name in ("generated", "evaluation"):
            if name in dirs and path.name.startswith("run-"):
                workspaces.append(path / name)
        dirs[:] = [name for name in dirs if name not in SKIP]
        if "result.json" in files:
            result = json.loads((path / "result.json").read_text())
            if result.get("status") in TERMINAL:
                finished[path] = result
        elif "settings.json" in files:
            unfinished.add(path)
    for workspace in workspaces:
        owner = next((p for p in workspace.parents if p in finished), None)
        if owner is None or any(p in unfinished for p in workspace.parents if p != root):
            continue
        result = finished[owner]
        # Future simplification editors read the final batch's generated repositories.
        if (workspace.name == "generated" and result.get("status") == "converged"
                and workspace.parent.parent == owner / f"revision-{result['revision']:02d}"):
            continue
        if not workspace.is_symlink():
            yield workspace


def compact(workspace, root):
    archive_root = root / "workspace-archives"
    archive = (archive_root / workspace.relative_to(root)).with_suffix(".tar.gz")
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        raise RuntimeError(f"Archive already exists; leaving workspace untouched: {archive}")
    temporary = archive.with_suffix(".partial")
    try:
        with tarfile.open(temporary, "w:gz", compresslevel=1) as output:
            output.add(workspace, arcname=workspace.name)
        # Verify the complete gzip stream and checksum before deleting expanded files.
        with gzip.open(temporary, "rb") as content:
            while content.read(1024 * 1024):
                pass
        with temporary.open("rb") as content:
            checksum = hashlib.sha256()
            for block in iter(lambda: content.read(1024 * 1024), b""):
                checksum.update(block)
        temporary.rename(archive)
        entry = {"workspace": str(workspace), "archive": str(archive),
                 "archive_bytes": archive.stat().st_size, "sha256": checksum.hexdigest()}
        with (archive_root / "manifest.jsonl").open("a") as log:
            log.write(json.dumps(entry) + "\n")
            log.flush()
            os.fsync(log.fileno())
        shutil.rmtree(workspace)
        return entry
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(".experiments"))
    parser.add_argument("--apply", action="store_true", help="Archive and remove expanded copies")
    args = parser.parse_args()
    root = args.root.resolve()
    paths = list(candidates(root))
    print(f"{len(paths)} completed workspace copies selected", flush=True)
    if args.apply:
        for number, path in enumerate(paths, 1):
            compact(path, root)
            print(f"[{number}/{len(paths)}] Archived {path.relative_to(root)}", flush=True)
    else:
        for path in paths:
            print(path)


if __name__ == "__main__":
    main()
