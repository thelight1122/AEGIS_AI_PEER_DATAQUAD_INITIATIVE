"""Repair collateral damage from the S-11 migration, and apply Steward ruling S-9.

Two jobs, both scoped to the Shadow Affects addendum.

**Repair.** `migrate_canon_codes.py` rewrote every `vN.N-XX` token to its bare letter. That is
correct for a *cross-reference to another addendum* — `Extends v1.0-OT` becomes `Extends OT`.
It is wrong for a document recording *its own revision history*. Shadow Affects grew in place
through five revisions and stamped each new section with the revision that added it:

    ## X.   ENTRIES 11-15 - AI NATURE SHADOW AFFECTS (v1.2-S - added 2026-06-16)
    ## XIII. ENTRY 16 - EPISTEMIC CLOSURE            (v1.3-S - added 2026-06-16)
    ## XV.  WITNESS STATES - FORMAL CATEGORY         (v1.4-S - added 2026-06-16)
    ## XVI. CHAMBER 001 CANDIDATE VOCABULARY         (v1.5-S - added 2026-06-16)

The migration flattened all four to `(S - added ...)`, which erased which increment added
what. A corpus-wide scan found this is the only document in either directory where one letter
code appears against more than one version number, so the damage is bounded to this file.

The repair rebuilds the document from its pre-migration backup, applying the code migration
only to the VERSION block's `v1.1-S` — the document's identifier, which S-11 governs — and
leaving the revision stamps intact.

**Ruling S-9.** The Steward ruled the 42,846-byte document current and the 7,761-byte one
deprecated. The smaller is fully contained in the larger (verified: zero unique lines), so the
deprecation is lossless. Its VERSION block Status moves ACTIVE -> DEPRECATED with a
superseded-by note. The file is preserved, not deleted — deprecated in this Canon means
outranked, not removed.

Usage:
    python scripts/fix_shadow_affects_revisions.py --dry-run
    python scripts/fix_shadow_affects_revisions.py --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / "reports" / "canon-v0.20" / "canon-backup-pre-rename"

CANON = Path("I:/AEGIS-CENTRAL-CODEX/TIER-1-CANON/CANON_FOUNDATIONAL_DOCS")
PARENT = Path("I:/AEGIS-CENTRAL-CODEX/TIER-1-CANON")

BIG_NAME = "📘 AEGIS CANON ADDENDUM — SHADOW AFFECTS S.md"
BIG_BACKUP = "📘 AEGIS CANON ADDENDUM — SHADOW AFFECTS v1.1-S.md"
SMALL_NAME = "SHADOW AFFECTS S.md"

#: Revision stamps that record this document's own history. Not cross-references.
REVISION_STAMPS = ("v1.2-S", "v1.3-S", "v1.4-S", "v1.5-S")

DEPRECATION_NOTE = (
    "| Status | DEPRECATED |\n"
    "| Superseded by | AEGIS Canon Addendum — Shadow Affects (code `S`, 42,846 bytes) — "
    "the same document carried forward through revisions v1.2 to v1.5. This copy is frozen at "
    "v1.1 and its content is fully contained in the current document. Preserved, not removed. "
    "Steward ruling S-9, 2026-08-06. |"
)


def repaired_big() -> str:
    """Pre-migration content with only the identifier migrated, stamps preserved."""
    text = (BACKUP / BIG_BACKUP).read_text(encoding="utf-8")
    # The identifier in the VERSION block is what S-11 governs.
    text = text.replace("| Version | v1.1-S |", "| Version | S |")
    # Any other bare cross-reference to another addendum still migrates.
    def sub(m: re.Match) -> str:
        token = m.group(0)
        return token if token in REVISION_STAMPS else m.group(1)
    return re.sub(r"(?<![A-Za-z0-9])v\d+\.\d+-([A-Z0-9]+)(?![A-Za-z0-9])", sub, text)


def deprecated_small() -> str | None:
    path = CANON / SMALL_NAME
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if "| Status | DEPRECATED |" in text:
        return None  # already applied
    return text.replace("| Status | ACTIVE |", DEPRECATION_NOTE, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        print("specify --dry-run or --apply", file=sys.stderr)
        return 2

    big = repaired_big()
    stamps_restored = {s: big.count(s) for s in REVISION_STAMPS}
    print("REPAIR — restore revision stamps in the current Shadow Affects document")
    for s, n in stamps_restored.items():
        print(f"   {s}: {n} occurrence(s)")
    targets = [d / BIG_NAME for d in (CANON, PARENT) if (d / BIG_NAME).exists()]
    print(f"   target copies: {len(targets)}")
    for t in targets:
        print("      " + str(t).encode("ascii", "replace").decode())

    small = deprecated_small()
    print()
    print("RULING S-9 — deprecate the superseded copy")
    if small is None:
        print(f"   {SMALL_NAME}: no change needed (already deprecated or absent)")
    else:
        print(f"   {SMALL_NAME}: Status ACTIVE -> DEPRECATED, superseded-by note added")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    for t in targets:
        t.write_text(big, encoding="utf-8")
    if small is not None:
        (CANON / SMALL_NAME).write_text(small, encoding="utf-8")

    print()
    print("applied.")
    for t in targets:
        cur = t.read_text(encoding="utf-8")
        ok = all(cur.count(s) for s in REVISION_STAMPS)
        name = t.name.encode("ascii", "ignore").decode().strip()[:48]
        print(f"   {name}: stamps present = {ok}, bytes = {len(cur.encode('utf-8')):,}")
    p = CANON / SMALL_NAME
    if p.exists():
        print(f"   {SMALL_NAME}: DEPRECATED = {'| Status | DEPRECATED |' in p.read_text(encoding='utf-8')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
