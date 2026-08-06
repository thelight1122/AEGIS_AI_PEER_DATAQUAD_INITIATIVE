"""Gates on the Canon v0.20 index generator.

The index is only trustworthy if it is derived. These tests pin the parsing behaviour that
the derivation depends on — in particular the three distinct header formats found in the
Canon directory, where a parser that handles only the first silently reports a document as
having no status when it plainly declares one.

The header-format tests are pure and run anywhere. Tests that read the Canon directory are
skipped when it is not mounted, per ADR-0001.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_canon_index", ROOT / "scripts" / "build_canon_index.py")
idx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(idx)

canon_available = pytest.mark.skipif(
    not idx.DEFAULT_CANON_DIR.exists(),
    reason="Canon directory not mounted (ADR-0001 environment-bound)",
)


# --- the three header formats -------------------------------------------------------------

VERSION_TABLE = """# TITLE

## VERSION

| Field | Value |
|---|---|
| Document | AEGIS Canon Addendum — SPINE |
| Version | v1.0-SP |
| Status | ACTIVE |
| Source | one |
| | two |
| Supersedes | Canon v1.0 glossary entry |
| Added to Canon | 2026-04-11 |
"""

BOLD_HEADER = """# TITLE

**Code:** v1.0-OT
**Status:** ACTIVE
**Supersedes:** Nothing — new Canon.
**Illumination:** Tracey Prutch, 2026-06-12
"""

BLOCKQUOTED = """# TITLE

