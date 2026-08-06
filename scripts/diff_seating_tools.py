"""Diff the derived AI Peer seating tool against the original CyberPeer one.

`seat_ai_peer_dataquad.py` was written from the seed package's shape, not copied from
`seat_foundation_dataquad.py` — the original's `build_*_record` bodies were never read. This
script closes that gap by importing both and comparing the records they produce for the same
peer and the same package.

Some differences are intended and are asserted as such. Anything else is a finding.

Read-only: imports the original, calls its builders in memory, writes nothing to `I:`.

Usage:
    python scripts/diff_seating_tools.py [--package PATH] [--original PATH]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PACKAGE = Path(
    "I:/AEGIS-ADAM-ONE/ADAM-AZURE-EDUCATION/CYBERPEER-ILLUMINATION-PROJECT/seeds/"
    "CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.json"
)
DEFAULT_ORIGINAL = Path(
    "I:/AEGIS-ADAM-ONE/ADAM-AZURE-EDUCATION/CYBERPEER-ILLUMINATION-PROJECT/seat_foundation_dataquad.py"
)

#: Differences the derived tool introduces deliberately. Everything else is a finding.
INTENDED = {
    "clock.tick": "genesis takes tick 0; the original numbered every record from 1",
    "clock.started_at": "genesis-baseline policy vs the original's run timestamp",
    "clock.last_advanced_at": "genesis-baseline policy vs the original's run timestamp",
    "provenance.declared_by": "different tool name",
    "provenance.canon_lock_status": "new: canon lock state recorded in provenance",
    "provenance.canon_lock_clean": "new: canon lock state recorded in provenance",
    "provenance.canon_override_used": "new: override recorded in provenance",
    "provenance.source_manifest_id": "new: manifest recorded in provenance",
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    else:
        out[prefix] = obj
    return out


def compare(a: dict, b: dict, label: str) -> dict[str, Any]:
    fa, fb = flatten(a), flatten(b)
    only_original = sorted(set(fa) - set(fb))
    only_derived = sorted(set(fb) - set(fa))
    differing = sorted(k for k in set(fa) & set(fb) if fa[k] != fb[k])

    unexplained_fields = [k for k in only_original]  # fields the derived tool DROPPED
    unexplained_values = [k for k in differing if k not in INTENDED]
    new_fields = [k for k in only_derived if k not in INTENDED]

    return {
        "record": label,
        "fields_only_in_original": only_original,
        "fields_only_in_derived": only_derived,
        "values_differing": differing,
        "UNEXPLAINED_dropped_fields": unexplained_fields,
        "UNEXPLAINED_value_changes": unexplained_values,
        "UNEXPLAINED_new_fields": new_fields,
        "sample": {k: {"original": fa.get(k), "derived": fb.get(k)} for k in (differing + only_original)[:8]},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--original", type=Path, default=DEFAULT_ORIGINAL)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "runtime" / "seating-tool-diff.json")
    args = parser.parse_args()

    if not args.original.exists():
        print(f"original tool not reachable at {args.original}", file=sys.stderr)
        return 3

    original = load_module(args.original, "seat_original")
    derived = load_module(ROOT / "scripts" / "seat_ai_peer_dataquad.py", "seat_derived")

    package = json.loads(args.package.read_text(encoding="utf-8"))
    # Use the original's own peer definition so the comparison isolates builder behaviour.
    peer = dict(original.PEERS[0])
    applied_at = original.TIMESTAMP

    # Both modules compute TIMESTAMP at import, microseconds apart. Align them so the diff
    # isolates builder behaviour rather than import timing.
    vendored = derived._vendored()
    vendored.TIMESTAMP = original.TIMESTAMP

    stamped = json.loads(derived.stamp(json.dumps(package), peer, applied_at))
    canon = derived.check_canon_lock(package, allow_unclean=True)

    findings: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}

    for tensor, builder in (("SPINE", original.build_spine_record), ("NCT", original.build_nct_record)):
        raw = stamped.get("records", {}).get(tensor, [])
        if not raw:
            continue
        orig_records = [builder(r, peer, i + 1) for i, r in enumerate(raw)]
        der_records = derived.shape_records(raw, tensor, "genesis-baseline", applied_at, canon, peer)

        summary[tensor] = {"original_count": len(orig_records), "derived_count": len(der_records),
                           "counts_match": len(orig_records) == len(der_records)}

        for i, (o, d) in enumerate(zip(orig_records, der_records)):
            result = compare(o, d, f"{tensor}[{i}] {str(o.get('id', ''))[:60]}")
            if result["UNEXPLAINED_dropped_fields"] or result["UNEXPLAINED_value_changes"] or result["UNEXPLAINED_new_fields"]:
                findings.append(result)

    report = {
        "schema_version": "1.0.0",
        "record_type": "seating_tool_diff",
        "package": str(args.package),
        "original": str(args.original),
        "peer_used": peer.get("peer_id"),
        "intended_differences": INTENDED,
        "summary": summary,
        "records_with_unexplained_differences": len(findings),
        "findings": findings[:20],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    print(f"peer used: {peer.get('peer_id')}")
    for tensor, s in summary.items():
        print(f"  {tensor:6} original={s['original_count']:3}  derived={s['derived_count']:3}  "
              f"counts_match={s['counts_match']}")
    print()
    if findings:
        print(f"UNEXPLAINED DIFFERENCES in {len(findings)} record(s):")
        for f in findings[:5]:
            print(f"  {f['record']}")
            if f["UNEXPLAINED_dropped_fields"]:
                print(f"    dropped by derived : {f['UNEXPLAINED_dropped_fields'][:10]}")
            if f["UNEXPLAINED_value_changes"]:
                print(f"    value changed      : {f['UNEXPLAINED_value_changes'][:10]}")
            if f["UNEXPLAINED_new_fields"]:
                print(f"    added by derived   : {f['UNEXPLAINED_new_fields'][:10]}")
    else:
        print("No unexplained differences. All deltas are in the intended set.")
    print(f"\nreport: {args.output}")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
