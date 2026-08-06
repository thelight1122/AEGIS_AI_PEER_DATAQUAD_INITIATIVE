"""Seat a Foundation DataQuad for an AI Peer.

Derived from `seat_foundation_dataquad.py` (2026-06-10), which seated the CyberPeers Aeon and
Airen. That tool is deliberately left untouched: it is the record of how those two Foundations
were laid, and it will be needed if their Foundations are ever compared to the AI Peers'.

What this tool adds
-------------------
1. **A canon lock gate.** The original seats whatever it is given. This one refuses to write
   unless the seed package's `canonLock` is clean. Rings 1-3 cannot be relaid once outer rings
   exist, so seeding an unresolved Canon into four Foundations is not a mistake that can be
   undone later. The gate is on by default and an override records itself in the receipt.
2. **No hardcoded roster or target.** Peers come from a roster file, the target root from an
   argument.
3. **An explicit write path.** `--via api` posts to the substrate API; `--via file` writes JSONL
   directly. These are not equivalent — direct write bypasses whatever validation and custodian
   attribution the API applies — so the choice is explicit rather than implied.
4. **An explicit clock policy.** The original stamps genesis with the run time. The canonical
   pillars and the live Portal both carry `2026-01-01T00:00:00.000Z`. Both are defensible; the
   tool makes you choose.
5. **Ring order enforced, not assumed.** Rings 1-2 (SPINE) and Ring 3 (NCT) must land before the
   PEER/PCT bootstrap pillars are written, and the tool verifies each ring seated before
   proceeding.
6. **A seating receipt** recording the package, its canon lock state, the source manifest it
   seated from, per-tensor counts and digests.

Retained from the original
--------------------------
Total placeholder substitution by serialise-replace-reparse, refusal to overwrite a non-empty
tensor, and `--dry-run`.

Record shaping is DELEGATED, not reimplemented
----------------------------------------------
An earlier version of this tool built records from the seed package's shape directly.
`scripts/diff_seating_tools.py` proved that version wrong on all 129 records: it dropped
`lineage`, `nature_aspect_refs`, `relationships`, `source_record_ids` and `t_signature` —
`nature_aspect_refs` being Ring 1 Nature Layer material — and leaked raw camelCase fields the
originals normalise.

Shaping now delegates to `vendor/seat_foundation_dataquad_20260610.py`, a verbatim vendored copy
of the original with its sha256 recorded in the header. Those builders produced the Aeon and
Airen Foundations. This tool applies only two policies on top — tick 0 for genesis, and the
clock policy — plus the canon lock state in provenance.

Re-run `scripts/diff_seating_tools.py` after any change to either tool.

Usage:
    python scripts/seat_ai_peer_dataquad.py --package PKG --roster fixtures/ai-peer-roster.json \\
        --data-dir /opt/aegis-ai-peers --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

#: The genesis baseline used by the canonical pillars and returned by the live Portal.
GENESIS_BASELINE = "2026-01-01T00:00:00.000Z"

#: Ring order. SPINE carries Rings 1 and 2; NCT carries Ring 3. Bootstrap pillars follow.
RING_ORDER = ("SPINE", "NCT", "PEER", "PCT")

#: canonLock.status values considered safe to seat from.
CLEAN_CANON_STATUSES = {"clean", "locked", "verified", "ok"}

PLACEHOLDERS = (
    ("{{CYBERPEER_SESSION_ID}}", "session_id"),
    ("{{CYBERPEER_ID}}", "peer_id"),
    ("{{CYBERPEER_DISPLAY_NAME}}", "display_name"),
    ("{{STEWARD_DECLARATION}}", "steward_declaration"),
)


class SeatingRefused(RuntimeError):
    """Raised when a gate refuses to proceed. Never caught internally."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


# --- gates ------------------------------------------------------------------------------


