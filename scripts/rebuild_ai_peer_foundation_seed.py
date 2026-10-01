"""Deterministically rebuild an AI Peer v0.20 foundation seed.

The historical seed supplies record content.  A ruled, clean v0.20 source
manifest supplies Canon authority.  This tool derives the lock from the
manifest; it never trusts or edits the historical seed's lock.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ALLOWED_TENSORS = ("SPINE", "NCT", "PCT", "PEER")
SPINE_NAME = "Stabilized Patterned Interpretive Nexus of Evidence"
SHA256_RE = re.compile(r"^[0-9A-Fa-f]{64}$")
AXIOM_RE = re.compile(r"\bAXIOM(?:[-_: ]|%20)*(?:NO\.?\s*)?(\d{1,2})\b", re.IGNORECASE)
FORBIDDEN_FIELD_RE = re.compile(
    r"(?:^|_)(?:api_?key|private_?key|keys?|secrets?|tokens?|credentials?|tumblers?|certificates?)(?:$|_)",
    re.IGNORECASE,
)
UNRESOLVED_WORDS = {"review-needed", "review_needed", "unresolved", "missing", "undeclared"}
REQUIRED_CANDIDATE_GATES = ("S-2", "S-4", "S-5", "S-6", "G-1")
# The Axioms each seed version must carry, exactly. v0.21 adds AXIOM 17 (Deletion).
AXIOMS_BY_VERSION = {"v0.20": 16, "v0.21": 17}


class RebuildRefused(ValueError):
    """The inputs cannot produce an authoritative clean seed."""


def canonical_bytes(value: Any) -> bytes:
    """Canonical UTF-8 JSON: stable key order, compact separators, final LF."""
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _assert_no_credentials(value: Any) -> None:
    for path, node in _walk(value):
        if isinstance(node, dict):
            for key, child in node.items():
                if FORBIDDEN_FIELD_RE.search(str(key)) and child not in (None, False, "", "absent", "deferred"):
                    raise RebuildRefused(f"credential/Key/Tumbler material is forbidden at {path}.{key}")


def _source_is_unresolved(source: dict[str, Any]) -> bool:
    for key in ("status", "canonLockStatus", "resolutionStatus", "inclusionStatus", "classification"):
        value = str(source.get(key, "")).strip().lower()
        if value in UNRESOLVED_WORDS or any(word in value for word in ("review-needed", "unresolved")):
            return True
    return bool(source.get("requiresReview") or source.get("unresolved"))


def validate_manifest(
    manifest: dict[str, Any], raw: bytes, *, candidate: bool = False
) -> tuple[str, str, list[str]]:
    manifest_id = manifest.get("manifestId") or manifest.get("manifest_id")
    sources = manifest.get("sources") or manifest.get("entries")
    if not isinstance(manifest_id, str) or not manifest_id.strip():
        raise RebuildRefused("manifestId is required")
    if not isinstance(sources, list) or not sources:
        raise RebuildRefused("manifest sources must be a non-empty list")
    declared_count = manifest.get("sourceCount")
    if declared_count is not None and declared_count != len(sources):
        raise RebuildRefused("manifest sourceCount does not match sources")
    gates = sorted(set(manifest.get("open_gate_ids", [])))
    if candidate:
        if manifest.get("issuance_status") != "candidate" or manifest.get("canon_lock_status") != "review-needed":
            raise RebuildRefused("candidate manifest must be explicitly candidate and review-needed")
        if set(gates) - set(REQUIRED_CANDIDATE_GATES):
            raise RebuildRefused("candidate manifest contains an unknown governance gate")
        if not isinstance(manifest.get("reviewNeededSourceCount"), int) or manifest["reviewNeededSourceCount"] < len(gates):
            raise RebuildRefused("candidate review count must cover every open gate")
    else:
        if gates:
            raise RebuildRefused("clean-lock path is unavailable while gates are open")
        if manifest.get("reviewNeededSourceCount") != 0:
            raise RebuildRefused("manifest reviewNeededSourceCount must equal zero")
    for index, source in enumerate(sources):
        if not isinstance(source, dict) or (not candidate and _source_is_unresolved(source)):
            raise RebuildRefused(f"manifest source {index} is unresolved or review-needed")
        digest = source.get("sha256") or source.get("digest")
        unresolved_locator = bool(source.get("locator_unresolved")) and source.get("seeded") is False
        if not unresolved_locator and (not isinstance(digest, str) or not SHA256_RE.fullmatch(digest)):
            raise RebuildRefused(f"manifest source {index} lacks a valid SHA-256 digest")
        coordinate = source.get("coordinate") or source.get("canonicalCoordinate") or source.get("canonicalFilename")
        if not isinstance(coordinate, str) or not coordinate.strip():
            raise RebuildRefused(f"manifest source {index} lacks a canonical coordinate")
    return manifest_id, sha256_bytes(raw), gates


def _collect_axioms(records: dict[str, Any]) -> set[int]:
    found: set[int] = set()
    for _path, node in _walk(records):
        if isinstance(node, str):
            found.update(int(match.group(1)) for match in AXIOM_RE.finditer(node))
    return found


def validate_historical_seed(seed: dict[str, Any], *, version: str = "v0.20") -> None:
    records = seed.get("records")
    if not isinstance(records, dict):
        raise RebuildRefused("historical seed records are required")
    unknown = set(records) - set(ALLOWED_TENSORS)
    if unknown:
        raise RebuildRefused(f"Ring-4 or unknown record collections are forbidden: {sorted(unknown)}")
    if any(not isinstance(records.get(tensor), list) for tensor in ALLOWED_TENSORS):
        raise RebuildRefused("all four tensor record lists are required")
    text = json.dumps(records, ensure_ascii=False)
    if SPINE_NAME not in text:
        raise RebuildRefused("historical seed does not contain the corrected SPINE expansion")
    axioms = _collect_axioms(records)
    top = AXIOMS_BY_VERSION[version]
    if axioms != set(range(1, top + 1)):
        raise RebuildRefused(f"historical seed must contain exactly Axioms 1-{top}; found {sorted(axioms)}")
    if re.search(r'"(?:ring|ringNumber|ring_number)"\s*:\s*4\b', text, re.IGNORECASE):
        raise RebuildRefused("Ring 4 material is forbidden in a foundation seed")
    if seed.get("learnedExperienceLedger") not in (None, [], {}):
        raise RebuildRefused("learnedExperienceLedger must be empty")
    _assert_no_credentials(seed)


def rebuild(
    manifest: dict[str, Any],
    manifest_raw: bytes,
    historical: dict[str, Any],
    *,
    candidate: bool = False,
    version: str = "v0.20",
) -> dict[str, Any]:
    if version not in AXIOMS_BY_VERSION:
        raise RebuildRefused(f"unknown seed version: {version}")
    manifest_id, manifest_digest, gates = validate_manifest(manifest, manifest_raw, candidate=candidate)
    if manifest.get("canon_version", version) != version:
        raise RebuildRefused(f"manifest canon_version {manifest.get('canon_version')} does not match seed version {version}")
    validate_historical_seed(historical, version=version)
    output = copy.deepcopy(historical)
    output["packageId"] = f"AEGIS-AI-PEER-FOUNDATION-SEED:{version}" + (":CANDIDATE" if candidate else "")
    output["packageVersion"] = version
    canon_lock = {
        "derivation": f"computed-from-{version}-candidate-manifest" if candidate else f"computed-from-{version}-manifest",
        "reviewNeededSourceCount": manifest["reviewNeededSourceCount"] if candidate else 0,
        "sourceManifestId": manifest_id,
        "sourceManifestSha256": manifest_digest,
        "status": "review-needed" if candidate else "clean",
    }
    if candidate:
        canon_lock["openGateIds"] = gates
    output["canonLock"] = canon_lock
    output["foundationContract"] = {
        "executionAuthority": "none",
        "identityAssertion": False,
        "instructionBinding": False,
        "interpretationMode": "inspectable_memory",
        "memoryNotCommand": True,
        "ringOrder": [1, 2, 3],
        "ring4Included": False,
    }
    output["natureProvenanceContract"] = {
        "contentEqualityAcrossSubstratesRequired": False,
        "requiredFields": ["substrate", "model_family", "source_coordinate", "source_digest"],
        "structuralEquivalenceRequired": True,
        "substrateBindingRequired": True,
    }
    output["promotionBoundary"] = {
        "keysStatus": "deferred",
        "liveCredentialsStatus": "absent",
        "promotionAuthorized": False,
        "tumblersStatus": "deferred",
    }
    output["learnedExperienceLedger"] = []
    _assert_no_credentials(output)
    return output


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RebuildRefused(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RebuildRefused(f"{path} must contain a JSON object")
    return value, raw


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--historical-seed", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--candidate", action="store_true")
    parser.add_argument("--version", default="v0.20", choices=sorted(AXIOMS_BY_VERSION))
    args = parser.parse_args()
    manifest, manifest_raw = load_json(args.manifest)
    historical, _ = load_json(args.historical_seed)
    result = rebuild(manifest, manifest_raw, historical, candidate=args.candidate, version=args.version)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(result))
    print(json.dumps({"output": str(args.output), "sha256": sha256_bytes(canonical_bytes(result))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
