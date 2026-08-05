"""Copy-backed, read-only DataQuad observation adapter.

This module deliberately has no imports from the CyberPeer Core runtime. It
reads an explicitly supplied immutable copy of the four canonical tensor
JSONL files and returns bounded observations. It never performs admission,
experience formation, or source writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TENSORS = ("PEER", "PCT", "NCT", "SPINE")
MAX_RECORD_BYTES = 2 * 1024 * 1024


class AdapterBoundaryError(ValueError):
    """Raised when the copy-backed source violates the read boundary."""


@dataclass(frozen=True)
class SourceFile:
    tensor: str
    path: Path
    sha256: str
    record_count: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_writable(path: Path) -> bool:
    mode = stat.S_IMODE(path.stat().st_mode)
    return bool(mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def _load_expected_hashes(path: Path) -> dict[str, str]:
    expected: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            parts = line.strip().split()
            if len(parts) != 2:
                continue
            digest, source = parts
            name = Path(source).stem
            if name in TENSORS:
                expected[name] = digest.lower()
    missing = [name for name in TENSORS if name not in expected]
    if missing:
        raise AdapterBoundaryError(f"expected hash record missing tensors: {', '.join(missing)}")
    return expected


def _validate_record(value: Any, tensor: str, line_number: int) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdapterBoundaryError(f"{tensor}.jsonl:{line_number}: record is not an object")
    if "id" not in value:
        raise AdapterBoundaryError(f"{tensor}.jsonl:{line_number}: id is missing")
    if "tensor" in value and value["tensor"] not in (None, tensor):
        raise AdapterBoundaryError(f"{tensor}.jsonl:{line_number}: tensor field mismatch")
    return value


def _validate_jsonl(path: Path, tensor: str) -> int:
    count = 0
    with path.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if len(raw) > MAX_RECORD_BYTES:
                raise AdapterBoundaryError(f"{tensor}.jsonl:{line_number}: record exceeds size bound")
            line = raw.decode("utf-8")
            if not line.strip():
                continue
            _validate_record(json.loads(line), tensor, line_number)
            count += 1
    return count


def _resolve_inside(path: Path, approved_root: Path, label: str) -> Path:
    if path.is_symlink():
        raise AdapterBoundaryError(f"{label} will not be a symlink")
    approved_root = approved_root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(approved_root)
    except ValueError as exc:
        raise AdapterBoundaryError(f"{label} escapes approved root") from exc
    return resolved


def validate_copy(
    source_root: Path,
    expected_hashes: Path,
    *,
    approved_root: Path | None = None,
    require_immutable: bool = True,
) -> tuple[dict[str, str], list[SourceFile], str]:
    source_input = source_root
    approved_input = approved_root if approved_root is not None else source_input.parent
    if approved_input.is_symlink():
        raise AdapterBoundaryError("approved root will not be a symlink")
    approved_root = approved_input.resolve()
    source_root = _resolve_inside(source_input, approved_root, "source root")
    expected_hashes = _resolve_inside(expected_hashes, approved_root, "expected hash manifest")
    if not source_root.is_dir():
        raise AdapterBoundaryError("source root will be a real directory")
    if require_immutable and _is_writable(source_root):
        raise AdapterBoundaryError("source root is writable; immutable copy required")

    expected = _load_expected_hashes(expected_hashes)
    expected_manifest_hash = sha256_file(expected_hashes)
    actual: dict[str, str] = {}
    files: list[SourceFile] = []
    visible = {path.name for path in source_root.iterdir()}
    unexpected = sorted(visible - {f"{name}.jsonl" for name in TENSORS})
    if unexpected:
        raise AdapterBoundaryError(f"unexpected source files: {', '.join(unexpected)}")

    for tensor in TENSORS:
        path = source_root / f"{tensor}.jsonl"
        if not path.is_file() or path.is_symlink():
            raise AdapterBoundaryError(f"missing or symlinked tensor file: {path.name}")
        if require_immutable and _is_writable(path):
            raise AdapterBoundaryError(f"tensor file is writable: {path.name}")
        digest = sha256_file(path)
        actual[tensor] = digest
        if digest != expected[tensor]:
            raise AdapterBoundaryError(
                f"hash drift for {tensor}: expected {expected[tensor]}, got {digest}"
            )
        files.append(SourceFile(tensor, path, digest, _validate_jsonl(path, tensor)))
    return actual, files, expected_manifest_hash


def observe(
    source_root: Path,
    expected_hashes: Path,
    query: str = "",
    limit: int = 20,
    *,
    approved_root: Path | None = None,
    require_immutable: bool = True,
    tensors: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    if limit < 1 or limit > 100:
        raise AdapterBoundaryError("limit will be between 1 and 100")
    actual, files, expected_manifest_hash = validate_copy(
        source_root,
        expected_hashes,
        approved_root=approved_root,
        require_immutable=require_immutable,
    )
    query_folded = query.casefold()
    matches: list[dict[str, Any]] = []
    selected_files = files if tensors is None else [item for item in files if item.tensor in tensors]
    for item in selected_files:
        with item.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if query_folded and query_folded not in json.dumps(record, ensure_ascii=False).casefold():
                    continue
                matches.append({
                    "tensor": item.tensor,
                    "line_number": line_number,
                    "record_id": record["id"],
                    "record": record,
                    "source_sha256": item.sha256,
                    "observation_only": True,
                    "admission_status": "not_admitted",
                })
                if len(matches) >= limit:
                    break
            if len(matches) >= limit:
                break

    post_hashes = {item.tensor: sha256_file(item.path) for item in files}
    post_manifest_hash = sha256_file(_resolve_inside(
        expected_hashes,
        approved_root if approved_root is not None else source_root.parent,
        "expected hash manifest",
    ))
    if post_hashes != actual:
        raise AdapterBoundaryError("source hash changed during observation")
    if post_manifest_hash != expected_manifest_hash:
        raise AdapterBoundaryError("expected hash manifest changed during observation")

    return {
        "schema_version": "0.1.0",
        "report": "phase1b-copy-read-observation",
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {
            "root": str(source_root.resolve()),
            "mode": "immutable_copy",
            "live_source": False,
            "expected_hashes": str(expected_hashes.resolve()),
            "tensor_hashes": actual,
            "post_observation_tensor_hashes": post_hashes,
            "expected_hashes_sha256": expected_manifest_hash,
            "post_observation_expected_hashes_sha256": post_manifest_hash,
            "record_counts": {item.tensor: item.record_count for item in selected_files},
        },
        "query": {"text": query, "limit": limit, "match_count": len(matches)},
        "observations": matches,
        "boundary": {
            "source_write_attempted": False,
            "pod_write_attempted": False,
            "admission_performed": False,
            "experience_created": False,
            "core_runtime_imported": False,
        },
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Observe an immutable copied DataQuad surface.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--expected-hashes", type=Path, required=True)
    parser.add_argument("--approved-root", type=Path, default=None)
    parser.add_argument("--query", default="")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    report = observe(
        args.source_root,
        args.expected_hashes,
        args.query,
        args.limit,
        approved_root=args.approved_root,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS Phase 1B copy-backed observation")
    print(f"REPORT {args.report.resolve()}")
    print("BOUNDARY immutable copy only; no Core import, source write, Pod write, or admission")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
