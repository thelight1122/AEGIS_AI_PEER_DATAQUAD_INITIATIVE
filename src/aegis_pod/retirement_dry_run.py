from __future__ import annotations

"""
AEGIS DataQuad Stage-1 Retirement — LOCAL, READ-ONLY DRY-RUN analyzer.

This tool SIMULATES Stage-1 retirement (gap-spec §5 / §7 step 2) against an already-
exported LOCAL copy of a peer's DataQuad. It NEVER performs retirement:

  * It does not mutate, delete, move, or rename any record or file.
  * It does not touch any live system, SSH/SCP/HTTP anywhere, or spawn subprocesses.
  * It does not write into I:\\AEGIS-CYBERPEER-CORE (the live runtime tree).
  * The exported source records are opened READ-ONLY.

"Archive-not-delete" is doctrine even in projection (Canon: decay != deletion;
Amendment 4 hash-proof): this tool only PROJECTS a conceptual archive destination and
computes a source hash-proof for each candidate. It never creates that archive.

There is deliberately NO --apply capability in this version. Dry-run only.

Stage-1 (what is SIMULATED, never done):
  * PCT -> NCT: PCT records past an inactivity/age window would condense into NCT relics;
    their source PCT records would be archived (hash-proof, rename-not-delete) and pruned
    from the live tensor.
  * PEER -> SPINE/NCT: established+stable PEER records would promote; sources archived.
    PEER is identity substrate (Axiom 16) and is handled CONSERVATIVELY — records that are
    SPINE-anchored, high-uniqueness, recent, or contested are EXCLUDED from retirement.
"""

import argparse
import hashlib
import json
import statistics
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

TOOL_ID = "aegis-dataquad-stage1-retirement-dry-run"
SCHEMA_VERSION = "0.1.0"
MODE = "dry-run-only"  # there is no apply path in this tool, by design.

TENSORS = ("PEER", "PCT", "NCT", "SPINE")

# Defaults for the configurable heuristics (see module docstring / gap-spec §5).
DEFAULT_PCT_INACTIVITY_DAYS = 14.0
DEFAULT_PEER_STABILITY_DAYS = 14.0
DEFAULT_PEER_MIN_CONFIRMATIONS = 2
DEFAULT_CONTESTED_MARKERS = (
    "contested",
    "contradiction",
    "contradicted",
    "disputed",
    "retract",
    "retraction",
    "correction",
    "corrected",
    "overturned",
)

# Roots this tool will NEVER read from or write into. Live runtime lives on I:.
FORBIDDEN_PATH_FRAGMENTS = ("aegis-cyberpeer-core",)
FORBIDDEN_DRIVE_PREFIXES = ("i:",)


# --------------------------------------------------------------------------------------
# Safety guards
# --------------------------------------------------------------------------------------
def assert_local_readonly_path(path: Path, *, purpose: str) -> Path:
    """Refuse any path that points at the live runtime tree or a forbidden drive.

    This is a belt-and-suspenders guard: the tool never opens source files for writing
    regardless, but this makes the boundary explicit and surfaces the shortfall loudly if misconfigured.
    """
    resolved = path.resolve()
    text = str(resolved).lower().replace("\\", "/")
    drive = (resolved.drive or "").lower()
    if drive in FORBIDDEN_DRIVE_PREFIXES:
        raise ValueError(
            f"REFUSED ({purpose}): path {resolved} is on forbidden drive {drive!r}. "
            "This tool will not read or write the live runtime tree."
        )
    for frag in FORBIDDEN_PATH_FRAGMENTS:
        if frag in text:
            raise ValueError(
                f"REFUSED ({purpose}): path {resolved} contains forbidden fragment {frag!r}."
            )
    return resolved


# --------------------------------------------------------------------------------------
# Parsing helpers
# --------------------------------------------------------------------------------------
def parse_iso(ts: str | None) -> datetime | None:
    if not ts or not isinstance(ts, str):
        return None
    raw = ts.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        # Fall back: drop fractional seconds if malformed.
        try:
            head = raw.split(".")[0]
            if "+" not in head and head.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
                head += "+00:00"
            dt = datetime.fromisoformat(head)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_text(value: Any) -> str:
    return " ".join(str(value).lower().split())


