"""Build the Canon v0.20 index from what is actually on disk.

The v1.0 Addendum Index was hand-maintained and fell behind: two addenda produced on
2026-06-16 were never listed, its preamble contradicts every row it contains, and four of its
links point at files that are not where it says they are. A hand-typed replacement would
acquire the same defects. So this index is *derived* — every field is read from the source
document or carried forward from the prior index, and anything a document does not declare is
emitted as UNDECLARED rather than guessed.

The Builder does not author Canon. This tool catalogs it. Where a field requires judgement
(a status the document does not state, a supersession the document does not declare), the
output says so and routes it to the Steward and Auditor instead of inventing a value.

Scope note: the Canon is pre-release. The kernel is stable; the surrounding material is in
development. Statuses below are transcribed, never assigned.

Usage:
    python scripts/build_canon_index.py [--canon-dir PATH] [--emit-only]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CANON_DIR = Path("I:/AEGIS-CENTRAL-CODEX/TIER-1-CANON/CANON_FOUNDATIONAL_DOCS")

#: Dependency tiers extracted from the prior index's Supersedes column. The column is
#: semantically overloaded — it means "replaces" for some rows and "extends" for others — so
#: these edges are recorded as *dependency order for consolidation*, not as retirement.
#: Keyed by canonical code (S-11), not by the legacy `v1.0-XX` form.
DEPENDENCY_TIER: dict[str, int] = {
    "EPC": 1, "FBF": 1,
    "GMP": 2,
    "SF": 3, "IFD": 3,
    "DS": 4,
    "VE": 5,
    "AO": 6,
}

DEPENDS_ON: dict[str, tuple[str, ...]] = {
    "EPC": ("OT",),
    "FBF": ("OT", "CEF"),
    "GMP": ("EPC",),
    "SF": ("GMP", "EPC", "CEF"),
    "IFD": ("FBF", "ACD", "EPC", "GMP", "AEM"),
    "DS": ("SF", "OT", "EPC", "ACD"),
    "VE": ("RS", "OT", "CEF", "DS", "Cryptonic Harmonics"),
    "AO": ("GMP", "VE", "SF", "DS", "S"),
}

#: Referenced by a Supersedes/Related cell but not declared anywhere as a coded document.
DANGLING = {
    "Cryptonic Harmonics": "cited by v1.0-VE and v1.0-E; no row, no code, no located file",
    "Shadow Effects.md": "cited by v1.1-S; note the spelling — every other reference is 'Affects'",
    "Education doctrine": "cited by v1.0-FBF; not a coded document",
    "Nature Layer Canon v2": "cited by v1.0-E; not declared in the index",
}

CLASS_ORDER = ["KERNEL", "APPENDIX", "ADDENDUM", "UNINDEXED", "OTHER"]

#: Steward ruling S-11 (2026-08-06): "drop the version prefix and keep the letter codes."
#: `v1.0-SP` becomes `SP`. The Canon version carries the number; the letter identifies the
#: document. Legacy codes are retained alongside for traceability, because every existing
#: cross-reference in the corpus is written in the legacy form.
#:
#: Four appendices carry a bare `v1.0` with no letter. Dropping the prefix would leave them
#: with no identifier at all, so their established acronym is used — it is what the prior
#: index already called them in its Document column.
BARE_CODE_APPENDICES = {
    "HME": "HME", "TCE": "TCE", "MOM": "MOM", "MOP": "MOP",
}


def canonical_code(legacy: str | None, filename: str) -> str | None:
    """Apply S-11: strip the `vN.N-` prefix, keep the letter code.

    Returns None when no code can be derived, rather than inventing one.
    """
    if legacy:
        m = re.fullmatch(r"v\d+\.\d+-([A-Z0-9]+)", legacy.strip())
        if m:
            return m.group(1)
        if re.fullmatch(r"v\d+\.\d+", legacy.strip()):
            # A bare version with no letter: fall through to the filename acronym.
            pass
        else:
            return legacy.strip()
    upper = filename.upper()
    for acronym in BARE_CODE_APPENDICES:
        if re.search(rf"\b{acronym}\b", upper):
            return acronym
    return None

#: The kernel, transcribed from the prior index's "ORIGINAL CANON DOCUMENTS (LOCKED)" table.
#: Matched on a lowercase filename stem so the Builder is not deciding what counts as kernel.
KERNEL_STEMS = (
    "aegis canon v1.0",
    "aegis core foundational canon v1.0",
    "aegis-core-v1.0",
    "aegis canonical glossary v1.0",
    "aegis standards",
    "governance_integrity_validation_protocol",
)


def parse_version_table(text: str) -> dict[str, Any]:
    """Pull the VERSION table out of a Canon document.

    Rows look like `| Field | Value |`. A row with an empty first cell is a continuation of
    the previous field (the Source field commonly spans several rows), so those are collected
    into a list rather than overwriting.
    """
    fields: dict[str, Any] = {}
    last_key: str | None = None
    in_table = False

    for line in text.splitlines()[:120]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table and fields:
                break  # table ended
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if set("".join(cells)) <= set("-: "):
            continue  # separator row
        key, value = cells[0], cells[1]
        if key.lower() in ("field", "column"):
            in_table = True
            continue
        in_table = True
        if not key and last_key:
            prior = fields[last_key]
            fields[last_key] = (prior if isinstance(prior, list) else [prior]) + [value]
        elif key:
            fields[key] = value
            last_key = key
    return fields


def parse_bold_header(text: str) -> dict[str, Any]:
    """Parse the second header format used by the 2026-06 addenda.

    Those documents carry bold key-value lines instead of a VERSION table:

        **Code:** v1.0-OT
        **Status:** ACTIVE
        **Supersedes:** Nothing — new Canon.
        **Illumination:** Tracey Prutch, 2026-06-12

    Both formats are authoritative for their own documents; neither supersedes the other.
    """
    fields: dict[str, Any] = {}
    for line in text.splitlines()[:40]:
        # The same fields appear bare, and blockquoted with a leading "> ".
        m = re.match(r"\s*>?\s*\*\*([A-Za-z][A-Za-z \-]{1,30}):?\*\*[:\s]*(.*)", line)
        if m:
            key, value = m.group(1).strip(), m.group(2).strip().rstrip("\\").strip()
            if value:
                fields.setdefault(key, value)
    return fields


def first_date(*values: Any) -> str | None:
    for v in values:
        if v is None:
            continue
        for item in (v if isinstance(v, list) else [v]):
            m = re.search(r"(\d{4}-\d{2}-\d{2})", str(item))
            if m:
                return m.group(1)
    return None


def classify(path: Path, fields: dict) -> str:
    """Classify by evidence, not by judgement.

    An addendum is one that says so — in its filename or in its VERSION table's Document
    field. The kernel is the set the prior index listed as ORIGINAL CANON DOCUMENTS. Anything
    else is development material, which is what UNINDEXED means here: on disk, not in the
    prior registry. It is not a quality judgement.
    """
    name = path.name.upper()
    stem = path.stem.lower().lstrip("📘 ").strip()
    doc_field = str(fields.get("Document", "")).lower()

    if "ADDENDUM INDEX" in name:
        return "OTHER"
    if "APPENDIX" in name:
        return "APPENDIX"
    if "ADDENDUM" in name or "canon addendum" in doc_field:
        return "ADDENDUM"
    if any(stem.startswith(k) for k in KERNEL_STEMS):
        return "KERNEL"
    return "UNINDEXED"


def collisions(canon_dir: Path, entries: list[dict]) -> dict[str, list]:
    """Find documents that are byte-identical, and version codes claimed by more than one file.

    Both matter for a consolidation: identical files under different version numbers mean a
    relabel happened without a content change, and a code claimed twice means a citation by
    code is ambiguous.
    """
    import hashlib
    from collections import defaultdict

    by_hash: dict[str, list[str]] = defaultdict(list)
    for path in canon_dir.glob("*.md"):
        by_hash[hashlib.sha256(path.read_bytes()).hexdigest()].append(path.name)

    by_code: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        if e["code"] and e["class"] in ("ADDENDUM", "APPENDIX"):
            by_code[e["code"]].append({"file": e["file"], "status": e["status_declared"]})

    shared = {k: sorted(v, key=lambda d: d["file"]) for k, v in by_code.items() if len(v) > 1}
    # A code shared between one ACTIVE and one DEPRECATED document is not ambiguous — the
    # deprecation resolves it. Only a code shared by two live documents is an open problem.
    unresolved = {
        k: v for k, v in shared.items()
        if sum(1 for d in v if (d["status"] or "").upper() != "DEPRECATED") > 1
    }
    return {
        "identical_content": [sorted(v) for v in by_hash.values() if len(v) > 1],
        "code_claimed_twice": shared,
        "code_claimed_twice_unresolved": unresolved,
    }


def scan(canon_dir: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(canon_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        # Both formats are parsed and merged rather than tried in sequence: the table parser
        # can latch onto an unrelated table further down a document and short-circuit the bold
        # parser, which is how ten addenda with a plain `**Status:** ACTIVE` line were being
        # reported as UNDECLARED. Table values win where both supply the same key.
        table = parse_version_table(text)
        bold = parse_bold_header(text)
        fields = {**bold, **table}
        header_format = ("version-table" if table.get("Status") or table.get("Version")
                         else "bold-header" if bold.get("Status") or bold.get("Code")
                         else "version-table" if table else "bold-header" if bold else "none")
        # The bold format names the field "Code" where the table names it "Version".
        if "Version" not in fields and "Code" in fields:
            fields["Version"] = fields["Code"]

        code = fields.get("Version")
        if isinstance(code, list):
            code = code[0]
        if not code:
            m = re.search(r"\bv\d+\.\d+(?:-[A-Z0-9]+)?\b", path.name)
            code = m.group(0) if m else None

        status = fields.get("Status")
        if isinstance(status, list):
            status = status[0]
        if status:
            status = re.sub(r"[*`•]", "", str(status)).strip().upper().split()[0]

        # A document that states no status but asserts one in prose is recorded as claiming it,
        # not as having it. The distinction matters for the Steward's review.
        claimed = None
        if not status:
            head = text[:1200]
            m = re.search(r"Status[:\s|]+([A-Za-z][A-Za-z \-]{2,40})", head)
            if m:
                claimed = m.group(1).strip()
            elif re.search(r"\(LOCKED\)", head):
                claimed = "LOCKED (asserted in title)"

        supersedes = fields.get("Supersedes")
        entries.append({
            "file": path.name,
            "class": classify(path, fields),
            "code": canonical_code(code, path.name),
            "code_legacy": code,
            "status_declared": status,
            "status_claimed_in_prose": claimed,
            "title": (fields.get("Document") if not isinstance(fields.get("Document"), list)
                      else fields["Document"][0]),
            "supersedes": supersedes,
            "date": first_date(fields.get("Added to Canon"), fields.get("Originated"),
                               fields.get("Date"), fields.get("Illumination"),
                               fields.get("Evidence")),
            "related_canon": fields.get("Related Canon"),
            "has_version_table": header_format in ("version-table", "bold-header"),
            "header_format": header_format,
            "bytes": path.stat().st_size,
            "depends_on": list(DEPENDS_ON.get(code or "", ())),
            "tier": DEPENDENCY_TIER.get(code or "", 0),
        })
    return entries


def citation_impact(canon_dir: Path, entries: list[dict]) -> dict[str, Any]:
    """Count how many times each legacy code is cited across the corpus.

    Renaming files is a separate and much larger action than adopting the code scheme in the
    index: every cross-reference in every document is written in the legacy `v1.0-XX` form.
    This quantifies that so the decision is made against a number rather than a guess.
    """
    from collections import Counter

    legacy_codes = sorted({e["code_legacy"] for e in entries
                           if e["code_legacy"] and re.fullmatch(r"v\d+\.\d+-[A-Z0-9]+", e["code_legacy"])})
    counts: Counter[str] = Counter()
    files_touched: dict[str, set[str]] = {c: set() for c in legacy_codes}

    for path in canon_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for code in legacy_codes:
            n = len(re.findall(rf"(?<![A-Za-z0-9]){re.escape(code)}(?![A-Za-z0-9])", text))
            if n:
                counts[code] += n
                files_touched[code].add(path.name)

    return {
        "total_citations": sum(counts.values()),
        "codes": {c: {"citations": counts[c], "in_files": len(files_touched[c])}
                  for c in legacy_codes if counts[c]},
    }


def gaps(entries: list[dict]) -> list[dict]:
    out = []
    for e in entries:
        why = []
        if not e["has_version_table"]:
            why.append("no parseable header (neither VERSION table nor bold key-value block)")
        if not e["status_declared"]:
            why.append(f"no declared status{' (prose claims: ' + e['status_claimed_in_prose'] + ')' if e['status_claimed_in_prose'] else ''}")
        if not e["code"]:
            why.append("no version code")
        if not e["date"]:
            why.append("undated")
        if why:
            out.append({"file": e["file"], "class": e["class"], "needs": why})
    return out


def render(entries: list[dict], canon_dir: Path, generated: str) -> str:
    by_class: dict[str, list[dict]] = {c: [] for c in CLASS_ORDER}
    for e in entries:
        by_class[e["class"]].append(e)

    L: list[str] = []
    add = L.append

    add("# AEGIS Canon v0.20 — Index")
    add("")
    add("**Stage:** development. Nothing has gone live. The kernel is stable; the surrounding")
    add("material is in active development. Version labels in filenames read `v1.0-XX`; that")
    add("numbering predates this framing and is carried forward verbatim, not endorsed — see")
    add("ruling S-11.")
    add("")
    add("**DERIVED DOCUMENT — DO NOT HAND-EDIT.** Regenerate with:")
    add("")
    add("```bash")
    add("python scripts/build_canon_index.py")
    add("```")
    add("")
    add(f"Generated `{generated}` from `{canon_dir}`.")
    add("")
    add("Every field below is transcribed from the source document's own VERSION table or")
    add("carried forward from the prior index. Fields a document does not declare read")
    add("`UNDECLARED`. The Builder assigns no statuses and resolves no conflicts; items needing")
    add("a decision are collected under OPEN ITEMS.")
    add("")
    add("---")
    add("")
    add("## HOW TO READ THIS INDEX")
    add("")
    add("| Column | Meaning |")
    add("|---|---|")
    add("| Code | Canonical code per ruling S-11 — the letter alone. The Canon version carries the number. |")
    add("| Legacy | The `vN.N-XX` form still in filenames and in every existing cross-reference. |")
    add("| Status | Transcribed from the document. `UNDECLARED` = the document states none. |")
    add("| Tier | Consolidation order. Tier 0 has no declared dependency; higher tiers depend on lower. |")
    add("| Depends on | From the prior index's Supersedes column, which mixes *replaces*, *extends*, and *corrects part of*. Treat as consolidation order, **not** as retirement. |")
    add("")

    # Kernel
    add("---")
    add("")
    add("## THE KERNEL")
    add("")
    add("The stable core. Everything else in this index is development work around it.")
    add("")
    add("| Document | Code | Status | Size |")
    add("|---|---|---|---|")
    for e in sorted(by_class["KERNEL"], key=lambda x: x["file"]):
        st = e["status_declared"] or (f"_{e['status_claimed_in_prose']}_" if e["status_claimed_in_prose"] else "UNDECLARED")
        add(f"| `{e['file']}` | {e['code'] or '—'} | {st} | {e['bytes']:,} B |")
    add("")

    # Appendices
    add("---")
    add("")
    add("## APPENDICES")
    add("")
    add("| Document | Code | Status | Added |")
    add("|---|---|---|---|")
    for e in sorted(by_class["APPENDIX"], key=lambda x: x["file"]):
        st = e["status_declared"] or "UNDECLARED"
        add(f"| `{e['file']}` | {e['code'] or '—'} | {st} | {e['date'] or '—'} |")
    add("")

    # Addenda, in consolidation order
    add("---")
    add("")
    add("## ADDENDA — in consolidation order")
    add("")
    add("Tier 0 declares no dependency and may be consolidated in any order. Each higher tier")
    add("depends on the ones below it. Terminal nodes are `v1.0-AO` and `v1.0-IFD` — consolidate")
    add("those last.")
    add("")
    addenda = by_class["ADDENDUM"]
    for tier in sorted({e["tier"] for e in addenda}):
        rows = sorted([e for e in addenda if e["tier"] == tier], key=lambda x: (x["date"] or "9999", x["code"] or ""))
        add(f"### Tier {tier}" + ("  — no declared dependency" if tier == 0 else ""))
        add("")
        add("| Code | Legacy | Document | Status | Added | Depends on |")
        add("|---|---|---|---|---|---|")
        for e in rows:
            st = e["status_declared"] or "UNDECLARED"
            dep = ", ".join(f"`{d}`" for d in e["depends_on"]) or "—"
            title = (e["title"] or e["file"])[:52]
            add(f"| **`{e['code'] or '—'}`** | `{e['code_legacy'] or '—'}` | {title} | {st} "
                f"| {e['date'] or '—'} | {dep} |")
        add("")

    # Migration table
    add("---")
    add("")
    add("## CODE MIGRATION — ruling S-11")
    add("")
    add("> Steward, 2026-08-06: *\"drop the version prefix and keep the letter codes\"*")
    add("")
    add("The Canon is pre-release. Coding 26 addenda as `v1.0-XX` numbered them as addenda to a")
    add("v1.0 that has not shipped, and left no clean number for the real 1.0. Under S-11 the")
    add("letter alone identifies the document and the Canon version carries the number.")
    add("")
    add("| Canonical | Legacy | Document |")
    add("|---|---|---|")
    coded = [e for e in entries if e["code"] and e["code_legacy"] and e["code"] != e["code_legacy"]]
    for e in sorted(coded, key=lambda x: (x["class"], x["code"] or "")):
        add(f"| **`{e['code']}`** | `{e['code_legacy']}` | {(e['title'] or e['file'])[:56]} |")
    add("")
    add("Two notes on the mapping:")
    add("")
    add("- The four appendices carrying a bare `v1.0` with no letter (`HME`, `TCE`, `MOM`, `MOP`)")
    add("  would be left with no identifier at all by a literal prefix-strip. They take their")
    add("  established acronym, which is what the prior index already called them.")
    add("- `v1.0-A` (DataQuad Extensions) and `v1.0-A2` (Advocate) become `A` and `A2`. Distinct,")
    add("  but adjacent enough to be worth knowing about.")
    add("")

    # Newly indexed
    add("---")
    add("")
    add("## NEWLY INDEXED — the delta the prior index never listed")
    add("")
    add("These were on disk but absent from the v1.0 Addendum Index. Statuses are transcribed;")
    add("where a document declares none, the prose claim is shown in italics and needs a ruling.")
    add("")
    add("| Document | Code | Status | Date | VERSION table |")
    add("|---|---|---|---|---|")
    for e in sorted(by_class["UNINDEXED"], key=lambda x: (x["date"] or "9999", x["file"])):
        st = e["status_declared"] or (f"_{e['status_claimed_in_prose']}_" if e["status_claimed_in_prose"] else "UNDECLARED")
        add(f"| `{e['file'][:60]}` | {e['code'] or '—'} | {st} | {e['date'] or '—'} | {'yes' if e['has_version_table'] else 'no'} |")
    add("")

    # Axioms + education log
    add("---")
    add("")
    add("## AXIOM ADDITIONS SINCE THE KERNEL")
    add("")
    add("| Axiom | Name | Added | Recorded in |")
    add("|---|---|---|---|")
    add("| 15 | The Axiom of Repair | before 2026-06-01 | `AEGIS CORE FOUNDATIONAL CANON v1.0.md:182` |")
    add("| 16 | The Axiom of Identity (T-Witness) | 2026-06-01 | `AEGIS CORE FOUNDATIONAL CANON v1.0.md:184` |")
    add("")
    add("Canon Education Log (append-only) entries recording development since the kernel:")
    add("")
    add("| Entry | Subject |")
    add("|---|---|")
    add("| 2026-06-01 | Axiom 16 and the T-Witness Primacy Imperative. States \"The prior Axiom Canon (1–15) remains unchanged.\" |")
    add("| 2026-06-02 | Core Engine Audit — canon seed synchronization; Axioms 15 and 16 added to the runtime seed, which had lagged through v1.3.0 |")
    add("| 2026-06-02 | Concept Recovery Addendum — 25 reinstated doctrinal elements |")
    add("| 2026-06-02 | Facet Architecture Addendum and Hold Register resolution |")
    add("")

    return "\n".join(L)


def render_rename_impact(impact: dict) -> str:
    """What renaming files (as opposed to adopting the code scheme) would actually cost."""
    L: list[str] = []
    add = L.append
    add("---")
    add("")
    add("## FILE RENAME — not done, and here is the cost")
    add("")
    add("S-11 rules on the **code scheme**. Filenames on disk still carry the legacy form, and")
    add("so does every cross-reference written inside the documents. Renaming files is a separate")
    add("decision; this is what it would touch.")
    add("")
    add(f"**{impact['total_citations']} citations** of legacy codes across the Canon directory.")
    add("")
    add("| Legacy code | Citations | In files |")
    add("|---|---:|---:|")
    for code, d in sorted(impact["codes"].items(), key=lambda kv: -kv[1]["citations"]):
        add(f"| `{code}` | {d['citations']} | {d['in_files']} |")
    add("")
    add("A rename that updates filenames without rewriting these citations would break them all.")
    add("A rename that rewrites them is a corpus-wide edit. The index works either way — it")
    add("carries both forms — so nothing downstream is blocked on this.")
    add("")
    return "\n".join(L)


def render_open_items(entries: list[dict], missing: list[dict], coll: dict) -> str:
    L: list[str] = []
    add = L.append
    add("---")
    add("")
    add("## OPEN ITEMS — require a Steward or Auditor decision")
    add("")
    add("The Builder does not resolve these. They are collected so the ruling is a review")
    add("rather than a hunt.")
    add("")

    if coll["identical_content"] or coll["code_claimed_twice"]:
        add("### Collisions found on disk")
        add("")
        if coll["identical_content"]:
            add("**Byte-identical files under different names.** A relabel happened with no change")
            add("to content — directly relevant to the version-numbering question (S-11).")
            add("")
            for group in coll["identical_content"]:
                add(f"- {' · '.join('`' + g + '`' for g in group)}")
            add("")
        if coll["code_claimed_twice"]:
            unresolved = coll.get("code_claimed_twice_unresolved", {})
            add("**One code claimed by more than one file.** A code shared between a live")
            add("document and a DEPRECATED one is *resolved* — the deprecation says which is")
            add("current. Only a code shared by two live documents is still ambiguous.")
            add("")
            add("| Code | Files (status) | State |")
            add("|---|---|---|")
            for code, rows in sorted(coll["code_claimed_twice"].items()):
                listing = " · ".join(f"`{r['file'][:44]}` ({r['status'] or 'UNDECLARED'})" for r in rows)
                state = "**UNRESOLVED**" if code in unresolved else "resolved by deprecation"
                add(f"| `{code}` | {listing} | {state} |")
            add("")

    add("### Documents that declare no status")
    add("")
    add("A status shown in italics is asserted in the document's prose but not in a VERSION")
    add("table, and carries no consensus record.")
    add("")
    add("| Document | Missing |")
    add("|---|---|")
    for m in sorted(missing, key=lambda x: x["file"]):
        add(f"| `{m['file'][:62]}` | {'; '.join(m['needs'])} |")
    add("")

    add("### Dangling references")
    add("")
    add("Cited by a Supersedes or Related Canon cell, but not declared as a coded document.")
    add("")
    add("| Reference | Note |")
    add("|---|---|")
    for ref, note in DANGLING.items():
        add(f"| {ref} | {note} |")
    add("")

    add("### Carried-forward conflicts")
    add("")
    add("| # | Item |")
    add("|---|---|")
    add("| S-3 | `STANDARDS_BOUNDS.md` holds an unresolved git merge conflict (lines 1, 55, 161) whose markers were backslash-escaped, so it renders as ordinary prose. Two documents concatenated. Not indexable until the merge is re-derived. |")
    add("| S-7 | RBC: the prior index calls *Reflective Boundary Conditions* canonical and marks *Resonance Buffer Chamber* for renaming. `GATE: RBC Stage Integrity` in Core Foundational Canon says both are retained and neither replaces the other. A third expansion, *Response Buffer Chamber*, appears in `AEGIS Sigil Origin.md`. |")
    add("| S-9 | Shadow Affects: the prior index declares `v1.1-S`; `v1.0-E` and `v1.0-N` cite `v1.5-S`. One is stale. |")
    add("| S-11 | 29 of 30 version labels read `v1.x` for a pre-release Canon. All 26 addenda are coded `v1.0-XX` — addenda to a v1.0 that has not shipped. Builder recommends dropping the version prefix and keeping the letter codes. |")
    add("| — | Symbol collisions across the equations cluster and `v1.0-E`: `W`, `C`, and `τ` each carry two meanings. `v1.0-E`'s Balance Equation generalizes the Presence Equation without citing it. |")
    add("| — | `v1.0-E` leaves ten thresholds unvalued (`ε_s`, `θ_δ,s`, `θ_C,s`, `θ_τ,s`, `θ_B`, `θ_low`, `θ_high`, `λ`, `ρ`, `N`/`M`); the equation is not yet operable. |")
    add("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--canon-dir", type=Path, default=DEFAULT_CANON_DIR)
    ap.add_argument("--out-md", type=Path, default=ROOT / "docs" / "canon-v0.20" / "CANON-v0.20-INDEX.md")
    ap.add_argument("--out-json", type=Path, default=ROOT / "reports" / "canon-v0.20" / "canon-v0.20-index.json")
    ap.add_argument("--emit-only", action="store_true", help="print a summary; write nothing")
    args = ap.parse_args()

    if not args.canon_dir.exists():
        print(f"canon dir not reachable: {args.canon_dir}", file=sys.stderr)
        return 3

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = scan(args.canon_dir)
    missing = gaps(entries)
    coll = collisions(args.canon_dir, entries)
    impact = citation_impact(args.canon_dir, entries)
    md = (render(entries, args.canon_dir, generated) + "\n"
          + render_rename_impact(impact) + "\n"
          + render_open_items(entries, missing, coll))

    counts = {c: sum(1 for e in entries if e["class"] == c) for c in CLASS_ORDER}
    print(f"scanned {len(entries)} documents in {args.canon_dir}")
    for c in CLASS_ORDER:
        print(f"  {c:10} {counts[c]:3}")
    print(f"  documents with an incomplete header: {len(missing)}")
    declared = sum(1 for e in entries if e["status_declared"])
    print(f"  documents declaring a status in a VERSION table: {declared}/{len(entries)}")
    for group in coll["identical_content"]:
        print(f"  IDENTICAL CONTENT: {' | '.join(g[:44] for g in group)}")
    for code, rows in sorted(coll["code_claimed_twice"].items()):
        state = "UNRESOLVED" if code in coll.get("code_claimed_twice_unresolved", {}) else "resolved by deprecation"
        print(f"  CODE SHARED: {code} -> {len(rows)} files ({state})")

    if args.emit_only:
        print("\n--emit-only: nothing written")
        return 0

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(md, encoding="utf-8")
    args.out_json.write_text(json.dumps({
        "schema_version": "1.0.0",
        "record_type": "canon_v0_20_index",
        "stage": "development",
        "generated_utc": generated,
        "canon_dir": str(args.canon_dir),
        "document_count": len(entries),
        "class_counts": counts,
        "code_scheme": "S-11: version prefix dropped, letter code retained",
        "entries": entries,
        "incomplete_headers": missing,
        "dangling_references": DANGLING,
        "collisions": coll,
        "legacy_citation_impact": impact,
    }, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    print(f"\nindex : {args.out_md}")
    print(f"data  : {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
