# -*- coding: utf-8 -*-
"""
Step 4 (Workstream B): rebuild Gabe's per-peer IdentityImage from his FOUND/lived layer.

Provenance-coupled: found = SPINE:<peer>:* (his 2 relational anchors); given = SPINE:foundation:* (the
seeded shared Foundation, referenced not carried). Lived content = his held tension (care vs protection)
+ integration event. Reuses the formalized identity_image module + the existing Builder Orb.
Local/offline; read-only source; no live system.
"""
import json, os, sys

ROOT = r"H:/AEGIS-POD-ARCHITECTURE"
sys.path.insert(0, os.path.join(ROOT, "packages", "orb-identity-field-builder-core", "src"))
from orb_identity_field_builder_core.identity_image import (
    build_peer_identity_image, foundation_reference, peer_found_invariant_anchors,
)

RECS = os.path.join(ROOT, "stage-gabe-out/live-copies/CP-1003-GABE/gabe-live-copy-20260725T063622Z/pod/records")
FIX = os.path.join(ROOT, "fixtures")
EDITION_MANIFEST = r"G:/THE_CYBERPEER_CANON/_edition-manifest.json"
OUT = os.path.join(ROOT, "reports/runtime/step4-identity-image/gabe-identity-image-v2.json")


def main():
    # FOUND relational anchors, by provenance, from the real invariant SPINE
    inv = [json.loads(l)["body"] for l in open(os.path.join(RECS, "SPINE.jsonl"), encoding="utf-8")
           if l.strip() and json.loads(l)["body"].get("invariant")]
    anchors = peer_found_invariant_anchors(inv)

    # Gabe's real lived-layer content
    held = json.load(open(os.path.join(FIX, "held-tension-care-protection.json"), encoding="utf-8"))
    integ = json.load(open(os.path.join(FIX, "integration-event-peer-recognized.json"), encoding="utf-8"))
    manifest = json.load(open(EDITION_MANIFEST, encoding="utf-8"))
    foundation = foundation_reference(manifest)

    packet = build_peer_identity_image(
        peer_id="CP-1003-GABE", self_name="Gabe",
        anchor_patterns=anchors, foundation=foundation,
        held_tensions=[held], integration_events=[integ],
    )
    json.dump(packet, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print("=== Gabe per-peer IdentityImage v2 (lived/found layer) ===")
    print("FOUND relational anchors (provenance-true):", len(anchors))
    for a in anchors:
        print("   -", a[:80])
    b = packet["budget"]
    print(f"budget: {b['actual_chars']} / {b['max_chars']}  within_budget={b['within_budget']}")
    print("active_held_tensions:", [t["id"] for t in packet["active_held_tensions"]])
    print("integration_markers :", packet["integration_markers"])
    print("relationship_posture:", packet["relationship_posture"][:120])
    print("standing_commitments:", packet["standing_commitments"], "| active_boundaries:", packet["active_boundaries"])
    print("negative_space all-false:", all(v is False for v in packet["negative_space_policy"].values()))
    print("foundation referenced:", packet["foundation_context"]["canon_identity_refs"][0][:60], "...")
    # provenance-clean: NO seeded-Foundation text in the packet
    blob = json.dumps(packet, ensure_ascii=False)
    leak = [tok for tok in ("AXIOM", "IMPERATIVE:", "STANDARD:", "GATE:", "NATURE:") if tok in blob]
    print("given-Foundation leak:", leak or "NONE")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
