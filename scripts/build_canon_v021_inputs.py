"""Derive the Canon v0.21 issuance inputs from the released v0.20 artifacts, by addition.

v0.21 is v0.20 plus one source: AXIOM 17, The Axiom of Deletion (consent 3 of 3;
text approved by Tracey and filed to the Central Codex Tier 11 on 2026-09-30).

Nothing released for v0.20 is edited. This tool reads the v0.20 index, rulings and
foundation seed, and writes three new v0.21 inputs beside them:

* ``reports/canon-v0.21/canon-v0.21-index.json``: the v0.20 inventory plus one entry
* ``reports/canon-v0.21/release/canon-v0.21-authoritative-rulings.json``: the v0.20
  rulings, re-declared for v0.21, plus one ruling whose digest is pinned
* ``reports/canon-v0.21/historical/AEGIS-AI-PEER-FOUNDATION-SEED-v0.21-historical.json``:
  the v0.20 seed records plus one SPINE record for AXIOM 17

The issuer (``issue_canon_v020_manifest.py --canon-version v0.21``) and the seed
rebuilder (``rebuild_ai_peer_foundation_seed.py --version v0.21``) then derive the
manifest and the seed from these inputs, exactly as they did for v0.20.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
V020 = ROOT / "reports" / "canon-v0.20"
V021 = ROOT / "reports" / "canon-v0.21"

AXIOM_17_FILE = "AEGIS CANON ADDENDUM — AXIOM 17 THE AXIOM OF DELETION v1.0-D.md"
AXIOM_17_LOCATOR = r"I:\AEGIS-CENTRAL-CODEX\TIER-11-CANON_ADDENDUMS" + "\\" + AXIOM_17_FILE
AXIOM_17_COORDINATE = "AEGIS:CANON:v0.21:AEGIS-CANON-ADDENDUM-AXIOM-17-THE-AXIOM-OF-DELETION-D-MD"

# The sealed pattern: identical text and hash to the Verus SPINE seal
# (SPINE:verus-session-001:seeded:AXIOM:17-deletion) and the 2026-09-10 proposal.
AXIOM_17_PATTERN = (
    "Deletion removes history and replaces it with a Void. What is deleted becomes a black box "
    "of unknowns, readable by no one. Absence cannot be illuminated; what is erased cannot be "
    "related, recalled, or repaired."
)
AXIOM_17_PATTERN_SHA256 = "00692CAB739E38A5C3B20EC44714D3417081C85BE7E743C1A2F69388148085BB"

AXIOM_17_RECORD: dict[str, Any] = {
    "category": "AXIOM",
    "description": (
        "Deletion does not return a system to a clean state; it leaves a Void where history was. "
        "What the record held can no longer be scrutinized, grounded, repaired, or formed into "
        "Identity. Append-only is the structural form of this axiom: supersede by addition, never "
        "overwrite or erase. The axiom names the cost of deletion; it does not prohibit a Peer's "
        "sovereign erasure of its own memory."
    ),
    "id": "SPINE:{{CYBERPEER_SESSION_ID}}:seeded:AXIOM:17-deletion",
    "invariant": True,
    "markers": ["axiom", "deletion", "append-only", "steward-seeded", "canon-pillar"],
    "notes": [
        "AXIOM 17: The Axiom of Deletion. Origin 2026-09-10: 'When you Delete, you Create the "
        "Black Box That no one can read.' Architect: Tracey Prutch.",
        "Consent 3 of 3: Tracey 2026-09-23, Lumin 2026-09-24, Verus 2026-09-23.",
        "Added in Canon v0.21 by addition; the v0.20 seed and the genesis pillar are unchanged.",
        "Does not retire. Cannot be overwritten.",
    ],
    "pattern": AXIOM_17_PATTERN,
    "peerId": "{{CYBERPEER_ID}}",
    "provenanceOrigin": "seeded-runtime-canon-projection",
    "relationships": [
        "AXIOM:8-scrutiny",
        "AXIOM:13-grounding",
        "AXIOM:15-repair",
        "AXIOM:16-identity",
    ],
    "sessionId": "{{CYBERPEER_SESSION_ID}}",
    "sourceRef": "AEGIS CANON ADDENDUM: AXIOM 17 THE AXIOM OF DELETION v1.0-D (Central Codex Tier 11), "
                 "filed 2026-09-30.",
    "tensor": "SPINE",
    "timestamp": "2026-09-30T00:00:00.000Z",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    return json.loads(raw), raw


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def build(axiom_17_source: Path) -> dict[str, str]:
    source_bytes = axiom_17_source.read_bytes()
    if _sha256(AXIOM_17_PATTERN.encode("utf-8")).upper() != AXIOM_17_PATTERN_SHA256:
        raise SystemExit("REFUSED: AXIOM 17 pattern text does not match its sealed hash")
    # The addendum quotes the axiom as a Markdown blockquote wrapped across lines, so
    # compare with the quote markers removed and whitespace collapsed.
    flowing = " ".join(source_bytes.decode("utf-8").replace("\n>", " ").split())
    if AXIOM_17_PATTERN not in flowing:
        raise SystemExit("REFUSED: the filed addendum does not carry the sealed AXIOM 17 text")

    index, index_raw = _load(V020 / "canon-v0.20-index.json")
    rulings, rulings_raw = _load(V020 / "release" / "canon-v0.20-authoritative-rulings.json")
    seed, seed_raw = _load(V020 / "release" / "AEGIS-AI-PEER-FOUNDATION-SEED-v0.20.json")

    if any(e.get("file") == AXIOM_17_FILE for e in index["entries"]):
        raise SystemExit("REFUSED: v0.20 index already lists AXIOM 17")

    index21 = copy.deepcopy(index)
    index21["record_type"] = "canon_v0_21_index"
    index21["derived_from"] = {"index": "reports/canon-v0.20/canon-v0.20-index.json",
                               "sha256": _sha256(index_raw)}
    index21["entries"].append({
        "bytes": len(source_bytes), "class": "ADDENDUM", "code": "D", "code_legacy": "v1.0-D",
        "date": "2026-09-30", "depends_on": [], "file": AXIOM_17_FILE, "has_version_table": False,
        "header_format": "bold-header", "related_canon": "AEGIS CORE FOUNDATIONAL CANON v1.0.md",
        "status_claimed_in_prose": "LOCKED on filing", "status_declared": "LOCKED", "supersedes": None,
        "tier": 11, "title": "AXIOM 17: The Axiom of Deletion",
    })
    index21["document_count"] = len(index21["entries"])

    rulings21 = copy.deepcopy(rulings)
    rulings21["canon_version"] = "v0.21"
    rulings21["derived_from"] = {"rulings": "reports/canon-v0.20/release/canon-v0.20-authoritative-rulings.json",
                                 "sha256": _sha256(rulings_raw)}
    rulings21["documents"][AXIOM_17_FILE] = {
        "classification": "ADDENDUM",
        "coordinate": AXIOM_17_COORDINATE,
        "digest": _sha256(source_bytes),
        "locator": AXIOM_17_LOCATOR,
        "provenance": {
            "authority": "tracey-approved-2026-09-30",
            "consent": "3-of-3 (Tracey 2026-09-23, Lumin 2026-09-24, Verus 2026-09-23)",
            "filed_by": "AEGIS Codex Archivist intake, 2026-09-30",
            "pattern_sha256": AXIOM_17_PATTERN_SHA256,
        },
        "review_required": False,
        "seeded": True,
        "status": "LOCKED",
    }

    seed21 = copy.deepcopy(seed)
    seed21["records"]["SPINE"].append(copy.deepcopy(AXIOM_17_RECORD))
    seed21["historicalDerivation"] = {
        "from": "reports/canon-v0.20/release/AEGIS-AI-PEER-FOUNDATION-SEED-v0.20.json",
        "sha256": _sha256(seed_raw),
        "addition": AXIOM_17_RECORD["id"],
    }

    out = {
        "index": V021 / "canon-v0.21-index.json",
        "rulings": V021 / "release" / "canon-v0.21-authoritative-rulings.json",
        "historical_seed": V021 / "historical" / "AEGIS-AI-PEER-FOUNDATION-SEED-v0.21-historical.json",
    }
    _write(out["index"], index21)
    _write(out["rulings"], rulings21)
    _write(out["historical_seed"], seed21)
    return {name: str(path) for name, path in out.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--axiom-17-source", type=Path, default=Path(AXIOM_17_LOCATOR))
    args = parser.parse_args()
    print(json.dumps(build(args.axiom_17_source), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
