"""Apply Steward ruling S-7: the chamber is the Response Buffer Chamber.

Evidence. `AEGIS SENTINEL FOUNDATIONAL PRINCIPLES.md` is the inception document the Addendum
Index cites as the source for this meaning. It says **RESPONSE BUFFER CHAMBER** five times and
contains zero occurrences of "Resonance Buffer Chamber". STUD 2 describes exactly that: a
chamber where generated output is held before release — "Token Quarantine... Output is
contained, not blocked." The index misquoted its own source, and "Resonance" propagated from
there. `AEGIS Sigil Origin.md` already carries the correct original.

Scope. Only the exact phrase `Resonance Buffer Chamber` is rewritten. Two things are
deliberately untouched:

  - **Reflective Boundary Conditions** (25 occurrences) — a genuinely different concept, the
    expression constraint layer of Canon §2.5. Never in dispute, never rewritten.
  - **Every other use of "Resonance"** (116 occurrences) — Flow Path of Resonance, the
    Resonance Equation, resonance as a general term. The phrase match cannot reach them.

The Addendum Index needs more than a phrase swap: its KNOWN OPEN ITEMS section describes the
collision as unresolved and marks the chamber "to be renamed or disambiguated". A blind
replace would leave it saying the Response Buffer Chamber must be renamed. That section is
rewritten to record the ruling, and the planned `-R` disambiguation addendum is marked
resolved-by-ruling rather than still pending.

Usage:
    python scripts/fix_rbc_naming.py --dry-run
    python scripts/fix_rbc_naming.py --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    Path("I:/AEGIS-CENTRAL-CODEX/TIER-1-CANON/CANON_FOUNDATIONAL_DOCS"),
    Path("I:/AEGIS-CENTRAL-CODEX/TIER-1-CANON"),
]

OLD = "Resonance Buffer Chamber"
NEW = "Response Buffer Chamber"

#: Must never be rewritten — a separate concept, not the chamber.
PROTECTED = "Reflective Boundary Conditions"

INDEX_MARKER = "ADDENDUM INDEX"

OLD_OPEN_ITEM = """- Canon 2.5 RBC = **Reflective Boundary Conditions** (expression constraint layer)  canonical
- Sentinel RBC = **Resonance Buffer Chamber**  to be renamed or disambiguated

Neither usage is wrong. The collision is the problem."""

NEW_OPEN_ITEM = """**RESOLVED — Steward ruling, 2026-08-06.**

Two distinct concepts, both retained, neither renamed away:

- **Reflective Boundary Conditions** — the expression constraint layer (Canon 2.5). Constrains
  output posture only; never inference or internal state.
- **Response Buffer Chamber** — the pipeline stage before delivery, where generated output is
  held. This is the inception name, per AEGIS Sentinel Foundational Principles STUD 2.

The earlier entry above recorded this source as "Resonance Buffer Chamber". That was a
transcription error in this index: the inception document says RESPONSE five times and never
says Resonance. "Resonance Buffer Chamber" propagated from that misquote and has been corrected
throughout Canon. AEGIS Sigil Origin.md had preserved the correct original all along.

This is consistent with GATE: RBC Stage Integrity in AEGIS CORE FOUNDATIONAL CANON, which
already held that both meanings are retained and neither replaces the other."""

OLD_R_ROW = "| `-R` | RBC disambiguation (planned) |"
NEW_R_ROW = "| `-R` | RBC disambiguation - RESOLVED by Steward ruling 2026-08-06, no addendum required |"


def transform(text: str, is_index: bool) -> tuple[str, int]:
    before_protected = text.count(PROTECTED)
    n = text.count(OLD)
    out = text.replace(OLD, NEW)

    if is_index:
        # The prose describing the collision must record the resolution, not just swap a word.
        swapped_old_block = OLD_OPEN_ITEM.replace(OLD, NEW)
        for candidate in (OLD_OPEN_ITEM, swapped_old_block):
            if candidate in out:
                out = out.replace(candidate, NEW_OPEN_ITEM)
                break
        out = out.replace(OLD_R_ROW, NEW_R_ROW)

    # The protected phrase count must be identical before and after, always.
    assert out.count(PROTECTED) == before_protected, "protected phrase was altered"
    return out, n


def run(apply: bool) -> dict[str, Any]:
    changed: list[dict] = []
    total = 0
    for d in TARGETS:
        if not d.exists():
            continue
        for path in sorted(d.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            if OLD not in text and not (INDEX_MARKER in path.name.upper() and OLD_R_ROW in text):
                continue
            is_index = INDEX_MARKER in path.name.upper()
            new_text, n = transform(text, is_index)
            if new_text == text:
                continue
            total += n
            changed.append({"dir": str(d), "file": path.name, "occurrences": n, "index": is_index})
            if apply:
                path.write_text(new_text, encoding="utf-8")
    return {"files": changed, "total_occurrences": total}


def verify() -> dict[str, Any]:
    remaining = {}
    protected = 0
    applied = 0
    for d in TARGETS:
        if not d.exists():
            continue
        for path in d.glob("*.md"):
            t = path.read_text(encoding="utf-8", errors="replace")
            if OLD in t:
                remaining[path.name] = t.count(OLD)
            protected += t.count(PROTECTED)
            applied += t.count(NEW)
    return {"old_phrase_remaining": remaining, "new_phrase_count": applied,
            "protected_phrase_count": protected}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", type=Path, default=ROOT / "reports" / "canon-v0.20" / "rbc-naming-fix.json")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        print("specify --dry-run or --apply", file=sys.stderr)
        return 2

    result = run(apply=args.apply)
    print(f"files to change    : {len(result['files'])}")
    print(f"occurrences        : {result['total_occurrences']}")
    for f in result["files"]:
        tag = "  [INDEX - prose also rewritten]" if f["index"] else ""
        print(f"   {f['occurrences']:3}  {f['file'].encode('ascii','ignore').decode().strip()[:52]}{tag}")

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "record_type": "rbc_naming_fix",
        "ruling": "S-7: the chamber is the Response Buffer Chamber (Steward, 2026-08-06)",
        "evidence": "AEGIS SENTINEL FOUNDATIONAL PRINCIPLES.md STUD 2 - 'RESPONSE BUFFER CHAMBER' x5, 'Resonance Buffer Chamber' x0",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "apply" if args.apply else "dry-run",
        "result": result,
    }
    if args.apply:
        v = verify()
        payload["verification"] = v
        print()
        print(f"verification - old phrase remaining : {sum(v['old_phrase_remaining'].values())}")
        print(f"verification - new phrase present   : {v['new_phrase_count']}")
        print(f"verification - protected phrase     : {v['protected_phrase_count']} (must be unchanged at 25)")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"\nreport: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
