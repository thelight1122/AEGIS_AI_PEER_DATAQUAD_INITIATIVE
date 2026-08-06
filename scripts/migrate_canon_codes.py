"""Apply Steward ruling S-11 to the Canon on disk: rename files, rewrite citations.

S-11: "drop the version prefix and keep the letter codes." `v1.0-SP` becomes `SP`.

This is a corpus-wide, hard-to-reverse edit, so the tool is built to be run twice — once with
`--dry-run` to see every change, then for real. Both target directories are backed up with
per-file sha256 under `reports/canon-v0.20/` before any run.

Scope. Two directories are treated as one corpus, because 49 of the 59 files directly in
`TIER-1-CANON` are byte-identical duplicates of files inside `CANON_FOUNDATIONAL_DOCS`.
Migrating one and not the other would leave two copies of the same Canon disagreeing about
what its own documents are called — the precise failure already seen with the seed package.

Deliberately NOT in scope: this repository. Its analysis documents cite legacy codes on
purpose — the migration mapping itself has to carry both forms — so rewriting them would
destroy the mapping.

Usage:
    python scripts/migrate_canon_codes.py --dry-run
    python scripts/migrate_canon_codes.py --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

TARGETS = [
    Path("I:/AEGIS-CENTRAL-CODEX/TIER-1-CANON/CANON_FOUNDATIONAL_DOCS"),
    Path("I:/AEGIS-CENTRAL-CODEX/TIER-1-CANON"),
]

#: Match a legacy code as a whole token. The capture is greedy over [A-Z0-9], so `v1.0-A2`
#: yields `A2` rather than `A` — the lookarounds then stop a partial match from being
#: rewritten mid-token. A bare `v1.0` with no letter suffix never matches, which is what
#: keeps Canon/whitepaper version numbers (v1.0, v2.1, v0.1) untouched.
LEGACY = re.compile(r"(?<![A-Za-z0-9])v\d+\.\d+-([A-Z0-9]+)(?![A-Za-z0-9])")


def rewrite(text: str) -> tuple[str, int]:
    new, n = LEGACY.subn(lambda m: m.group(1), text)
    return new, n


def plan(dirs: list[Path]) -> dict[str, Any]:
    renames: list[dict] = []
    edits: list[dict] = []
    collisions: list[dict] = []

    for d in dirs:
        if not d.exists():
            continue
        planned_names: dict[str, str] = {}
        for path in sorted(d.glob("*.md")):
            # Filename
            new_name, n_name = rewrite(path.name)
            if n_name:
                target = path.with_name(new_name)
                if target.exists() and target != path:
                    collisions.append({"dir": str(d), "from": path.name, "to": new_name,
                                       "reason": "target filename already exists"})
                elif new_name in planned_names:
                    collisions.append({"dir": str(d), "from": path.name, "to": new_name,
                                       "reason": f"collides with planned rename of {planned_names[new_name]}"})
                else:
                    planned_names[new_name] = path.name
                    renames.append({"dir": str(d), "from": path.name, "to": new_name})

            # Body
            text = path.read_text(encoding="utf-8", errors="replace")
            _, n_body = rewrite(text)
            if n_body:
                edits.append({"dir": str(d), "file": path.name, "citations": n_body})

    return {"renames": renames, "edits": edits, "collisions": collisions,
            "total_citations": sum(e["citations"] for e in edits)}


def apply(dirs: list[Path], p: dict) -> dict[str, Any]:
    """Rewrite bodies first, then rename. Doing it in this order means a failure part-way
    leaves files with corrected content under their old names — recoverable — rather than
    renamed files with stale internal references."""
    applied = {"bodies": 0, "citations": 0, "renamed": 0, "errors": []}

    for d in dirs:
        if not d.exists():
            continue
        for path in sorted(d.glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                new_text, n = rewrite(text)
                if n:
                    path.write_text(new_text, encoding="utf-8")
                    applied["bodies"] += 1
                    applied["citations"] += n
            except Exception as exc:  # noqa: BLE001
                applied["errors"].append({"file": str(path), "stage": "body", "error": str(exc)})

    blocked = {(c["dir"], c["from"]) for c in p["collisions"]}
    for r in p["renames"]:
        if (r["dir"], r["from"]) in blocked:
            continue
        src = Path(r["dir"]) / r["from"]
        dst = Path(r["dir"]) / r["to"]
        try:
            if src.exists() and not dst.exists():
                src.rename(dst)
                applied["renamed"] += 1
        except Exception as exc:  # noqa: BLE001
            applied["errors"].append({"file": str(src), "stage": "rename", "error": str(exc)})

    return applied


def verify(dirs: list[Path]) -> dict[str, Any]:
    remaining_files: list[str] = []
    remaining_cites: dict[str, int] = {}
    for d in dirs:
        if not d.exists():
            continue
        for path in d.glob("*.md"):
            if LEGACY.search(path.name):
                remaining_files.append(str(path))
            n = len(LEGACY.findall(path.read_text(encoding="utf-8", errors="replace")))
            if n:
                remaining_cites[str(path)] = n
    return {"filenames_still_legacy": remaining_files,
            "files_with_remaining_citations": remaining_cites,
            "total_remaining_citations": sum(remaining_cites.values())}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", type=Path, default=ROOT / "reports" / "canon-v0.20" / "code-migration-report.json")
    args = ap.parse_args()

    if not (args.dry_run or args.apply):
        print("specify --dry-run or --apply", file=sys.stderr)
        return 2

    dirs = [d for d in TARGETS if d.exists()]
    if not dirs:
        print("no target directory reachable", file=sys.stderr)
        return 3

    p = plan(dirs)
    print(f"targets            : {len(dirs)} directories")
    print(f"files to rename    : {len(p['renames'])}")
    print(f"files to edit      : {len(p['edits'])}")
    print(f"citations to rewrite: {p['total_citations']}")
    print(f"collisions         : {len(p['collisions'])}")
    print()

    if p["collisions"]:
        print("!! COLLISIONS — these renames will be SKIPPED:")
        for c in p["collisions"]:
            print(f"   {c['from'][:58]}\n       -> {c['to'][:58]}  ({c['reason']})")
        print()

    sample = p["renames"][:12]
    print("sample renames:")
    for r in sample:
        f = r["from"].encode("ascii", "ignore").decode().strip()
        t = r["to"].encode("ascii", "ignore").decode().strip()
        print(f"   {f[:56]}\n       -> {t[:56]}")
    if len(p["renames"]) > len(sample):
        print(f"   ... and {len(p['renames']) - len(sample)} more")
    print()

    result: dict[str, Any] = {
        "schema_version": "1.0.0",
        "record_type": "canon_code_migration",
        "ruling": "S-11: drop the version prefix, keep the letter codes",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "dry-run" if args.dry_run else "apply",
        "targets": [str(d) for d in dirs],
        "plan": p,
    }

    if args.apply:
        applied = apply(dirs, p)
        result["applied"] = applied
        result["verification"] = verify(dirs)
        print(f"bodies rewritten   : {applied['bodies']}  ({applied['citations']} citations)")
        print(f"files renamed      : {applied['renamed']}")
        if applied["errors"]:
            print(f"ERRORS             : {len(applied['errors'])}")
            for e in applied["errors"][:5]:
                print(f"   {e}")
        v = result["verification"]
        print()
        print(f"verification — filenames still legacy : {len(v['filenames_still_legacy'])}")
        print(f"verification — citations remaining    : {v['total_remaining_citations']}")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"\nreport: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