@dataclass
class RecordRow:
    """One record from an exported tensor JSONL file (kept in memory read-only)."""

    lineno: int
    raw: str  # the exact JSONL line (without trailing newline)
    record: dict[str, Any]
    tensor: str
    record_id: str
    timestamp: datetime | None
    body: dict[str, Any] = field(default_factory=dict)

    @property
    def byte_len(self) -> int:
        return len(self.raw.encode("utf-8"))

    @property
    def content_key(self) -> str:
        """Normalized content signal, used for PEER confirmation/uniqueness counting."""
        b = self.body
        for key in ("presentState", "workingContext", "sourceSnapshot", "distilledSummary", "pattern"):
            v = b.get(key)
            if isinstance(v, dict):
                sig = v.get("signal") or v.get("definition")
                if sig:
                    return _normalize_text(sig)
            elif isinstance(v, str) and v.strip():
                return _normalize_text(v)
        return _normalize_text(self.record_id)


def iter_tensor(path: Path) -> Iterable[RecordRow]:
    with path.open("r", encoding="utf-8") as handle:
        for i, line in enumerate(handle):
            stripped = line.rstrip("\n")
            if not stripped.strip():
                continue
            try:
                rec = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            body = rec.get("body")
            if not isinstance(body, dict):
                body = {}
            yield RecordRow(
                lineno=i,
                raw=stripped,
                record=rec,
                tensor=str(rec.get("tensor", "")),
                record_id=str(rec.get("record_id") or rec.get("id") or f"line-{i}"),
                timestamp=parse_iso(rec.get("timestamp_utc") or body.get("timestamp")),
                body=body,
            )


def load_tensor(source_root: Path, tensor: str) -> list[RecordRow]:
    path = source_root / f"{tensor}.jsonl"
    if not path.exists():
        return []
    return list(iter_tensor(path))


# --------------------------------------------------------------------------------------
# Candidate detection signals
# --------------------------------------------------------------------------------------
def _references_spine(row: RecordRow) -> bool:
    """True if the record is SPINE-anchored (lineage / source refs / body point at SPINE)."""
    probes: list[Any] = [
        row.record.get("source_record_id"),
        row.record.get("lineage"),
        row.body.get("source_record_ids"),
        row.body.get("lineage"),
        row.body.get("canonId"),
        row.body.get("provenance"),
    ]
    for p in probes:
        if p is None:
            continue
        if "spine:" in json.dumps(p).lower():
            return True
    return False


def _is_contested(row: RecordRow, contested_markers: tuple[str, ...]) -> bool:
    fields: list[Any] = [row.body.get("markers"), row.body.get("notes"), row.body.get("tags")]
    blob = _normalize_text(json.dumps(fields))
    return any(tok in blob for tok in contested_markers)


def _projected_archive_dest(archive_root: str, tensor: str, record_id: str) -> str:
    safe = record_id.replace(":", "_").replace("/", "_").replace("\\", "_")
    # Conceptual destination string only — this path is NEVER created.
    return f"{archive_root}/{tensor}/{safe}.json"


