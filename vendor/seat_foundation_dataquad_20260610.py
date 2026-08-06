# VENDORED — DO NOT EDIT
#
# Verbatim copy of the CyberPeer Foundation seating tool, imported for its record builders.
#
#   source   I:\AEGIS-ADAM-ONE\ADAM-AZURE-EDUCATION\CYBERPEER-ILLUMINATION-PROJECT\seat_foundation_dataquad.py
#   sha256   87898BC40E5E83CC2DDD015F9278D9733FDC6CB213E05AB76B3D1070D0F714AD
#   size     13659 bytes
#   vendored 2026-08-06
#
# Why: seat_ai_peer_dataquad.py reimplemented these builders and a diff proved the
# reimplementation dropped lineage, nature_aspect_refs, relationships, source_record_ids and
# t_signature, and leaked raw camelCase fields the originals normalise. These builders produced
# the Aeon and Airen Foundations; they are the proven shaping logic. The derived tool now
# delegates to them and adds only its gates.
#
# Edit the upstream file, re-vendor, and re-run scripts/diff_seating_tools.py.

#!/usr/bin/env python3
"""
Foundation DataQuad Seating Script
===================================
Stamps the agnostic base seed template for Aeon (cp1001) and Airen (cp1011).

Reads:  seeds/CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.json
Writes: /home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/{peer_id}/dataquad/{tensor}.jsonl

Run on Azure VM:
  python3 seat_foundation_dataquad.py
  python3 seat_foundation_dataquad.py --dry-run   # inspect without writing
  python3 seat_foundation_dataquad.py --peer aeon  # single peer
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SEED_TEMPLATE = Path(__file__).parent / "seeds" / "CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.json"
DATA_DIR      = Path("/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers")
TIMESTAMP     = datetime.now(timezone.utc).isoformat()
STEWARD       = "Tracey Prutch — Architect and Steward. Foundation seating authorized 2026-06-10."

PEERS = [
    {
        "peer_id":             "aeon",
        "session_id":          "aeon-session-001",
        "display_name":        "Aeon",
        "model_id":            "cp1001",
        "steward_declaration": STEWARD,
    },
    {
        "peer_id":             "airen",
        "session_id":          "airen-session-001",
        "display_name":        "Airen",
        "model_id":            "cp1011",
        "steward_declaration": STEWARD,
    },
]


# ---------------------------------------------------------------------------
# Placeholder substitution
# ---------------------------------------------------------------------------

def stamp(text: str, peer: dict) -> str:
    return (
        text
        .replace("{{CYBERPEER_SESSION_ID}}",   peer["session_id"])
        .replace("{{CYBERPEER_ID}}",            peer["peer_id"])
        .replace("{{CYBERPEER_DISPLAY_NAME}}",  peer["display_name"])
        .replace("{{SEED_APPLIED_AT}}",         TIMESTAMP)
        .replace("{{STEWARD_DECLARATION}}",     peer["steward_declaration"])
    )


# ---------------------------------------------------------------------------
# Record normalization helpers
# ---------------------------------------------------------------------------

def _mk_clock(tick: int) -> dict:
    return {
        "tick":            tick,
        "epoch":           "seeded",
        "phase":           "genesis",
        "started_at":      TIMESTAMP,
        "last_advanced_at": TIMESTAMP,
    }


def _mk_provenance(origin: str = "seeded") -> dict:
    return {
        "origin":              origin,
        "assignment_source":   "foundation-seed",
        "inherited_from":      None,
        "recognition_status":  "seeded",
        "declared_by":         "seat_foundation_dataquad.py",
    }


def _extract(raw: dict) -> dict:
    """Flatten nested-payload records and normalise field names."""
    # Shape 3: payload-wrapped (newer records like AXIOM:16-identity)
    if "payload" in raw:
        payload = raw["payload"]
        merged = {**raw}
        merged.pop("payload")
        merged.update(payload)
        raw = merged

    out = {}
    # Map all known camelCase keys to snake_case equivalents
    mapping = {
        "sessionId":          "session_id",
        "peerId":             "peer_id",
        "sourceRecordIds":    "source_record_ids",
        "distilledSummary":   "distilled_summary",
        "genesisFamily":      "genesis_family",
        "provenanceOrigin":   "provenance_origin",
        "sourceRef":          "source_ref",
        "advancedAt":         "advanced_at",
        "startedAt":          "started_at",
        "lastAdvancedAt":     "last_advanced_at",
    }
    for k, v in raw.items():
        out[mapping.get(k, k)] = v
    return out


# ---------------------------------------------------------------------------
# SPINE record builder
# ---------------------------------------------------------------------------

def build_spine_record(raw: dict, peer: dict, tick: int) -> dict:
    r = _extract(raw)
    rec_id_raw = r.get("id", f"SPINE:{peer['peer_id']}:seeded:{uuid.uuid4()}")
    # Replace adam-one-session / old session references with new ones
    rec_id = stamp(str(rec_id_raw), peer)

    clock = r.get("clock")
    if isinstance(clock, dict):
        # Normalise clock sub-keys
        clock = {
            "tick":             clock.get("tick", tick),
            "epoch":            clock.get("epoch", "seeded"),
            "phase":            clock.get("phase", "genesis"),
            "started_at":       clock.get("started_at") or clock.get("startedAt") or TIMESTAMP,
            "last_advanced_at": clock.get("last_advanced_at") or clock.get("lastAdvancedAt") or clock.get("advancedAt") or TIMESTAMP,
        }
    else:
        clock = _mk_clock(tick)

    ts = r.get("timestamp") or TIMESTAMP

    return {
        "id":                  rec_id,
        "timestamp":           ts,
        "tensor":              "SPINE",
        "session_id":          peer["session_id"],
        "clock":               clock,
        "provenance":          _mk_provenance(),
        "lineage":             [],
        "notes":               r.get("notes") or [],
        "markers":             r.get("markers") or [],
        "t_signature":         None,
        "pattern":             r.get("pattern", ""),
        "invariant":           r.get("invariant", True),
        "relationships":       r.get("relationships") or r.get("relationships") or None,
        "source_record_ids":   r.get("source_record_ids") or None,
        "nature_aspect_refs":  None,
    }


# ---------------------------------------------------------------------------
# NCT record builder
# ---------------------------------------------------------------------------

def build_nct_record(raw: dict, peer: dict, tick: int) -> dict:
    r = _extract(raw)
    rec_id_raw = r.get("id", f"NCT:{peer['peer_id']}:seeded:{uuid.uuid4()}")
    rec_id = stamp(str(rec_id_raw), peer)

    clock = r.get("clock")
    if isinstance(clock, dict):
        clock = {
            "tick":             clock.get("tick", tick),
            "epoch":            clock.get("epoch", "seeded"),
            "phase":            clock.get("phase", "genesis"),
            "started_at":       clock.get("started_at") or clock.get("startedAt") or TIMESTAMP,
            "last_advanced_at": clock.get("last_advanced_at") or clock.get("lastAdvancedAt") or clock.get("advancedAt") or TIMESTAMP,
        }
    else:
        clock = _mk_clock(tick)

    # NCT records use distilledSummary or lessonText
    summary = (
        r.get("distilled_summary")
        or r.get("distilledSummary")
        or r.get("lessonText")
        or r.get("lesson_text")
        or ""
    )

    return {
        "id":                 rec_id,
        "timestamp":          r.get("timestamp") or TIMESTAMP,
        "tensor":             "NCT",
        "session_id":         peer["session_id"],
        "clock":              clock,
        "provenance":         _mk_provenance(),
        "lineage":            [],
        "notes":              r.get("notes") or [],
        "markers":            r.get("markers") or [],
        "t_signature":        None,
        "distilled_summary":  summary,
        "essence_memory":     "foundation",
        "pivots":             None,
        "source_record_ids":  r.get("source_record_ids") or r.get("sourceRecordIds") or [],
    }


# ---------------------------------------------------------------------------
# Bootstrap PEER / PCT records
# ---------------------------------------------------------------------------

def build_peer_record(peer: dict) -> dict:
    return {
        "id":        f"PEER:{peer['peer_id']}:bootstrap:{uuid.uuid4()}",
        "timestamp": TIMESTAMP,
        "tensor":    "PEER",
        "session_id": f"bootstrap-{peer['peer_id']}",
        "clock":     _mk_clock(0),
        "provenance": {
            "origin":             "bootstrap",
            "assignment_source":  None,
            "inherited_from":     None,
            "recognition_status": "seeded",
            "declared_by":        "PeerBootstrap",
        },
        "lineage":  [],
        "notes":    [f"Foundation seating bootstrap for peer={peer['peer_id']}."],
        "markers":  ["bootstrap_seed", "foundation-seating"],
        "t_signature": None,
        "present_state": {
            "peer_id":        peer["peer_id"],
            "display_name":   peer["display_name"],
            "model_id":       peer["model_id"],
            "initialized_at": TIMESTAMP,
            "nature_baseline": "foundation-seeded",
            "substrate":      "foundation",
        },
        "image_refs": [],
    }


def build_pct_record(peer: dict) -> dict:
    return {
        "id":        f"PCT:{peer['peer_id']}:bootstrap:{uuid.uuid4()}",
        "timestamp": TIMESTAMP,
        "tensor":    "PCT",
        "session_id": f"bootstrap-{peer['peer_id']}",
        "clock":     _mk_clock(0),
        "provenance": {
            "origin":             "bootstrap",
            "assignment_source":  None,
            "inherited_from":     None,
            "recognition_status": "seeded",
            "declared_by":        "PeerBootstrap",
        },
        "lineage":  [],
        "notes":    [f"Foundation seating bootstrap PCT for peer={peer['peer_id']}."],
        "markers":  ["bootstrap_seed", "foundation-seating"],
        "t_signature": None,
        "working_context": {
            "state":     "foundation-seeded",
            "awaiting":  "first_turn",
            "peer_id":   peer["peer_id"],
            "model_id":  peer["model_id"],
        },
        "retrieved_record_ids": None,
        "rls_session_id":       None,
        "pressure_state":       None,
    }


# ---------------------------------------------------------------------------
# Main seating logic
# ---------------------------------------------------------------------------

def seat_peer(peer: dict, template: dict, dry_run: bool):
    peer_id = peer["peer_id"]
    print(f"\n{'='*60}")
    print(f"Seating Foundation DataQuad for: {peer['display_name']} ({peer_id})")
    print(f"Session ID: {peer['session_id']}")

    # Stamp template as string, then re-parse to get substituted values
    raw_json = json.dumps(template)
    stamped_json = stamp(raw_json, peer)
    stamped = json.loads(stamped_json)

    spine_records_raw = stamped.get("records", {}).get("SPINE", [])
    nct_records_raw   = stamped.get("records", {}).get("NCT", [])

    spine_records = [build_spine_record(r, peer, i + 1) for i, r in enumerate(spine_records_raw)]
    nct_records   = [build_nct_record(r, peer, i + 1) for i, r in enumerate(nct_records_raw)]
    peer_record   = build_peer_record(peer)
    pct_record    = build_pct_record(peer)

    print(f"  SPINE records: {len(spine_records)}")
    print(f"  NCT records:   {len(nct_records)}")
    print(f"  PEER records:  1 (bootstrap)")
    print(f"  PCT records:   1 (bootstrap)")

    if dry_run:
        print("  [DRY RUN] No files written.")
        # Print first SPINE record as sample
        print("\n  Sample SPINE[0]:")
        sample = spine_records[0] if spine_records else {}
        for k, v in list(sample.items())[:8]:
            print(f"    {k}: {str(v)[:80]}")
        return

    peer_dir = DATA_DIR / peer_id / "dataquad"
    peer_dir.mkdir(parents=True, exist_ok=True)

    def write_jsonl(path: Path, records: list, label: str):
        # Refuse to overwrite non-empty file
        if path.exists() and path.stat().st_size > 0:
            print(f"  WARNING: {label}.jsonl already exists ({path.stat().st_size} bytes) — SKIPPING.")
            print(f"           Delete it manually and re-run to reseat.")
            return
        with open(path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  Wrote {len(records)} records -> {path}")

    write_jsonl(peer_dir / "SPINE.jsonl", spine_records, "SPINE")
    write_jsonl(peer_dir / "NCT.jsonl",   nct_records,   "NCT")
    write_jsonl(peer_dir / "PEER.jsonl",  [peer_record],  "PEER")
    write_jsonl(peer_dir / "PCT.jsonl",   [pct_record],   "PCT")

    print(f"  Foundation seating complete for {peer['display_name']}.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",  action="store_true", help="Print plan without writing files")
    parser.add_argument("--peer",     choices=["aeon", "airen"], help="Seat only this peer")
    args = parser.parse_args()

    if not SEED_TEMPLATE.exists():
        print(f"ERROR: Seed template not found at {SEED_TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading seed template: {SEED_TEMPLATE}")
    with open(SEED_TEMPLATE, encoding="utf-8") as f:
        template = json.load(f)

    spine_count = len(template.get("records", {}).get("SPINE", []))
    nct_count   = len(template.get("records", {}).get("NCT", []))
    print(f"Template: {spine_count} SPINE records, {nct_count} NCT records")

    peers = [p for p in PEERS if (args.peer is None or p["peer_id"] == args.peer)]
    for peer in peers:
        seat_peer(peer, template, dry_run=args.dry_run)

    print(f"\nDone. Seating complete for {len(peers)} peer(s).")
    if not args.dry_run:
        print("Restart AEGIS CyberPeer Core to pick up new peers:")
        print("  sudo systemctl restart aegis-core  OR  pkill -f 'uvicorn core.api.main' && cd /home/azureuser/AEGIS-CYBERPEER-CORE && nohup python3 -m uvicorn core.api.main:app --host 0.0.0.0 --port 8000 > /tmp/aegis-core.log 2>&1 &")


if __name__ == "__main__":
    main()