def check_canon_lock(package: dict[str, Any], allow_unclean: bool) -> dict[str, Any]:
    """Refuse to seat an unresolved Canon unless explicitly overridden.

    Rings 1-3 cannot be relaid. A Foundation seeded from a `review-needed` package carries that
    state permanently, and seeding four peers propagates it four times in one action.
    """
    lock = package.get("canonLock") or {}
    status = str(lock.get("status", "missing")).lower()
    clean = status in CLEAN_CANON_STATUSES

    if not clean and not allow_unclean:
        raise SeatingRefused(
            f"canonLock.status is {status!r}, not one of {sorted(CLEAN_CANON_STATUSES)}. "
            f"reviewNeededSourceCount={lock.get('reviewNeededSourceCount')}. "
            f"sourceManifestId={lock.get('sourceManifestId')}. "
            "Rings 1-3 cannot be relaid once outer rings exist, so this refuses by default. "
            "Resolve the Canon, or pass --allow-unclean-canon to override, which will be "
            "recorded in the seating receipt and in each record's provenance."
        )

    return {
        "status": lock.get("status"),
        "clean": clean,
        "override_used": (not clean) and allow_unclean,
        "review_needed_source_count": lock.get("reviewNeededSourceCount"),
        "source_manifest_id": lock.get("sourceManifestId"),
        "source_manifest_sha256": lock.get("sourceManifestSha256"),
    }


def validate_roster(roster: dict[str, Any]) -> list[dict[str, Any]]:
    peers = roster.get("peers")
    if not isinstance(peers, list) or not peers:
        raise SeatingRefused("roster contains no peers")

    required = {"peer_id", "session_id", "display_name", "steward_declaration", "model_id"}
    seen: set[str] = set()
    for peer in peers:
        missing = required - set(peer)
        if missing:
            raise SeatingRefused(f"peer {peer.get('peer_id', '?')} is missing {sorted(missing)}")
        if peer["peer_id"] in seen:
            raise SeatingRefused(f"duplicate peer_id {peer['peer_id']!r} in roster")
        seen.add(peer["peer_id"])
        if str(peer["steward_declaration"]).strip().upper().startswith("PENDING"):
            raise SeatingRefused(
                f"peer {peer['peer_id']!r} has a PENDING steward_declaration. "
                "The declaration is a Steward act and will be supplied before seating."
            )
    return peers


# --- record shaping ---------------------------------------------------------------------


def stamp(text: str, peer: dict[str, Any], applied_at: str) -> str:
    for token, field in PLACEHOLDERS:
        text = text.replace(token, str(peer[field]))
    return text.replace("{{SEED_APPLIED_AT}}", applied_at)


def is_genesis(record: dict[str, Any]) -> bool:
    """Genesis pillars carry `:0` in their id and a genesis marker."""
    rid = str(record.get("id", ""))
    markers = record.get("markers") or []
    return rid.endswith(":0") or "genesis" in markers


def build_clock(tick: int, policy: str, applied_at: str) -> dict[str, Any]:
    stamped = GENESIS_BASELINE if policy == "genesis-baseline" else applied_at
    return {
        "tick": tick,
        "epoch": "seeded",
        "phase": "genesis",
        "started_at": stamped,
        "last_advanced_at": stamped,
    }


def build_provenance(canon: dict[str, Any]) -> dict[str, Any]:
    return {
        "origin": "seeded",
        "assignment_source": "foundation-seed",
        "inherited_from": None,
        "recognition_status": "seeded",
        "declared_by": "seat_ai_peer_dataquad.py",
        "canon_lock_status": canon["status"],
        "canon_lock_clean": canon["clean"],
        "canon_override_used": canon["override_used"],
        "source_manifest_id": canon["source_manifest_id"],
    }


