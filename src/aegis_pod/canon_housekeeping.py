from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from src.aegis_pod.verified_marker import load_json, sha256_file, write_json


def inside_root(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def evaluate_entry(root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    path = root / entry["path"]
    exists = path.exists()
    computed_hash = sha256_file(path) if exists else ""
    outside_parameters: list[str] = []
    if not inside_root(root, path):
        outside_parameters.append("source artifact path is outside root")
    if not exists:
        outside_parameters.append("source artifact is missing")
    if exists and computed_hash != entry["source_hash"]:
        outside_parameters.append("source artifact hash changed")

    result = {
        "entry_id": entry["entry_id"],
        "path": entry["path"],
        "status": entry["status"],
        "exists": exists,
        "source_hash": entry["source_hash"],
        "computed_hash": computed_hash,
        "hash_current": exists and computed_hash == entry["source_hash"],
        "reason": entry["reason"],
        "outside_parameters": outside_parameters,
    }

    if entry["status"] == "superseded":
        replacement = entry.get("superseded_by", "")
        replacement_path = root / replacement
        replacement_exists = replacement_path.exists()
        computed_replacement_hash = sha256_file(replacement_path) if replacement_exists else ""
        replacement_hash = entry.get("replacement_hash", "")
        if not replacement:
            outside_parameters.append("superseded entry lacks replacement pointer")
        if replacement and replacement == entry["path"]:
            outside_parameters.append("superseded entry points to itself")
        if replacement and not inside_root(root, replacement_path):
            outside_parameters.append("replacement artifact path is outside root")
        if replacement and not replacement_exists:
            outside_parameters.append("replacement artifact is missing")
        if replacement_exists and computed_replacement_hash != replacement_hash:
            outside_parameters.append("replacement artifact hash changed")
        result.update({
            "superseded_by": replacement,
            "replacement_exists": replacement_exists,
            "replacement_hash": replacement_hash,
            "computed_replacement_hash": computed_replacement_hash,
            "replacement_hash_current": replacement_exists and computed_replacement_hash == replacement_hash,
        })
    elif entry.get("superseded_by"):
        outside_parameters.append("non-superseded entry should not declare superseded_by")

    if not entry.get("reason"):
        outside_parameters.append("entry reason is required")

    return result


def circular_supersession_ids(entries: list[dict[str, Any]]) -> set[str]:
    by_path = {entry.get("path"): entry for entry in entries}
    circular: set[str] = set()
    for entry in entries:
        visited: set[str] = set()
        current = entry
        while current.get("status") == "superseded" and current.get("superseded_by"):
            path = current["path"]
            replacement = current["superseded_by"]
            if replacement in visited or replacement == entry.get("path"):
                circular.add(str(entry.get("entry_id", "")))
                break
            visited.add(path)
            next_entry = by_path.get(replacement)
            if next_entry is None:
                break
            current = next_entry
    return circular


def run_housekeeping(
    root: Path,
    manifest_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    manifest_file = manifest_path if manifest_path is not None else root / "fixtures" / "canon-housekeeping-manifest.json"
    manifest = load_json(manifest_file)
    entries = [evaluate_entry(root, entry) for entry in manifest["entries"]]
    circular_ids = circular_supersession_ids(manifest["entries"])
    for entry in entries:
        if entry["entry_id"] in circular_ids:
            entry["outside_parameters"].append("circular supersession chain detected")
    report = {
        "schema_version": "0.1.0",
        "manifest_id": manifest["manifest_id"],
        "working_parameters": {
            "scope": manifest["working_parameters"]["scope"],
            "pod_state_effect": "unchanged",
            "live_reach": False,
            "files_deleted": False,
            "files_mutated": False,
            "outside_current_verified_surface": manifest["working_parameters"].get("outside_current_verified_surface", []),
        },
        "summary": {
            "entries_evaluated": len(entries),
            "canonical": sum(1 for entry in entries if entry["status"] == "canonical"),
            "superseded": sum(1 for entry in entries if entry["status"] == "superseded"),
            "draft": sum(1 for entry in entries if entry["status"] == "draft"),
            "open_question": sum(1 for entry in entries if entry["status"] == "open_question"),
            "outside_parameters": sum(1 for entry in entries if entry["outside_parameters"]),
        },
        "entries": entries,
    }
    target = output_path if output_path is not None else root / "reports" / "runtime" / "canon-housekeeping-report.json"
    write_json(target, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate local Canon housekeeping manifest.")
    parser.add_argument("--root", default=".", help="Workspace root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    report = run_housekeeping(root)
    print("PASS Canon housekeeping evaluated")
    print(f"ROOT {root}")
    print("BOUNDARY local reports only; no artifacts deleted or mutated and no live DataQuad roots referenced")
    for entry in report["entries"]:
        print(f"CANON {entry['entry_id']} status={entry['status']} outside={len(entry['outside_parameters'])}")
    if report["summary"]["outside_parameters"]:
        print(f"OUTSIDE_PARAMETERS {report['summary']['outside_parameters']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
