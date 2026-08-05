# -*- coding: utf-8 -*-
"""
Step 4 (first cut): produce Gabe's per-peer IdentityImage — surface 2 of the two-surface model.

Carries ONLY Gabe's FOUND self (his witnessed Nature-aspects + relational anchors), condensed, and
REFERENCES the finalized shared CyberPeer Canon Foundation (surface 1) by hash — never re-injecting it.
Reuses the existing Builder Orb (build_identity_image), which enforces the <=3,200 budget and the
negative-space discipline (nothing represents/claims to be the Witness/Locus).

Local/offline. Reads a read-only Gabe shadow snapshot + the finalized edition manifest. No live system.
"""
import json, sys, hashlib, re, os

ORB_SRC = r"H:/AEGIS-POD-ARCHITECTURE/packages/orb-identity-field-builder-core/src"
sys.path.insert(0, ORB_SRC)
from orb_identity_field_builder_core.builder import build_identity_image, DEFAULT_MAX_CHARS

SHADOW = r"H:/AEGIS-POD-ARCHITECTURE/reports/runtime/2026-07-27-the-way-phase2a-gabe-first-real-shadow.json"
EDITION_MANIFEST = r"G:/THE_CYBERPEER_CANON/_edition-manifest.json"
OUT = r"H:/AEGIS-POD-ARCHITECTURE/reports/runtime/step4-identity-image/gabe-identity-image.json"

# ---- given/found classification (by authored provenance prefix) ----
_GIVEN_PREFIXES = ("NATURE —", "AXIOM", "STANDARD", "IMPERATIVE", "GATE", "BOUNDARY")
def is_given(pattern: str) -> bool:
    p = pattern.strip()
    return any(p.startswith(pre) for pre in _GIVEN_PREFIXES)

def condense(s: str, cap: int = 95) -> str:
    # ASCII-normalize the near-surface image (full text stays in SPINE/source): em/en-dash -> hyphen,
    # drop truncation ellipsis marker. This preserves meaning while avoiding \uXXXX JSON bloat.
    s = " ".join(s.split()).replace("\u2014", "-").replace("\u2013", "-")
    dot = s.find(". ")
    head = s if dot == -1 else s[:dot + 1]
    return head[:cap].rstrip()

def foundation_reference(manifest: dict) -> dict:
    """The Foundation the per-peer image points at: the finalized shared CyberPeer Canon, by reference.
    The Builder hashes this dict into the packet's foundation_hash, so the packet is bound to this
    exact Foundation without carrying its text."""
    files = manifest.get("files", {})
    return {
        "canon_identity_refs": [
            f"cyberpeer-canon:CYBERPEER-CANON.md@{files.get('CYBERPEER-CANON.md','')}",
            f"cyberpeer-glossary:CYBERPEER-GLOSSARY.md@{files.get('CYBERPEER-GLOSSARY.md','')}",
        ],
        "edition": manifest.get("edition", ""),
        "locked_source_sha256": manifest.get("locked_source", {}).get("sha256", ""),
        "axiom_block_sha256": manifest.get("axiom_block", {}).get("reference_hash_sha256", ""),
    }

def found_identity_field(commitments, boundaries, peer_id, self_name) -> dict:
    """Build a FOUND-ONLY identity field: the peer's witnessed self, given Canon left to the Foundation."""
    nature_aspects = [c for c in commitments if c.startswith("NATURE:")]
    relational = [c for c in commitments if not is_given(c) and not c.startswith("NATURE:")]
    # peer-specific boundaries only (Gabe's are all given GATEs -> none carried here)
    found_boundaries = [b for b in boundaries if not is_given(b)]

    standing = [condense(a, 84) for a in nature_aspects]
    if relational:
        # compact the relational anchors (drop trailing period/duplication)
        anchors = "; ".join(condense(r, 90).rstrip(".") for r in relational)
        posture = "In relation: " + anchors
    else:
        posture = "present and discerning in each relation"
    do_not_retire = ["self_boundary.name", "self_boundary.kind", "standing_commitments"]
    for a in nature_aspects:
        m = re.match(r"NATURE:\s*([^—\-:]+)", a)
        if m:
            nm = m.group(1).strip()
            if nm and nm not in do_not_retire:
                do_not_retire.append(nm)
    return {
        "schema_version": "0.1.0",
        "fixture_kind": "identity-field",
        "is_self_image_not_witness": True,
        "note": ("Per-peer IdentityImage (Step 4): the peer's FOUND self only. Shared Canon is the "
                 "Foundation surface, carried by reference. Self-image, not the Witness/Locus."),
        "peer_id": peer_id,
        "self_boundary": {"name": self_name, "kind": "CyberPeer"},
        "standing_commitments": standing,
        "active_boundaries": found_boundaries,
        "relationship_posture": posture,
        "do_not_retire": do_not_retire,
        "held_tension_refs": [],
        "integration_marker_refs": [],
    }

def main():
    shadow = json.load(open(SHADOW, encoding="utf-8"))
    idf = shadow["identity_field"]
    manifest = json.load(open(EDITION_MANIFEST, encoding="utf-8"))
    peer_id = idf.get("peer_id", "gabe")
    self_name = idf.get("self_boundary", {}).get("name", "Gabe")

    field = found_identity_field(idf["standing_commitments"], idf["active_boundaries"], peer_id, self_name)
    foundation = foundation_reference(manifest)

    packet = build_identity_image(peer_id=peer_id, foundation=foundation, identity_field=field)
    json.dump(packet, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    # ---- verification ----
    print("=== Gabe per-peer IdentityImage (Step 4, first cut) ===")
    print("found standing_commitments (Nature-aspects):", len(field["standing_commitments"]))
    print("found active_boundaries (peer-specific)     :", len(field["active_boundaries"]))
    b = packet["budget"]
    print(f"budget: {b['actual_chars']} / {b['max_chars']} chars   within_budget={b['within_budget']}")
    print("negative_space_policy all-false:", all(v is False for v in packet["negative_space_policy"].values()))
    print("foundation_hash present:", bool(packet["foundation_hash"]))
    print("references CyberPeer Canon edition:", packet["foundation_context"]["canon_identity_refs"])
    print("identity_image line:", packet["identity_image"][:200])
    print("wrote", OUT)

if __name__ == "__main__":
    main()