# --------------------------------------------------------------------------------------
# Core analysis
# --------------------------------------------------------------------------------------
def analyze(
    source_root: Path,
    *,
    pct_inactivity_days: float = DEFAULT_PCT_INACTIVITY_DAYS,
    peer_stability_days: float = DEFAULT_PEER_STABILITY_DAYS,
    peer_min_confirmations: int = DEFAULT_PEER_MIN_CONFIRMATIONS,
    contested_markers: tuple[str, ...] = DEFAULT_CONTESTED_MARKERS,
    now: datetime | None = None,
    archive_root: str = "pod/records/_archive/retired",
) -> dict[str, Any]:
    source_root = assert_local_readonly_path(source_root, purpose="source-root")

    tensors: dict[str, list[RecordRow]] = {t: load_tensor(source_root, t) for t in TENSORS}

    # Reference "now" for the age window: max observed timestamp unless overridden.
    all_ts = [r.timestamp for rows in tensors.values() for r in rows if r.timestamp]
    reference_now = now or (max(all_ts) if all_ts else datetime.now(timezone.utc))

    def age_days(row: RecordRow) -> float | None:
        if row.timestamp is None:
            return None
        return (reference_now - row.timestamp).total_seconds() / 86400.0

    # ---- Per-tensor current counts + byte sizes -------------------------------------
    tensor_stats: dict[str, dict[str, Any]] = {}
    for t, rows in tensors.items():
        path = source_root / f"{t}.jsonl"
        tensor_stats[t] = {
            "records": len(rows),
            "content_bytes": sum(r.byte_len for r in rows),
            "file_bytes": path.stat().st_size if path.exists() else 0,
            "present": path.exists(),
        }

    # Data-driven per-relic size estimate (median NCT record content bytes).
    nct_sizes = [r.byte_len for r in tensors["NCT"] if r.byte_len]
    est_relic_bytes = int(statistics.median(nct_sizes)) if nct_sizes else 0

    # ---- PCT retirement candidates (age/inactivity heuristic) -----------------------
    pct_candidates: list[dict[str, Any]] = []
    pct_new_relics = 0
    for row in tensors["PCT"]:
        a = age_days(row)
        if a is None or a < pct_inactivity_days:
            continue
        already_condensed = bool(row.body.get("retired")) and bool(row.body.get("retiredToId"))
        if already_condensed:
            relic_id = str(row.body.get("retiredToId"))
            relic_projected = False
        else:
            relic_id = f"NCT:PROJECTED-FROM-PCT:{sha256_hex(row.raw.encode('utf-8'))[:16]}"
            relic_projected = True
            pct_new_relics += 1
        pct_candidates.append(
            {
                "record_id": row.record_id,
                "tensor": "PCT",
                "age_days": round(a, 3),
                "clock_tick": (row.body.get("clock") or {}).get("tick") if isinstance(row.body.get("clock"), dict) else None,
                "reference_count": row.body.get("referenceCount"),
                "already_condensed": already_condensed,
                "source_hash": sha256_hex(row.raw.encode("utf-8")),
                "source_hash_scope": "raw_jsonl_record_line_utf8",
                "declared_source_hash": row.record.get("source_hash"),
                "source_bytes": row.byte_len,
                "projected_archive_dest": _projected_archive_dest(archive_root, "PCT", row.record_id),
                "relic_id": relic_id,
                "relic_projected": relic_projected,
                "lineage_link": {"relic_id": relic_id, "source_record_id": row.record_id},
            }
        )

    # ---- PEER promotion candidates + caution exclusions -----------------------------
    # Confirmation / uniqueness counting over PEER content signals.
    content_counts: dict[str, int] = {}
    for row in tensors["PEER"]:
        content_counts[row.content_key] = content_counts.get(row.content_key, 0) + 1

    peer_candidates: list[dict[str, Any]] = []
    peer_exclusions: list[dict[str, Any]] = []
    exclusion_reason_counts: dict[str, int] = {}

    def _exclude(row: RecordRow, reason: str, detail: dict[str, Any]) -> None:
        exclusion_reason_counts[reason] = exclusion_reason_counts.get(reason, 0) + 1
        peer_exclusions.append(
            {"record_id": row.record_id, "tensor": "PEER", "reason": reason, **detail}
        )

    for row in tensors["PEER"]:
        a = age_days(row)
        dup_count = content_counts.get(row.content_key, 1)
        spine_anchored = _references_spine(row)
        contested = _is_contested(row, contested_markers)

        # Conservative caution rules (Axiom 16): exclude first, promote only what survives.
        if a is None:
            _exclude(row, "no_timestamp_cannot_age", {})
            continue
        if a < peer_stability_days:
            _exclude(row, "recent_experience", {"age_days": round(a, 3)})
            continue
        if spine_anchored:
            _exclude(row, "spine_anchored", {"age_days": round(a, 3)})
            continue
        if contested:
            _exclude(row, "contested", {"age_days": round(a, 3)})
            continue
        if dup_count < peer_min_confirmations:
            _exclude(
                row,
                "high_uniqueness_unique_experience",
                {"age_days": round(a, 3), "confirmations": dup_count},
            )
            continue

        # Survivor: established (repeatedly reinforced) + stable (old) + not anchored/contested.
        invariant = bool(row.body.get("invariant"))
        relic_tensor = "SPINE" if invariant else "NCT"
        relic_id = f"{relic_tensor}:PROJECTED-FROM-PEER:{sha256_hex(row.raw.encode('utf-8'))[:16]}"
        peer_candidates.append(
            {
                "record_id": row.record_id,
                "tensor": "PEER",
                "age_days": round(a, 3),
                "confirmations": dup_count,
                "spine_anchored": False,
                "contested": False,
                "promote_to": relic_tensor,
                "source_hash": sha256_hex(row.raw.encode("utf-8")),
                "source_hash_scope": "raw_jsonl_record_line_utf8",
                "declared_source_hash": row.record.get("source_hash"),
                "source_bytes": row.byte_len,
                "projected_archive_dest": _projected_archive_dest(archive_root, "PEER", row.record_id),
                "relic_id": relic_id,
                "relic_projected": True,
                "lineage_link": {"relic_id": relic_id, "source_record_id": row.record_id},
            }
        )

    peer_new_relics = len(peer_candidates)

    # ---- Projected live-tensor shrinkage --------------------------------------------
    pct_removed_bytes = sum(c["source_bytes"] for c in pct_candidates)
    peer_removed_bytes = sum(c["source_bytes"] for c in peer_candidates)
    projected_new_relics = pct_new_relics + peer_new_relics

    def _shrink(tensor: str, removed_records: int, removed_bytes: int) -> dict[str, Any]:
        cur_records = tensor_stats[tensor]["records"]
        cur_bytes = tensor_stats[tensor]["content_bytes"]
        return {
            "current_records": cur_records,
            "current_content_bytes": cur_bytes,
            "retired_out_records": removed_records,
            "retired_out_bytes": removed_bytes,
            "projected_remaining_records": cur_records - removed_records,
            "projected_remaining_content_bytes": cur_bytes - removed_bytes,
            "projected_record_reduction_pct": round(100.0 * removed_records / cur_records, 2) if cur_records else 0.0,
            "projected_byte_reduction_pct": round(100.0 * removed_bytes / cur_bytes, 2) if cur_bytes else 0.0,
        }

    shrinkage = {
        "PCT": _shrink("PCT", len(pct_candidates), pct_removed_bytes),
        "PEER": _shrink("PEER", len(peer_candidates), peer_removed_bytes),
        "projected_new_relics": {
            "count": projected_new_relics,
            "from_pct": pct_new_relics,
            "from_peer": peer_new_relics,
            "estimated_bytes_added": projected_new_relics * est_relic_bytes,
            "estimated_per_relic_bytes": est_relic_bytes,
            "estimate_basis": "median NCT record content bytes",
        },
        "net_live_tensor_bytes_removed": pct_removed_bytes + peer_removed_bytes,
        "net_live_tensor_records_removed": len(pct_candidates) + len(peer_candidates),
    }

    manifest = pct_candidates + peer_candidates

    report: dict[str, Any] = {
        "tool_id": TOOL_ID,
        "schema_version": SCHEMA_VERSION,
        "mode": MODE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "boundary": {
            "read_only": True,
            "mutations": "none",
            "archive_action": "PROJECTED-ONLY (archive-not-delete doctrine; no file created/moved/renamed/deleted)",
            "live_reach": "none (no ssh/scp/http/subprocess; no writes under I:)",
            "apply_capability": "absent-by-design",
        },
        "source_root": str(source_root),
        "reference_now": reference_now.isoformat(),
        "parameters": {
            "pct_inactivity_days": pct_inactivity_days,
            "peer_stability_days": peer_stability_days,
            "peer_min_confirmations": peer_min_confirmations,
            "contested_markers": list(contested_markers),
            "archive_root": archive_root,
        },
        "tensor_stats": tensor_stats,
        "stage1_candidates": {
            "pct_retirement": {
                "count": len(pct_candidates),
                "already_condensed": sum(1 for c in pct_candidates if c["already_condensed"]),
                "needs_new_relic": pct_new_relics,
            },
            "peer_promotion": {
                "count": len(peer_candidates),
                "promote_to_spine": sum(1 for c in peer_candidates if c["promote_to"] == "SPINE"),
                "promote_to_nct": sum(1 for c in peer_candidates if c["promote_to"] == "NCT"),
            },
        },
        "peer_exclusions": {
            "total": len(peer_exclusions),
            "by_reason": exclusion_reason_counts,
        },
        "projected_shrinkage": shrinkage,
        "archive_manifest_summary": {
            "total_entries": len(manifest),
            "pct_entries": len(pct_candidates),
            "peer_entries": len(peer_candidates),
            "hash_scope": "raw_jsonl_record_line_utf8",
        },
    }

    return {
        "report": report,
        "manifest": manifest,
        "peer_exclusions_full": peer_exclusions,
    }