> **Status:** ACTIVE
> **Code:** v1.0-RS
> **Produced:** 2026-06-12
> **Supersedes:** Nothing — new Canon
"""


def test_version_table_is_parsed():
    f = idx.parse_version_table(VERSION_TABLE)
    assert f["Version"] == "v1.0-SP"
    assert f["Status"] == "ACTIVE"
    assert f["Added to Canon"] == "2026-04-11"


def test_continuation_rows_accumulate_rather_than_overwrite():
    """The Source field spans several rows; an overwrite would silently drop provenance."""
    f = idx.parse_version_table(VERSION_TABLE)
    assert f["Source"] == ["one", "two"]


def test_bold_header_is_parsed():
    f = idx.parse_bold_header(BOLD_HEADER)
    assert f["Code"] == "v1.0-OT"
    assert f["Status"] == "ACTIVE"


def test_blockquoted_bold_header_is_parsed():
    """Ten addenda were reported as UNDECLARED because of a leading '> '."""
    f = idx.parse_bold_header(BLOCKQUOTED)
    assert f["Code"] == "v1.0-RS"
    assert f["Status"] == "ACTIVE"


def test_date_extraction_prefers_the_first_available_field():
    assert idx.first_date(None, "Tracey Prutch, 2026-06-12") == "2026-06-12"
    assert idx.first_date(["a", "b 2026-04-11"]) == "2026-04-11"
    assert idx.first_date(None, "no date here") is None


# --- classification -----------------------------------------------------------------------


def test_addendum_index_is_not_classified_as_an_addendum():
    assert idx.classify(Path("📘 AEGIS CANON ADDENDUM INDEX.md"), {}) == "OTHER"


def test_addendum_detected_by_filename_and_by_document_field():
    assert idx.classify(Path("📘 AEGIS CANON ADDENDUM — SPINE v1.0-SP.md"), {}) == "ADDENDUM"
    assert idx.classify(Path("SHADOW AFFECTS v1.1-S.md"),
                        {"Document": "AEGIS Canon Addendum — Shadow Affects"}) == "ADDENDUM"


def test_kernel_membership_is_transcribed_not_inferred():
    assert idx.classify(Path("AEGIS Canonical Glossary v1.0.md"), {}) == "KERNEL"
    assert idx.classify(Path("AEGIS STANDARDS v0.1.md"), {}) == "KERNEL"
    assert idx.classify(Path("BIOPEER_DOCTRINE.md"), {}) == "UNINDEXED"


# --- ruling S-11: drop the version prefix, keep the letter code -----------------------------


def test_version_prefix_is_dropped():
    assert idx.canonical_code("v1.0-SP", "x.md") == "SP"
    assert idx.canonical_code("v1.0-EPC", "x.md") == "EPC"
    assert idx.canonical_code("v1.0-A2", "x.md") == "A2"


def test_minor_version_is_dropped_too_not_just_v1_0():
    """Shadow Affects is v1.1-S, not v1.0-S; the rule is prefix-agnostic."""
    assert idx.canonical_code("v1.1-S", "x.md") == "S"


def test_bare_version_falls_back_to_the_appendix_acronym():
    """Four appendices carry a bare v1.0; a literal strip would leave them unidentified."""
    assert idx.canonical_code("v1.0", "📘 AEGIS CANON APPENDIX — HME v1.md") == "HME"
    assert idx.canonical_code("v1.0", "📘 AEGIS CANON APPENDIX — MOP v1.md") == "MOP"


def test_no_code_is_invented_when_none_can_be_derived():
    assert idx.canonical_code(None, "BIOPEER_DOCTRINE.md") is None
    assert idx.canonical_code("v1.0", "SOME UNRELATED DOC.md") is None


def test_dependency_graph_is_keyed_by_canonical_codes():
    """A stale legacy key here would silently empty every Depends-on cell."""
    assert "EPC" in idx.DEPENDENCY_TIER
    assert not any(k.startswith("v1.") for k in idx.DEPENDENCY_TIER)
    assert not any(k.startswith("v1.") for k in idx.DEPENDS_ON)
    for deps in idx.DEPENDS_ON.values():
        for d in deps:
            assert not d.startswith("v1."), f"legacy code in dependency list: {d}"


# --- the derivation, against the real corpus ------------------------------------------------


@canon_available
def test_every_addendum_resolves_a_status():
    """A parser regression here silently reports declared statuses as UNDECLARED."""
    entries = idx.scan(idx.DEFAULT_CANON_DIR)
    addenda = [e for e in entries if e["class"] == "ADDENDUM"]
    assert addenda, "no addenda found"
    undeclared = [e["file"] for e in addenda if not e["status_declared"]]
    assert not undeclared, f"addenda with unresolved status: {undeclared}"


@canon_available
def test_no_addendum_is_locked():
    """The prior index's preamble claims every addendum is locked. None is.

    DEPRECATED joined the set on 2026-08-06 with ruling S-9; the Canon being pre-release,
    LOCKED remains the status that must not appear.
    """
    entries = idx.scan(idx.DEFAULT_CANON_DIR)
    statuses = {e["status_declared"] for e in entries if e["class"] == "ADDENDUM"}
    assert "LOCKED" not in statuses
    assert statuses <= {"ACTIVE", "PROPOSED", "DEPRECATED"}, f"unexpected status: {statuses}"


@canon_available
def test_kernel_and_appendix_counts_match_the_prior_index():
    """The prior index lists 5 original Canon documents and 7 appendices."""
    entries = idx.scan(idx.DEFAULT_CANON_DIR)
    counts = {c: sum(1 for e in entries if e["class"] == c) for c in idx.CLASS_ORDER}
    assert counts["KERNEL"] == 5
    assert counts["APPENDIX"] == 7


@canon_available
def test_known_collisions_are_still_detected():
    """Both are open items; if either disappears, the index must stop reporting it."""
    entries = idx.scan(idx.DEFAULT_CANON_DIR)
    coll = idx.collisions(idx.DEFAULT_CANON_DIR, entries)
    assert any("STANDARDS" in f for group in coll["identical_content"] for f in group)
    assert "S" in coll["code_claimed_twice"], "the two Shadow Affects files both claim S"


@canon_available
def test_standards_bounds_merge_conflict_is_resolved():
    """Steward ruling S-3, 2026-08-06.

    The file carried an unresolved Git merge conflict whose markers had been backslash-escaped
    and Markdown-mangled, so it rendered as ordinary prose rather than as obvious breakage.
    Both sides are standards for different applications and both were preserved.

    The provenance note deliberately quotes the removed markers to document the repair, so the
    assertions run against the document body only.
    """
    path = idx.DEFAULT_CANON_DIR / "STANDARDS_BOUNDS.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    body = text[text.index("# Part I"):]

    import re
    assert not re.search(r"^(<{7}|={7}|>{7})", body, re.M), "raw conflict markers in body"
    assert not re.search(r"^>\s*0fc14ea", body, re.M), "closing marker still present"
    assert "\\<\\<\\<" not in body, "escaped opening marker in body"
    assert "\xa0" not in body, "non-breaking space separator still present"

    # Escaping damage inside code spans, where Markdown does not process escapes.
    for tok in ("AWARENESS\\_ACK", "LENS\\_REVIEW", "CoLAB\\_APP", "/tools/\\*"):
        assert tok not in body, f"escaping damage not repaired: {tok}"

    # Both sides must survive — commit 0fc14ea is in no local repo, so this file is the
    # only record of either.
    assert "AEGIS Education Chamber: Standards & Bounds" in body
    assert "AEGIS-CoLAB_APP Standards & Constraints" in body
    assert "computeInclusionState" in body and "Single Active Session" in body


@canon_available
def test_rbc_chamber_is_named_response_not_resonance():
    """Steward ruling S-7, 2026-08-06.

    The inception document (AEGIS Sentinel Foundational Principles, STUD 2) says RESPONSE
    Buffer Chamber five times and never says Resonance. "Resonance" entered the corpus through
    a transcription error in the Addendum Index and propagated from there — including into one
    seed package copy. If it reappears, something was restored from a pre-fix source.
    """
    offenders = {}
    for path in idx.DEFAULT_CANON_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        n = text.count("Resonance Buffer Chamber")
        if not n:
            continue
        # The index legitimately quotes the old term inside its RESOLVED note, to explain what
        # was corrected and why. Those mentions are the record of the fix, not a regression.
        if "ADDENDUM INDEX" in path.name.upper() and "RESOLVED" in text:
            continue
        offenders[path.name] = n
    assert not offenders, f"'Resonance Buffer Chamber' reappeared: {offenders}"


@canon_available
def test_reflective_boundary_conditions_was_not_collateral_damage():
    """A separate concept, never in dispute. The RBC fix must not have touched it.

    Counted across both Canon directories, since the corpus is duplicated between them:
    11 in CANON_FOUNDATIONAL_DOCS plus 14 at the TIER-1-CANON level.
    """
    dirs = [idx.DEFAULT_CANON_DIR, idx.DEFAULT_CANON_DIR.parent]
    total = sum(p.read_text(encoding="utf-8", errors="replace").count("Reflective Boundary Conditions")
                for d in dirs for p in d.glob("*.md"))
    assert total == 25, f"expected 25 occurrences across both directories, found {total}"


@canon_available
def test_shared_S_code_is_reported_as_resolved_not_open():
    """Ruling S-9 deprecated one of the two; a shared code with one live doc is unambiguous."""
    entries = idx.scan(idx.DEFAULT_CANON_DIR)
    coll = idx.collisions(idx.DEFAULT_CANON_DIR, entries)
    assert "S" not in coll["code_claimed_twice_unresolved"]
    assert not coll["code_claimed_twice_unresolved"], "an unresolved code collision remains"


@canon_available
def test_every_addendum_carries_both_code_forms():
    """The index is only usable during migration if it maps old citations to new codes."""
    entries = idx.scan(idx.DEFAULT_CANON_DIR)
    for e in (x for x in entries if x["class"] == "ADDENDUM"):
        assert e["code"], f"no canonical code: {e['file']}"
        assert e["code_legacy"], f"no legacy code: {e['file']}"
        assert not e["code"].startswith("v1."), f"prefix not dropped: {e['code']}"


#: Shadow Affects stamps its own sections with the revision that added them (`v1.2-S` ..
#: `v1.5-S`). Those are revision history, not cross-references to another addendum, and the
#: S-11 migration wrongly flattened them before they were restored. They are expected to
#: remain in `vN.N-S` form and must not be "migrated" again.
SHADOW_AFFECTS_REVISION_STAMPS = {"v1.2-S", "v1.3-S", "v1.4-S", "v1.5-S"}


@canon_available
def test_migration_is_complete_apart_from_revision_stamps():
    """S-11 was applied to disk on 2026-08-06: 53 files renamed, 784 citations rewritten.

    This asserted `> 0` before the migration, which was the right gate then. Now the
    invariant is the opposite — a legacy `vN.N-XX` code reappearing means something was
    restored from a pre-migration copy or authored against the old scheme. The one sanctioned
    exception is Shadow Affects' own revision history.
    """
    entries = idx.scan(idx.DEFAULT_CANON_DIR)
    impact = idx.citation_impact(idx.DEFAULT_CANON_DIR, entries)
    unexpected = {c: d for c, d in impact["codes"].items()
                  if c not in SHADOW_AFFECTS_REVISION_STAMPS}
    assert not unexpected, f"legacy codes reappeared: {unexpected}"


@canon_available
def test_shadow_affects_revision_history_survived_the_migration():
    """The migration erased which increment added which section; the repair restored it.

    Without this gate, a re-run of migrate_canon_codes.py would silently flatten them again.
    """
    big = [p for p in idx.DEFAULT_CANON_DIR.glob("*.md")
           if "ADDENDUM" in p.name.upper() and "SHADOW" in p.name.upper()]
    assert len(big) == 1, f"expected one current Shadow Affects document, found {len(big)}"
    text = big[0].read_text(encoding="utf-8")
    for stamp in sorted(SHADOW_AFFECTS_REVISION_STAMPS):
        assert stamp in text, f"revision stamp lost: {stamp}"


@canon_available
def test_superseded_shadow_affects_copy_is_deprecated_not_deleted():
    """Steward ruling S-9. Deprecated in this Canon means outranked, not removed."""
    small = idx.DEFAULT_CANON_DIR / "SHADOW AFFECTS S.md"
    assert small.exists(), "the superseded copy must be preserved, not deleted"
    text = small.read_text(encoding="utf-8")
    assert "| Status | DEPRECATED |" in text
    assert "Superseded by" in text


@canon_available
def test_no_filename_still_carries_a_legacy_code():
    stragglers = [p.name for p in idx.DEFAULT_CANON_DIR.glob("*.md")
                  if __import__("re").search(r"v\d+\.\d+-[A-Z0-9]+", p.name)]
    assert not stragglers, f"filenames not migrated: {stragglers}"
