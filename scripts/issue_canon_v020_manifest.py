"""Issue a deterministic developmental Canon v0.20 source manifest.

The index is inventory.  The rulings file is authority.  This issuer never edits
source documents and refuses to infer governance fields from source prose.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0.0"
MANIFEST_ID = "AEGIS:CANON:v0.20:SOURCE-MANIFEST"
MERGE_MARKERS = re.compile(r"(?m)^(?:<<<<<<<|=======|>>>>>>>)(?:\s|$)")
REQUIRED_RULING_FIELDS = ("coordinate", "classification", "status", "seeded", "provenance")
REQUIRED_CANDIDATE_GATES = ("S-2", "S-4", "S-5", "S-6", "G-1")


class IssuanceError(ValueError):
    """A fail-closed manifest issuance refusal."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IssuanceError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise IssuanceError(f"JSON root must be an object: {path}")
    return value


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _resolve_locator(index_path: Path, canon_dir: str | None, locator: str) -> Path:
    path = Path(locator)
    if path.is_absolute():
        return path
    if canon_dir:
        return Path(canon_dir) / path
    return index_path.parent / path


def _normalized_supersession(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise IssuanceError("supersession must be an array of non-empty coordinates")
    return sorted(set(value))


def issue(
    index_path: Path,
    rulings_path: Path,
    *,
    candidate: bool = False,
    open_gate_ids: list[str] | None = None,
) -> dict[str, Any]:
    index = _load(index_path)
    rulings = _load(rulings_path)
    if rulings.get("canon_version") != "v0.20":
        raise IssuanceError("rulings canon_version must be v0.20")
    expected_status = "candidate" if candidate else "approved"
    if rulings.get("ruling_status") != expected_status:
        raise IssuanceError(f"rulings must declare ruling_status={expected_status}")
    gates = sorted(set(open_gate_ids or rulings.get("open_gate_ids", [])))
    if candidate:
        unknown_gates = sorted(set(gates) - set(REQUIRED_CANDIDATE_GATES))
        if unknown_gates:
            raise IssuanceError("candidate mode contains unknown governance gates: " + ", ".join(unknown_gates))
    elif gates:
        raise IssuanceError("clean issuance is unavailable while governance gates are open")

    entries = index.get("entries")
    decisions = rulings.get("documents")
    if not isinstance(entries, list) or not isinstance(decisions, dict):
        raise IssuanceError("index.entries and rulings.documents are required")
    if index.get("collisions", {}).get("code_claimed_twice_unresolved"):
        raise IssuanceError("index contains an unresolved code collision")

    indexed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("file"), str):
            raise IssuanceError("every index entry requires a file")
        if entry["file"] in indexed:
            raise IssuanceError(f"duplicate indexed file: {entry['file']}")
        indexed[entry["file"]] = entry
    unknown = sorted(set(decisions) - set(indexed))
    if unknown:
        raise IssuanceError(f"rulings name files absent from index: {', '.join(unknown)}")
    missing = sorted(set(indexed) - set(decisions))
    if missing:
        raise IssuanceError(f"unruled index entries: {', '.join(missing)}")

    manifest_entries: list[dict[str, Any]] = []
    coordinates: set[str] = set()
    canon_dir = index.get("canon_dir")
    for filename in sorted(indexed):
        decision = decisions[filename]
        if not isinstance(decision, dict):
            raise IssuanceError(f"ruling for {filename} must be an object")
        absent = [field for field in REQUIRED_RULING_FIELDS if field not in decision]
        if absent:
            raise IssuanceError(f"ruling for {filename} lacks: {', '.join(absent)}")
        coordinate = decision["coordinate"]
        if not isinstance(coordinate, str) or not coordinate.strip() or coordinate in coordinates:
            raise IssuanceError(f"invalid or duplicate coordinate for {filename}: {coordinate!r}")
        coordinates.add(coordinate)
        classification = decision["classification"]
        status = decision["status"]
        seeded = decision["seeded"]
        provenance = decision["provenance"]
        if classification in (None, "") or status in (None, ""):
            raise IssuanceError(f"undeclared classification/status for {filename}")
        if not candidate and (classification == "UNDECLARED" or status == "UNDECLARED"):
            raise IssuanceError(f"undeclared classification/status for {filename}")
        if not isinstance(seeded, bool) or not isinstance(provenance, dict) or not provenance:
            raise IssuanceError(f"invalid seeded/provenance ruling for {filename}")

        locator = decision.get("locator", filename)
        locator_unresolved = bool(decision.get("locator_unresolved", False))
        digest = decision.get("digest")
        if locator_unresolved:
            nature_exception = (
                coordinate == "AEGIS:NATURE-LAYER-CANON:v2"
                and classification == "EXCLUDED_LOCATOR_UNRESOLVED"
                and seeded is False
                and decision.get("exclusion_reason") == "locator_unresolved_excluded_from_seeded_bytes"
            )
            candidate_exception = candidate and seeded is False and bool(decision.get("review_required"))
            if not (nature_exception or candidate_exception):
                raise IssuanceError(f"unresolved required locator for {filename}")
            if digest is not None:
                raise IssuanceError("unresolved Nature v2 locator cannot assert a digest")
            locator_value: str | None = None
            digest_value: str | None = None
            byte_count: int | None = None
        else:
            if not isinstance(locator, str) or not locator:
                raise IssuanceError(f"missing locator for {filename}")
            source = _resolve_locator(index_path, canon_dir if isinstance(canon_dir, str) else None, locator)
            try:
                data = source.read_bytes()
            except OSError as exc:
                raise IssuanceError(f"unresolved required locator for {filename}: {source}") from exc
            if MERGE_MARKERS.search(data.decode("utf-8", errors="replace")):
                raise IssuanceError(f"merge marker found in {filename}")
            computed = _digest(data)
            if digest is not None and (not isinstance(digest, str) or digest.lower() != computed):
                raise IssuanceError(f"digest mismatch for {filename}")
            digest_value = computed
            locator_value = locator
            byte_count = len(data)

        manifest_entries.append({
            "classification": classification,
            "coordinate": coordinate,
            "digest": digest_value,
            "locator": locator_value,
            "locator_unresolved": locator_unresolved,
            "provenance": provenance,
            "review_required": bool(decision.get("review_required", False)),
            "seeded": seeded,
            "source_bytes": byte_count,
            "status": status,
            "supersession": _normalized_supersession(decision.get("supersession")),
        })

    manifest_entries.sort(key=lambda entry: entry["coordinate"])
    by_coordinate = {e["coordinate"]: e for e in manifest_entries}
    for entry in manifest_entries:
        for target in entry["supersession"]:
            if target not in by_coordinate:
                raise IssuanceError(f"dangling supersession reference: {entry['coordinate']} -> {target}")

    references = rulings.get("references", {})
    if not isinstance(references, dict):
        raise IssuanceError("rulings.references must be an object")
    index_refs = index.get("dangling_references", {})
    if not isinstance(index_refs, dict):
        raise IssuanceError("index.dangling_references must be an object")
    unresolved_refs = []
    resolved_refs = []
    for name in sorted(index_refs):
        ruling = references.get(name)
        if not isinstance(ruling, dict) or ruling.get("disposition") not in {"registered", "excluded", "corrected"}:
            unresolved_refs.append(name)
        else:
            target = ruling.get("coordinate")
            if ruling["disposition"] == "registered" and target not in by_coordinate:
                unresolved_refs.append(name)
            else:
                resolved_refs.append({"reference": name, **ruling})
    if unresolved_refs and not candidate:
        raise IssuanceError(f"dangling references lack ruled disposition: {', '.join(unresolved_refs)}")

    review_count = sum(1 for entry in manifest_entries if entry["review_required"])
    if candidate:
        review_count = max(review_count, len(gates))
    body = {
        "canon_lock_status": "review-needed" if candidate else "clean",
        "canon_version": "v0.20",
        "entries": manifest_entries,
        "issuance_status": "candidate" if candidate else "authoritative",
        "manifest_id": MANIFEST_ID,
        "open_gate_ids": gates,
        "reference_dispositions": resolved_refs,
        "unresolved_references": sorted(unresolved_refs),
        "reviewNeededSourceCount": review_count,
        "schema_version": SCHEMA_VERSION,
        "source_index_digest": _digest(index_path.read_bytes()),
        "source_rulings_digest": _digest(rulings_path.read_bytes()),
    }
    body["manifest_digest"] = _digest(_canonical_bytes(body))
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--rulings", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit-only", action="store_true")
    parser.add_argument("--candidate", action="store_true")
    parser.add_argument("--open-gate", action="append", default=[])
    args = parser.parse_args(argv)
    if not args.emit_only and args.output is None:
        parser.error("--output is required unless --emit-only is used")
    try:
        manifest = issue(
            args.index,
            args.rulings,
            candidate=args.candidate,
            open_gate_ids=args.open_gate,
        )
    except IssuanceError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.emit_only:
        sys.stdout.write(payload)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8", newline="\n")
        print(f"issued {args.output} ({len(manifest['entries'])} entries; review={manifest['reviewNeededSourceCount']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
