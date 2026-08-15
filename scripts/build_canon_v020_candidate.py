"""Build explicitly non-authoritative Canon v0.20 candidate artifacts.

This command reads the current generated index, derives provisional inventory
rulings, and emits only review-needed artifacts beneath the requested candidate
directory.  It cannot issue an authoritative manifest or a clean seed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts.issue_canon_v020_manifest import REQUIRED_CANDIDATE_GATES, issue
    from scripts.rebuild_ai_peer_foundation_seed import canonical_bytes, load_json, rebuild, sha256_bytes
except ModuleNotFoundError:  # Direct execution places scripts/ itself on sys.path.
    from issue_canon_v020_manifest import REQUIRED_CANDIDATE_GATES, issue
    from rebuild_ai_peer_foundation_seed import canonical_bytes, load_json, rebuild, sha256_bytes


def _slug(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    return clean[:72] or hashlib.sha256(value.encode("utf-8")).hexdigest()[:16].upper()


def derive_candidate_rulings(index: dict[str, Any]) -> dict[str, Any]:
    entries = index.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("current index must contain entries")
    documents: dict[str, Any] = {}
    canon_dir = Path(index.get("canon_dir", "."))
    for entry in entries:
        filename = entry.get("file")
        if not isinstance(filename, str) or not filename:
            raise ValueError("every current index entry must name a file")
        classification = entry.get("class") or "UNDECLARED"
        status = entry.get("status_declared") or entry.get("status_claimed_in_prose") or "UNDECLARED"
        locator_missing = not (canon_dir / filename).is_file()
        documents[filename] = {
            "classification": classification,
            "coordinate": f"AEGIS:CANON:v0.20:CANDIDATE:{_slug(filename)}",
            "locator": filename,
            "provenance": {
                "authority": "current-index-inventory-only",
                "index_file": filename,
                "provisional": True,
            },
            "review_required": locator_missing or classification == "UNINDEXED" or status == "UNDECLARED",
            "seeded": not locator_missing and classification in {"KERNEL", "APPENDIX", "ADDENDUM"},
            "status": status,
        }
        if locator_missing:
            documents[filename]["locator_unresolved"] = True
            documents[filename]["provenance"]["locator_drift"] = "indexed locator absent on current disk"
    return {
        "canon_version": "v0.20",
        "documents": documents,
        "open_gate_ids": list(REQUIRED_CANDIDATE_GATES),
        "references": {},
        "ruling_status": "candidate",
    }


def _write_json(path: Path, value: Any, *, canonical: bool = False) -> bytes:
    data = canonical_bytes(value) if canonical else (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def build(index_path: Path, historical_seed_path: Path, output_dir: Path) -> dict[str, Any]:
    index_raw = index_path.read_bytes()
    index = json.loads(index_raw)
    if not isinstance(index, dict):
        raise ValueError("current index root must be an object")
    rulings = derive_candidate_rulings(index)
    rulings_path = output_dir / "canon-v0.20-candidate-rulings.json"
    _write_json(rulings_path, rulings)
    manifest = issue(
        index_path,
        rulings_path,
        candidate=True,
        open_gate_ids=list(REQUIRED_CANDIDATE_GATES),
    )
    manifest_path = output_dir / "canon-v0.20-candidate-manifest.json"
    manifest_raw = _write_json(manifest_path, manifest, canonical=True)
    historical, _ = load_json(historical_seed_path)
    seed = rebuild(manifest, manifest_raw, historical, candidate=True)
    seed_path = output_dir / "ai-peer-foundation-seed-v0.20-candidate.json"
    seed_raw = _write_json(seed_path, seed, canonical=True)
    report = {
        "artifact_status": "candidate-review-needed",
        "canon_lock_status": seed["canonLock"]["status"],
        "invariants": {
            "axiom_count": 16,
            "credentials_present": False,
            "memory_not_command": True,
            "ring4_included": False,
            "spine_name": "Stabilized Patterned Interpretive Nexus of Evidence",
        },
        "manifest_digest_bound_in_seed": seed["canonLock"]["sourceManifestSha256"],
        "open_gate_ids": list(REQUIRED_CANDIDATE_GATES),
        "outputs": {
            "manifest": {"path": str(manifest_path), "sha256": sha256_bytes(manifest_raw)},
            "rulings": {"path": str(rulings_path), "sha256": sha256_bytes(rulings_path.read_bytes())},
            "seed": {"path": str(seed_path), "sha256": sha256_bytes(seed_raw)},
            "source_index": {"path": str(index_path), "sha256": sha256_bytes(index_raw)},
        },
    }
    _write_json(output_dir / "candidate-build-report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--historical-seed", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = build(args.index, args.historical_seed, args.output_dir)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