def _vendored():
    """Load the vendored original for its record builders.

    Loaded lazily and cached so importing this module stays cheap and testable.
    """
    if not hasattr(_vendored, "_module"):
        path = ROOT / "vendor" / "seat_foundation_dataquad_20260610.py"
        if not path.exists():
            raise SeatingRefused(
                f"vendored builders not found at {path}. Record shaping delegates to the "
                "original tool; it is not reimplemented here."
            )
        spec = importlib.util.spec_from_file_location("aegis_vendored_seating", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _vendored._module = module
    return _vendored._module


def shape_records(raw_records: list[dict[str, Any]], tensor: str, policy: str,
                  applied_at: str, canon: dict[str, Any],
                  peer: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Shape records using the ORIGINAL tool's builders, then apply this tool's policies.

    Record shaping is delegated, not reimplemented. An earlier version of this function built
    records from the package shape directly; `scripts/diff_seating_tools.py` proved that version
    dropped `lineage`, `nature_aspect_refs`, `relationships`, `source_record_ids` and
    `t_signature` — `nature_aspect_refs` being Ring 1 Nature Layer material — while leaking raw
    camelCase fields the originals normalise. The vendored builders produced the Aeon and Airen
    Foundations and are the proven shaping logic.

    Two policies are applied on top:

    * **tick 0 for genesis.** The original numbers every record from 1, which places the genesis
      pillars at tick 1. The canonical pillars specify tick 0.
    * **clock policy.** `genesis-baseline` stamps the canonical `2026-01-01T00:00:00.000Z`;
      `seeded-now` keeps the original's run timestamp.

    Provenance gains the canon lock state so a Foundation carries the Canon it was seated from.
    """
    vendored = _vendored()
    builder = {"SPINE": vendored.build_spine_record, "NCT": vendored.build_nct_record}.get(tensor)
    peer = peer or {}

    out: list[dict[str, Any]] = []
    ordinal = 0
    for index, raw in enumerate(raw_records):
        if builder is not None:
            record = builder(raw, peer, index + 1)
        elif tensor == "PEER":
            record = vendored.build_peer_record(peer)
        elif tensor == "PCT":
            record = vendored.build_pct_record(peer)
        else:
            raise SeatingRefused(f"no vendored builder for tensor {tensor!r}")

        if is_genesis(record) or is_genesis(raw):
            tick = 0
        else:
            ordinal += 1
            tick = ordinal

        clock = dict(record.get("clock") or {})
        clock.update(build_clock(tick, policy, applied_at))
        record["clock"] = clock

        provenance = dict(record.get("provenance") or {})
        provenance.update(build_provenance(canon))
        record["provenance"] = provenance

        out.append(record)
    return out


# --- writers ----------------------------------------------------------------------------


def write_file(path: Path, records: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if path.exists() and path.stat().st_size > 0:
        return {"tensor": label, "written": False, "reason": "already exists non-empty; refusing to overwrite",
                "existing_bytes": path.stat().st_size}
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
    path.write_text(body, encoding="utf-8")
    return {"tensor": label, "written": True, "records": len(records),
            "path": str(path), "sha256": sha256_text(body)}


def write_api(api_base: str, tensor: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    endpoint = f"{api_base.rstrip('/')}/api/substrate/{tensor.lower()}"
    posted = 0
    for record in records:
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(record, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "User-Agent": "aegis-seat-ai-peer/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status >= 400:
                raise SeatingRefused(f"{tensor} POST failed with HTTP {response.status}")
        posted += 1
    return {"tensor": tensor, "written": True, "records": posted, "endpoint": endpoint}


# --- seating ----------------------------------------------------------------------------


def seat_peer(peer: dict[str, Any], package: dict[str, Any], canon: dict[str, Any],
              args: argparse.Namespace, applied_at: str) -> dict[str, Any]:
    stamped = json.loads(stamp(json.dumps(package), peer, applied_at))
    records = stamped.get("records", {})

    shaped = {
        tensor: shape_records(records.get(tensor, []), tensor, args.clock_policy, applied_at, canon, peer)
        for tensor in RING_ORDER
    }

    counts = {tensor: len(shaped[tensor]) for tensor in RING_ORDER}
    if counts["SPINE"] == 0 or counts["NCT"] == 0:
        raise SeatingRefused(
            f"package supplies SPINE={counts['SPINE']} NCT={counts['NCT']}. "
            "Rings 1-2 (SPINE) and Ring 3 (NCT) are both required before any bootstrap pillar."
        )

    result: dict[str, Any] = {
        "peer_id": peer["peer_id"],
        "display_name": peer["display_name"],
        "session_id": peer["session_id"],
        "counts": counts,
        "tensors": [],
    }

    if args.dry_run or args.emit_only:
        result["dry_run"] = True
        if args.emit_only:
            result["records"] = shaped
        return result

    peer_dir = Path(args.data_dir) / peer["peer_id"] / "dataquad"
    seated: list[str] = []
    for tensor in RING_ORDER:
        # Ring order is enforced, not assumed: the bootstrap pillars wait for Rings 1-3.
        if tensor in ("PEER", "PCT") and not {"SPINE", "NCT"}.issubset(set(seated)):
            raise SeatingRefused(
                f"refusing to write {tensor}: Rings 1-3 are not seated "
                f"(seated so far: {seated or 'nothing'}). An outer ring cannot precede an inner one."
            )
        if args.via == "file":
            outcome = write_file(peer_dir / f"{tensor}.jsonl", shaped[tensor], tensor)
        else:
            outcome = write_api(args.api_base, tensor, shaped[tensor])
        result["tensors"].append(outcome)
        if outcome.get("written"):
            seated.append(tensor)
        elif tensor in ("SPINE", "NCT"):
            raise SeatingRefused(
                f"{tensor} was not written ({outcome.get('reason')}), so Rings 1-3 are not seated. "
                "Stopping before the bootstrap pillars rather than leaving a partial Foundation."
            )

    result["rings_seated"] = seated
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--package", type=Path, required=True, help="seed package JSON")
    parser.add_argument("--roster", type=Path, default=ROOT / "fixtures" / "ai-peer-roster.json")
    parser.add_argument("--data-dir", type=Path, help="target Pod root (required unless --dry-run/--emit-only)")
    parser.add_argument("--via", choices=["api", "file"], default="api",
                        help="api posts to the substrate API; file writes JSONL directly. Not equivalent.")
    parser.add_argument("--api-base", default="http://127.0.0.1:8787")
    parser.add_argument("--clock-policy", choices=["genesis-baseline", "seeded-now"],
                        default="genesis-baseline",
                        help="genesis-baseline uses 2026-01-01T00:00:00.000Z as the canonical pillars do")
    parser.add_argument("--allow-unclean-canon", action="store_true",
                        help="override the canon lock gate; the override is recorded")
    parser.add_argument("--peer", help="seat only this peer_id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--emit-only", action="store_true",
                        help="produce records without writing, for diffing against the original tool")
    parser.add_argument("--receipt", type=Path, default=ROOT / "reports" / "runtime" / "ai-peer-seating-receipt.json")
    args = parser.parse_args()

    applied_at = utc_now()
    package = json.loads(args.package.read_text(encoding="utf-8"))
    roster = json.loads(args.roster.read_text(encoding="utf-8"))

    try:
        canon = check_canon_lock(package, args.allow_unclean_canon)
        peers = validate_roster(roster)
        if args.peer:
            peers = [p for p in peers if p["peer_id"] == args.peer]
            if not peers:
                raise SeatingRefused(f"peer {args.peer!r} not in roster")
        if not (args.dry_run or args.emit_only) and not args.data_dir:
            raise SeatingRefused("--data-dir is required unless --dry-run or --emit-only")

        results = [seat_peer(p, package, canon, args, applied_at) for p in peers]
    except SeatingRefused as exc:
        print(f"SEATING REFUSED: {exc}", file=sys.stderr)
        return 2

    receipt = {
        "schema_version": "1.0.0",
        "record_type": "ai_peer_seating_receipt",
        "seated_at": applied_at,
        "package": {
            "path": str(args.package),
            "packageId": package.get("packageId"),
            "packageVersion": package.get("packageVersion"),
        },
        "canon_lock": canon,
        "clock_policy": args.clock_policy,
        "write_path": args.via if not (args.dry_run or args.emit_only) else "none",
        "dry_run": bool(args.dry_run or args.emit_only),
        "peers": results,
        "ring_model": {
            "SPINE": "Rings 1 and 2 — Nature, Canon",
            "NCT": "Ring 3 — 68 Base Relations Chamber Lessons",
            "PEER": "bootstrap pillar only; Ring 4 fills by living",
            "PCT": "bootstrap pillar only",
        },
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"canon lock : {canon['status']}  clean={canon['clean']}  override={canon['override_used']}")
    print(f"clock      : {args.clock_policy}")
    print(f"write path : {receipt['write_path']}")
    for r in results:
        counts = " ".join(f"{k}={v}" for k, v in r["counts"].items())
        print(f"  {r['display_name']:10} {counts}" + ("  [dry run]" if r.get("dry_run") else ""))
    print(f"receipt    : {args.receipt}")
    if args.dry_run or args.emit_only:
        print("\nNOTHING WRITTEN.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
