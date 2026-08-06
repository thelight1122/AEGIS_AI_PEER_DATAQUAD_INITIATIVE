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
    """The prior index's preamble claims every addendum is locked. None is."""
    entries = idx.scan(idx.DEFAULT_CANON_DIR)
    statuses = {e["status_declared"] for e in entries if e["class"] == "ADDENDUM"}
    assert "LOCKED" not in statuses
    assert statuses <= {"ACTIVE", "PROPOSED"}


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
    assert "v1.1-S" in coll["code_claimed_twice"]
