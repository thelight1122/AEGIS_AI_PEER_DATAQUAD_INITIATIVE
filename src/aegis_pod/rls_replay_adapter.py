"""Immutable-copy RLS evidence replay adapter.

The adapter observes preserved RLS ledger events. It does not import the Core
RLS runtime, start a container, write a ledger, admit experience, or perform
writeback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_RECORD_BYTES = 2 * 1024 * 1024
MAX_LIMIT = 100


class RLSReplayBoundaryError(ValueError):
    """Raised when replay evidence violates the immutable observation boundary."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def writable(path: Path) -> bool:
    mode = stat.S_IMODE(path.stat().st_mode)
    return bool(mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def resolve_inside(path: Path, approved_root: Path, label: str) -> Path:
    if path.is_symlink():
        raise RLSReplayBoundaryError(f"{label} will not be a symlink")
    if approved_root.is_symlink():
        raise RLSReplayBoundaryError("approved root will not be a symlink")
    root = approved_root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RLSReplayBoundaryError(f"{label} escapes approved root") from exc
    return resolved


def expected_hash(manifest: Path, filename: str) -> str:
    for line in manifest.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2 and Path(parts[1]).name == filename:
            return parts[0].lower()
    raise RLSReplayBoundaryError(f"hash manifest has no entry for {filename}")


def validate_source(
    source: Path,
    manifest: Path,
    approved_root: Path,
) -> tuple[str, str]:
    source = resolve_inside(source, approved_root, "RLS source")
    manifest = resolve_inside(manifest, approved_root, "RLS hash manifest")
    if source.name != "rls-ledger.jsonl":
        raise RLSReplayBoundaryError("source will be rls-ledger.jsonl")
    if not source.is_file() or not manifest.is_file():
        raise RLSReplayBoundaryError("RLS source and hash manifest will be files")
    if writable(source) or writable(manifest):
        raise RLSReplayBoundaryError("RLS source and hash manifest will be non-writable")
    source_hash = sha256_file(source)
    if source_hash != expected_hash(manifest, source.name):
        raise RLSReplayBoundaryError("RLS source hash drift detected")
    return source_hash, sha256_file(manifest)


def read_events(source: Path, query: str, limit: int) -> tuple[list[dict[str, Any]], int]:
    folded = query.casefold()
    matches: list[dict[str, Any]] = []
    total = 0
    with source.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if len(raw) > MAX_RECORD_BYTES:
                raise RLSReplayBoundaryError(f"rls-ledger.jsonl:{line_number}: record exceeds size bound")
            if not raw.strip():
                continue
            try:
                event = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise RLSReplayBoundaryError(f"rls-ledger.jsonl:{line_number}: malformed JSON") from exc
            if not isinstance(event, dict) or not isinstance(event.get("record"), dict):
                raise RLSReplayBoundaryError(f"rls-ledger.jsonl:{line_number}: invalid RLS event envelope")
            record = event["record"]
            if record.get("type") != "RLS" or not record.get("id") or not record.get("timestamp"):
                raise RLSReplayBoundaryError(f"rls-ledger.jsonl:{line_number}: invalid RLS record identity")
            total += 1
            if folded and folded not in json.dumps(event, ensure_ascii=False).casefold():
                continue
            if len(matches) >= limit:
                continue
            reflection = record.get("reflection") if isinstance(record.get("reflection"), dict) else {}
            matches.append({
                "line_number": line_number,
                "event": event.get("event"),
                "record_id": record["id"],
                "timestamp": record["timestamp"],
                "phase": record.get("phase"),
                "aspect_name": reflection.get("aspectName"),
                "layer": reflection.get("layer"),
                "drift_visible": reflection.get("driftVisible"),
                "return_signal": reflection.get("returnSignal"),
                "source_peer_id": reflection.get("sourcePeerId"),
                "source_psyche_id": reflection.get("sourcePsycheId"),
                "observation": reflection.get("observation"),
                "observation_only": True,
                "admission_status": "not_admitted",
            })
    return matches, total


def replay(
    source: Path,
    manifest: Path,
    approved_root: Path,
    query: str,
    limit: int,
) -> dict[str, Any]:
    if limit < 1 or limit > MAX_LIMIT:
        raise RLSReplayBoundaryError(f"limit will be between 1 and {MAX_LIMIT}")
    source_hash, manifest_hash = validate_source(source, manifest, approved_root)
    source = resolve_inside(source, approved_root, "RLS source")
    matches, total = read_events(source, query, limit)
    post_source_hash = sha256_file(source)
    post_manifest_hash = sha256_file(resolve_inside(manifest, approved_root, "RLS hash manifest"))
    if source_hash != post_source_hash:
        raise RLSReplayBoundaryError("RLS source changed during replay")
    if manifest_hash != post_manifest_hash:
        raise RLSReplayBoundaryError("RLS hash manifest changed during replay")
    return {
        "schema_version": "0.1.0",
        "report": "phase1-rls-replay-observation",
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {
            "path": str(source),
            "mode": "immutable_copy_replay",
            "live_source": False,
            "source_sha256": source_hash,
            "post_replay_source_sha256": post_source_hash,
            "hash_manifest": str(manifest),
            "hash_manifest_sha256": manifest_hash,
            "post_replay_hash_manifest_sha256": post_manifest_hash,
            "event_count": total,
        },
        "query": {"text": query, "limit": limit, "match_count": len(matches)},
        "observations": matches,
        "boundary": {
            "core_runtime_imported": False,
            "rls_started": False,
            "source_write_attempted": False,
            "pod_write_attempted": False,
            "writeback_performed": False,
            "admission_performed": False,
            "experience_created": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay immutable RLS evidence without writeback.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--hash-manifest", type=Path, required=True)
    parser.add_argument("--approved-root", type=Path, required=True)
    parser.add_argument("--query", default="")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = replay(args.source, args.hash_manifest, args.approved_root, args.query, args.limit)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS RLS immutable-copy replay observation")
    print(f"REPORT {args.report.resolve()}")
    print("BOUNDARY replay only; no Core import, RLS start, writeback, admission, or experience creation")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