# --------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------
def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_manifest_jsonl(path: Path, manifest: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in manifest:
            handle.write(json.dumps(entry, sort_keys=True))
            handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="LOCAL read-only DRY-RUN analyzer for AEGIS DataQuad Stage-1 retirement. "
        "Simulates PCT->NCT retirement and PEER->SPINE/NCT promotion; mutates nothing. "
        "There is no --apply path.",
    )
    parser.add_argument("--root", default=".", help="AEGIS-POD-ARCHITECTURE repo root")
    parser.add_argument(
        "--source-root",
        default="stage-gabe-out/CP-1003-GABE/pod/records",
        help="Exported DataQuad records dir (relative to --root unless absolute). Read-only.",
    )
    parser.add_argument("--pct-inactivity-days", type=float, default=DEFAULT_PCT_INACTIVITY_DAYS)
    parser.add_argument("--peer-stability-days", type=float, default=DEFAULT_PEER_STABILITY_DAYS)
    parser.add_argument("--peer-min-confirmations", type=int, default=DEFAULT_PEER_MIN_CONFIRMATIONS)
    parser.add_argument(
        "--now",
        default="",
        help="Override reference 'now' as ISO-8601 UTC (default: max timestamp in the export).",
    )
    parser.add_argument(
        "--contested-markers",
        default="",
        help="Comma-separated extra contested tokens (added to defaults).",
    )
    parser.add_argument("--archive-root", default="pod/records/_archive/retired", help="Conceptual archive root (never created).")
    parser.add_argument("--output", default="", help="Report JSON path (default under reports/runtime/).")
    parser.add_argument("--no-write", action="store_true", help="Compute and print summary only; write no files.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    src = Path(args.source_root)
    source_root = src if src.is_absolute() else (root / src)

    now = None
    if args.now:
        now = parse_iso(args.now)
        if now is None:
            print(f"ERROR could not parse --now {args.now!r}")
            return 1

    contested = tuple(DEFAULT_CONTESTED_MARKERS) + tuple(
        tok.strip().lower() for tok in args.contested_markers.split(",") if tok.strip()
    )

    result = analyze(
        source_root,
        pct_inactivity_days=args.pct_inactivity_days,
        peer_stability_days=args.peer_stability_days,
        peer_min_confirmations=args.peer_min_confirmations,
        contested_markers=contested,
        now=now,
        archive_root=args.archive_root,
    )
    report = result["report"]

    if not args.no_write:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = Path(args.output) if args.output else (root / "reports" / "runtime" / f"retirement-dry-run-report-{stamp}.json")
        out = assert_local_readonly_path(out, purpose="report-output")
        manifest_path = out.with_name(out.stem.replace("report", "manifest") + ".jsonl")
        exclusions_path = out.with_name(out.stem.replace("report", "peer-exclusions") + ".jsonl")
        report["archive_manifest_path"] = str(manifest_path)
        report["peer_exclusions_path"] = str(exclusions_path)
        write_json(out, report)
        write_manifest_jsonl(manifest_path, result["manifest"])
        write_manifest_jsonl(exclusions_path, result["peer_exclusions_full"])
        print(f"REPORT {out}")
        print(f"MANIFEST {manifest_path} ({len(result['manifest'])} entries)")
        print(f"EXCLUSIONS {exclusions_path} ({len(result['peer_exclusions_full'])} entries)")

    ts = report["tensor_stats"]
    sh = report["projected_shrinkage"]
    print("=== Stage-1 retirement DRY-RUN (nothing mutated) ===")
    for t in TENSORS:
        print(f"  {t}: {ts[t]['records']} records, {ts[t]['content_bytes']} content bytes")
    print(f"  PCT retirement candidates: {report['stage1_candidates']['pct_retirement']['count']}")
    print(f"  PEER promotion candidates: {report['stage1_candidates']['peer_promotion']['count']}")
    print(f"  PEER exclusions: {report['peer_exclusions']['total']} {report['peer_exclusions']['by_reason']}")
    print(f"  Projected PCT shrink: {sh['PCT']['retired_out_records']} recs / {sh['PCT']['retired_out_bytes']} bytes ({sh['PCT']['projected_byte_reduction_pct']}%)")
    print(f"  Projected PEER shrink: {sh['PEER']['retired_out_records']} recs / {sh['PEER']['retired_out_bytes']} bytes ({sh['PEER']['projected_byte_reduction_pct']}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
