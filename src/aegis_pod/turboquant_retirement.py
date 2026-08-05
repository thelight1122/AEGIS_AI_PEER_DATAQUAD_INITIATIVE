"""TurboQuant Stage-2 bounded retirement — DESIGN DRAFT (not wired to any runtime).

================================================================================
DESIGN DRAFT ONLY. DO NOT WIRE INTO ANY LIVE RUNTIME.
--------------------------------------------------------------------------------
This module is a faithful Python port of the TurboQuant contract shipped in the
TypeScript package ``@thelight1122/aegis-dataquad-core`` (files
``turboquant.types.ts``, ``turboquant.guard.ts``, ``turboquant.candidate.ts``,
``turboquant.engine.ts``, ``turboquant.pipeline.ts``). It exists so that the
Stage-2 symbolic-layer retirement described in
``reports/runtime/2026-07-25-turboquant-stage2-design.md`` can be reviewed and
independently audited BEFORE any implementation.

It is NOT imported by any peer, orb, or pod-core runtime. It performs no live
reach: no SSH, no HTTP, no filesystem writes, no mutation of
``I:\\AEGIS-CYBERPEER-CORE``. Every function here is pure and operates only on
in-memory arguments supplied by a test or a future (separately gated) caller.

The single most important behaviour is the guard: TurboQuant retires the
already-symbolic tensors NCT and SPINE only, and WILL refuse any source record
whose id begins with ``PEER:`` or ``PCT:`` (raising / reporting TQ-002
``live-tensor-forbidden``). PEER and PCT are the live "Conscious Cache" and are
never a TurboQuant source.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Guard constants (port of turboquant.guard.ts)
# ---------------------------------------------------------------------------

TargetTensor = Literal["NCT", "SPINE"]

TURBOQUANT_ALLOWED_TARGET_TENSORS: tuple[str, ...] = ("NCT", "SPINE")

# The non-negotiable guard: PEER/PCT are live tensors and may never be a source.
TURBOQUANT_FORBIDDEN_SOURCE_PREFIXES: tuple[str, ...] = ("PEER:", "PCT:")

TURBOQUANT_REQUIRED_RECIPE_PRESERVES: tuple[str, ...] = (
    "relationships",
    "lineage",
    "structure",
    "reference-integrity",
)

TURBOQUANT_REQUIRED_RECIPE_FORBIDS: tuple[str, ...] = (
    "meaning-storage",
    "peer-compression",
    "pct-compression",
    "exact-replay",
)


class TurboQuantGuardError(Exception):
    """Raised when a guarded operation is asked to proceed on invalid input.

    The message carries the TQ-* shortfall codes so a caller (or an auditor
    reading a stack trace) can see exactly which guard tripped.
    """


# ---------------------------------------------------------------------------
# Types (port of turboquant.types.ts / steward.ledger.types.ts)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TurboQuantRecipe:
    """A retirement recipe. Mirrors ``TurboQuantRecipe`` in turboquant.types.ts."""

    id: str
    version: str
    target_tensor: str
    quantization_mode: str  # contextual-summarization | affective-condensation | graph-reduction
    source_encoding: str  # feature-vector | graph-sketch | hybrid
    compression_profile: str
    preserves: list[str]
    forbids: list[str]
    algorithm: str = "turboquant"


@dataclass(frozen=True)
class TurboQuantSourceEnvelope:
    """Bounded description of the source records being retired."""

    id: str
    session_id: str
    source_tensor: str
    source_record_ids: list[str]
    timestamp_range: dict[str, str]
    lineage: list[str]
    lattice_ref_ids: list[str]
    payload_descriptor: dict[str, Any]
    source_snapshot: str | None = None
    snapshot_anchor_ids: list[str] | None = None
    steward_ledger_ref_ids: list[str] | None = None


@dataclass(frozen=True)
class TurboQuantCandidate:
    """A validated candidate ready to be quantized."""

    envelope: TurboQuantSourceEnvelope
    feature_payload: dict[str, Any]
    lattice_ref_ids: list[str]
    validation_checks: list[str]


@dataclass(frozen=True)
class TurboQuantBackendResult:
    """Return shape of a quantization backend."""

    digest: str
    compressed_bytes: int
    dimensions: int
    payload: dict[str, Any]


@dataclass(frozen=True)
class TurboQuantArtifact:
    """The append-only, reconstructive-only retirement artifact."""

    id: str
    session_id: str
    target_tensor: str
    created_at: str
    source_envelope_id: str
    source_record_ids: list[str]
    lineage: list[str]
    lattice_ref_ids: list[str]
    steward_ledger_ref_ids: list[str]
    recipe: TurboQuantRecipe
    quantized_payload: dict[str, Any]
    snapshot_anchor_ids: list[str] | None = None
    reconstruction_hints: dict[str, Any] | None = None
    # These three are structurally fixed True in the TS contract. We default
    # them True but keep them assignable so validate_artifact can catch a
    # malformed artifact that claims exact replay (TQ-006 / TQ-007).
    preserved_reference_integrity: bool = True
    reconstructive_only: bool = True
    exact_replay_forbidden: bool = True


@dataclass(frozen=True)
class StewardLedgerTurboQuantEntry:
    """Steward ledger entry recording a turboquant-transform (TQ-005 subject)."""

    id: str
    timestamp: str
    source_references: list[str]
    surfaced_output_or_null: str | None
    lineage_references: list[str]
    target_tensor: str
    artifact_id: str
    recipe_id: str
    lattice_ref_ids: list[str]
    action_or_observation_type: str = "turboquant-transform"
    notes: list[str] | None = None


@dataclass(frozen=True)
class ReconstructedContinuityView:
    """Approximate rehydration output. Never an exact restore of the source."""

    artifact_id: str
    source_record_ids: list[str]
    derived_view: dict[str, Any]
    notes: list[str]
    approximate_only: bool = True


@dataclass(frozen=True)
class ValidationResult:
    """Mirror of TS ``TurboQuantValidationResult``."""

    ok: bool
    failures: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RunTurboQuantRetirementResult:
    """Bundle returned by :func:`run_turboquant_retirement`."""

    artifact: TurboQuantArtifact
    ledger_entry: StewardLedgerTurboQuantEntry
    notes: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_turboquant_target_tensor(value: str) -> bool:
    """Port of ``isTurboQuantTargetTensor``."""

    return value in TURBOQUANT_ALLOWED_TARGET_TENSORS


def _has_forbidden_source(record_ids: list[str]) -> bool:
    return any(
        rid.startswith(prefix)
        for rid in record_ids
        for prefix in TURBOQUANT_FORBIDDEN_SOURCE_PREFIXES
    )


def _collect_unique(values: list[list[str]]) -> list[str]:
    seen: dict[str, None] = {}
    for group in values:
        for item in group:
            seen.setdefault(item, None)
    return list(seen.keys())


# ---------------------------------------------------------------------------
# Guard / validation (port of turboquant.guard.ts)
# ---------------------------------------------------------------------------


def validate_recipe(recipe: TurboQuantRecipe) -> ValidationResult:
    """Port of ``validateTurboQuantRecipe``.

    TQ-001 illegal-target; TQ-004 missing-preserve/missing-forbid.
    """

    failures: list[str] = []

    if not is_turboquant_target_tensor(recipe.target_tensor):
        failures.append("TQ-001 illegal-target")

    for requirement in TURBOQUANT_REQUIRED_RECIPE_PRESERVES:
        if requirement not in recipe.preserves:
            failures.append(f"TQ-004 missing-preserve:{requirement}")

    for forbidden in TURBOQUANT_REQUIRED_RECIPE_FORBIDS:
        if forbidden not in recipe.forbids:
            failures.append(f"TQ-004 missing-forbid:{forbidden}")

    return ValidationResult(ok=len(failures) == 0, failures=failures)


def validate_source_envelope(envelope: TurboQuantSourceEnvelope) -> ValidationResult:
    """Port of ``validateTurboQuantSourceEnvelope``.

    TQ-001 illegal-target; TQ-004 missing source lineage / lineage;
    TQ-003 missing-lattice-refs; TQ-002 live-tensor-forbidden (PEER:/PCT:).
    """

    failures: list[str] = []

    if not is_turboquant_target_tensor(envelope.source_tensor):
        failures.append("TQ-001 illegal-target")

    if len(envelope.source_record_ids) == 0:
        failures.append("TQ-004 missing-source-lineage")

    if len(envelope.lineage) == 0:
        failures.append("TQ-004 missing-lineage")

    if len(envelope.lattice_ref_ids) == 0:
        failures.append("TQ-003 missing-lattice-refs")

    if _has_forbidden_source(envelope.source_record_ids):
        failures.append("TQ-002 live-tensor-forbidden")

    return ValidationResult(ok=len(failures) == 0, failures=failures)


def validate_artifact(artifact: TurboQuantArtifact) -> ValidationResult:
    """Port of ``validateTurboQuantArtifact``.

    Rolls up recipe failures, then TQ-001/003/004/005/002/006/007 and the
    recipe<->artifact target mismatch check.
    """

    failures: list[str] = []
    failures.extend(validate_recipe(artifact.recipe).failures)

    if not is_turboquant_target_tensor(artifact.target_tensor):
        failures.append("TQ-001 illegal-target")

    if len(artifact.source_record_ids) == 0 or len(artifact.lineage) == 0:
        failures.append("TQ-004 missing-source-lineage")

    if len(artifact.lattice_ref_ids) == 0:
        failures.append("TQ-003 missing-lattice-refs")

    if len(artifact.steward_ledger_ref_ids) == 0:
        failures.append("TQ-005 steward-log-required")

    if _has_forbidden_source(artifact.source_record_ids):
        failures.append("TQ-002 live-tensor-forbidden")

    if artifact.reconstructive_only is not True or artifact.exact_replay_forbidden is not True:
        failures.append("TQ-006 replay-claim-forbidden")

    if artifact.preserved_reference_integrity is not True:
        failures.append("TQ-007 untraceable-artifact")

    if artifact.recipe.target_tensor != artifact.target_tensor:
        failures.append("TQ-001 recipe-target-mismatch")

    return ValidationResult(ok=len(failures) == 0, failures=failures)


def validate_reconstruction_input(
    artifact: TurboQuantArtifact, lattice_ref_ids: list[str]
) -> ValidationResult:
    """Port of ``validateTurboQuantReconstructionInput``."""

    failures: list[str] = []
    failures.extend(validate_artifact(artifact).failures)

    if len(lattice_ref_ids) == 0:
        failures.append("TQ-003 missing-lattice-refs")

    required_refs = (artifact.reconstruction_hints or {}).get("required_lattice_refs", [])
    for ref in required_refs:
        if ref not in lattice_ref_ids:
            failures.append(f"TQ-003 missing-required-lattice-ref:{ref}")

    return ValidationResult(ok=len(failures) == 0, failures=failures)


# ---------------------------------------------------------------------------
# Candidate preparation (port of turboquant.candidate.ts)
# ---------------------------------------------------------------------------


def _build_context_feature_payload(records: list[dict[str, Any]], notes: list[str] | None) -> dict[str, Any]:
    return {
        "kind": "context",
        "summaries": [r.get("distilled_summary") for r in records],
        "essence_memories": [r["essence_memory"] for r in records if isinstance(r.get("essence_memory"), str)],
        "pivots": _collect_unique([list(r.get("pivots") or []) for r in records]),
        "descendant_refs": _collect_unique([list(r.get("descendant_of") or []) for r in records]),
        "diff_refs": _collect_unique([list(r.get("diff_from") or []) for r in records]),
        "notes": notes or [],
    }


def _build_pattern_feature_payload(records: list[dict[str, Any]], notes: list[str] | None) -> dict[str, Any]:
    return {
        "kind": "pattern",
        "patterns": [r.get("pattern") for r in records],
        "invariant_count": sum(1 for r in records if r.get("invariant") is True),
        "relationships": _collect_unique([list(r.get("relationships") or []) for r in records]),
        "narrative_continuity_refs": [
            r["narrative_continuity_ref"] for r in records if isinstance(r.get("narrative_continuity_ref"), str)
        ],
        "notes": notes or [],
    }


def prepare_candidate(
    *,
    session_id: str,
    target_tensor: str,
    source_records: list[dict[str, Any]],
    lattice_ref_ids_by_source: dict[str, list[str]],
    source_snapshot: str | None = None,
    snapshot_anchor_ids: list[str] | None = None,
    steward_ledger_ref_ids: list[str] | None = None,
    notes: list[str] | None = None,
) -> TurboQuantCandidate:
    """Port of ``prepareTurboQuantCandidate``.

    ``source_records`` are the resolved NCT/SPINE records (dicts) that Stage-1
    previously produced. Each will carry at least ``id``, ``timestamp`` and
    ``lineage``. This is a faithful analogue of the TS resolver, but takes the
    already-resolved records directly rather than a full ``DataQuadState`` — the
    draft is deliberately runtime-agnostic.

    Raises :class:`TurboQuantGuardError` when the guard trips, matching the TS
    ``assertCandidateInputs`` / ``assertEnvelopeValid`` throw behaviour.
    """

    source_record_ids = [str(r["id"]) for r in source_records]
    lattice_ref_ids = _collect_unique(
        [list(lattice_ref_ids_by_source.get(rid, [])) for rid in source_record_ids]
    )

    # assertCandidateInputs — including the direct PEER:/PCT: prefix guard.
    pre_failures: list[str] = []
    if len(source_records) == 0:
        pre_failures.append("TQ-004 missing-source-lineage")
    if len(lattice_ref_ids) == 0:
        pre_failures.append("TQ-003 missing-lattice-refs")
    if _has_forbidden_source(source_record_ids):
        pre_failures.append("TQ-002 live-tensor-forbidden")
    if pre_failures:
        raise TurboQuantGuardError(
            "Invalid TurboQuant candidate input: " + ", ".join(pre_failures)
        )

    timestamps = sorted(str(r["timestamp"]) for r in source_records)
    latest_timestamp = timestamps[-1] if timestamps else _now_iso()
    lineage = _collect_unique([list(r.get("lineage") or []) for r in source_records])
    payload_kind = "context" if target_tensor == "NCT" else "pattern"

    envelope = TurboQuantSourceEnvelope(
        id=f"TQENV:{target_tensor}:{session_id}:{latest_timestamp}",
        session_id=session_id,
        source_tensor=target_tensor,
        source_record_ids=source_record_ids,
        source_snapshot=source_snapshot,
        timestamp_range={"start": timestamps[0] if timestamps else latest_timestamp, "end": latest_timestamp},
        lineage=lineage,
        lattice_ref_ids=lattice_ref_ids,
        snapshot_anchor_ids=snapshot_anchor_ids,
        steward_ledger_ref_ids=steward_ledger_ref_ids,
        payload_descriptor={"kind": payload_kind, "chunk_count": len(source_records), "notes": notes},
    )

    envelope_validation = validate_source_envelope(envelope)
    if not envelope_validation.ok:
        raise TurboQuantGuardError(
            "Invalid TurboQuant source envelope: " + ", ".join(envelope_validation.failures)
        )

    feature_payload = (
        _build_context_feature_payload(source_records, notes)
        if target_tensor == "NCT"
        else _build_pattern_feature_payload(source_records, notes)
    )

    return TurboQuantCandidate(
        envelope=envelope,
        feature_payload=feature_payload,
        lattice_ref_ids=lattice_ref_ids,
        validation_checks=[
            "target-tensor-validated",
            "source-records-resolved",
            "source-envelope-validated",
        ],
    )


# ---------------------------------------------------------------------------
# Deterministic backend (port of DeterministicTurboQuantBackend / engine.ts)
# ---------------------------------------------------------------------------


def _stable_stringify(value: Any) -> str:
    """Port of the TS ``stableStringify`` (sorted keys, JSON scalars)."""

    if isinstance(value, list):
        return "[" + ",".join(_stable_stringify(item) for item in value) + "]"
    if isinstance(value, dict):
        entries = sorted(value.items(), key=lambda kv: kv[0])
        return "{" + ",".join(f'"{k}":{_stable_stringify(v)}' for k, v in entries) + "}"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value) if isinstance(value, float) else str(value)
    # string
    import json

    return json.dumps(value)


def _iter_utf16_code_units(text: str):
    """Yield UTF-16 code units for ``text`` to match TS ``String.charCodeAt``.

    JS strings are UTF-16, so ``charCodeAt`` returns surrogate halves for non-BMP
    characters. Python iterates Unicode code points, so we expand supplementary-plane
    code points into surrogate pairs — keeping the digest byte-for-byte identical to the
    TS backend (turboquant.engine.ts) even for emoji / non-BMP text (audit finding 2,
    Codex 2026-07-25). BMP characters are unchanged, so the pinned ASCII digests hold.
    """

    for char in text:
        code_point = ord(char)
        if code_point > 0xFFFF:
            code_point -= 0x10000
            yield 0xD800 + (code_point >> 10)
            yield 0xDC00 + (code_point & 0x3FF)
        else:
            yield code_point


def _compute_deterministic_digest(text: str) -> str:
    """Port of the TS FNV-1a digest using 32-bit ``Math.imul`` semantics.

    Iterates UTF-16 code units (not Unicode code points) so the digest matches the TS
    ``input.charCodeAt(index)`` backend exactly, including for non-BMP characters.
    """

    hash_value = 2166136261
    for code_unit in _iter_utf16_code_units(text):
        hash_value ^= code_unit & 0xFFFFFFFF
        # Math.imul(hash, 16777619): 32-bit multiply, keep low 32 bits.
        hash_value = (hash_value * 16777619) & 0xFFFFFFFF
    return f"tq-{hash_value & 0xFFFFFFFF:08x}"


def _estimate_compressed_bytes(serialized: str) -> int:
    import math

    return max(64, math.ceil(len(serialized) * 0.6))


def _infer_dimensions(feature_payload: dict[str, Any]) -> int:
    for value in feature_payload.values():
        if isinstance(value, list):
            return len(value)
    return len(feature_payload)


def deterministic_backend(candidate: TurboQuantCandidate, recipe: TurboQuantRecipe) -> TurboQuantBackendResult:
    """Port of ``DeterministicTurboQuantBackend.quantize``.

    This is the ``placeholderImplementation: true`` backend from the TS engine.
    It is deterministic and dependency-free, which is what a design draft and
    its audit want. A future implementation may swap in a feature-space backend
    (the TS default) without changing the guard or artifact contract.
    """

    serialized = _stable_stringify(
        {
            "envelope": _envelope_as_dict(candidate.envelope),
            "featurePayload": candidate.feature_payload,
            "recipe": _recipe_as_dict(recipe),
        }
    )
    digest = _compute_deterministic_digest(serialized)
    return TurboQuantBackendResult(
        digest=digest,
        compressed_bytes=_estimate_compressed_bytes(serialized),
        dimensions=_infer_dimensions(candidate.feature_payload),
        payload={
            "placeholder_implementation": True,
            "digest": digest,
            "source_encoding": recipe.source_encoding,
            "compression_profile": recipe.compression_profile,
            "validation_checks": candidate.validation_checks,
            "feature_summary": candidate.feature_payload,
        },
    )


def _recipe_as_dict(recipe: TurboQuantRecipe) -> dict[str, Any]:
    return {
        "id": recipe.id,
        "version": recipe.version,
        "algorithm": recipe.algorithm,
        "targetTensor": recipe.target_tensor,
        "quantizationMode": recipe.quantization_mode,
        "sourceEncoding": recipe.source_encoding,
        "compressionProfile": recipe.compression_profile,
        "preserves": recipe.preserves,
        "forbids": recipe.forbids,
    }


def _envelope_as_dict(envelope: TurboQuantSourceEnvelope) -> dict[str, Any]:
    return {
        "id": envelope.id,
        "sessionId": envelope.session_id,
        "sourceTensor": envelope.source_tensor,
        "sourceRecordIds": envelope.source_record_ids,
        "timestampRange": envelope.timestamp_range,
        "lineage": envelope.lineage,
        "latticeRefIds": envelope.lattice_ref_ids,
        "payloadDescriptor": envelope.payload_descriptor,
    }


# ---------------------------------------------------------------------------
# Engine apply (port of applyTurboQuant / turboquant.engine.ts)
# ---------------------------------------------------------------------------


def _build_artifact_id(session_id: str, target_tensor: str, digest: str, timestamp: str) -> str:
    return f"TQART:{target_tensor}:{session_id}:{timestamp}:{digest}"


def _build_steward_ledger_entry_id(session_id: str, timestamp: str) -> str:
    return f"STEWARD:{session_id}:{timestamp}:turboquant-transform"


def apply_turboquant(
    *,
    candidate: TurboQuantCandidate,
    recipe: TurboQuantRecipe,
    timestamp: str | None = None,
    steward_ledger_ref_ids: list[str] | None = None,
    snapshot_anchor_ids: list[str] | None = None,
    backend: Any = None,
) -> TurboQuantArtifact:
    """Port of ``applyTurboQuant``.

    Validates the recipe, enforces recipe<->candidate tensor match, quantizes,
    assembles a reconstructive-only artifact, then re-validates the artifact.
    Raises :class:`TurboQuantGuardError` on any guard shortfall.
    """

    recipe_validation = validate_recipe(recipe)
    if not recipe_validation.ok:
        raise TurboQuantGuardError("Invalid TurboQuant recipe: " + ", ".join(recipe_validation.failures))

    if recipe.target_tensor != candidate.envelope.source_tensor:
        raise TurboQuantGuardError("TurboQuant recipe target will match candidate source tensor.")

    # Guard BEFORE any backend sees the candidate (audit finding 1, Codex 2026-07-25).
    # run_turboquant_retirement reaches this via prepare_candidate, but apply_turboquant
    # is a public lower-level entry: a PEER:/PCT: source id will be refused (TQ-002),
    # and the envelope re-validated (TQ-001/003/004), before backend invocation — never
    # let a custom backend observe or process a forbidden source id.
    envelope_validation = validate_source_envelope(candidate.envelope)
    if not envelope_validation.ok:
        raise TurboQuantGuardError(
            "Invalid TurboQuant candidate envelope: " + ", ".join(envelope_validation.failures)
        )

    ts = timestamp or _now_iso()
    run_backend = backend or deterministic_backend
    backend_result = run_backend(candidate, recipe)
    digest = backend_result.digest
    artifact_id = _build_artifact_id(candidate.envelope.session_id, candidate.envelope.source_tensor, digest, ts)
    planned_ledger_ref_ids = steward_ledger_ref_ids or [
        _build_steward_ledger_entry_id(candidate.envelope.session_id, ts)
    ]

    artifact = TurboQuantArtifact(
        id=artifact_id,
        session_id=candidate.envelope.session_id,
        target_tensor=recipe.target_tensor,
        created_at=ts,
        source_envelope_id=candidate.envelope.id,
        source_record_ids=candidate.envelope.source_record_ids,
        lineage=[*candidate.envelope.lineage, artifact_id],
        lattice_ref_ids=candidate.lattice_ref_ids,
        steward_ledger_ref_ids=planned_ledger_ref_ids,
        snapshot_anchor_ids=snapshot_anchor_ids or candidate.envelope.snapshot_anchor_ids,
        recipe=recipe,
        preserved_reference_integrity=True,
        reconstructive_only=True,
        exact_replay_forbidden=True,
        quantized_payload={
            "encoding": "turboquant",
            "dimensions": backend_result.dimensions,
            "chunk_count": candidate.envelope.payload_descriptor.get("chunk_count", 1),
            "compressed_bytes": backend_result.compressed_bytes,
            "reference_checksum": digest,
            "payload": backend_result.payload,
        },
        reconstruction_hints={
            "required_lattice_refs": candidate.lattice_ref_ids,
            "approximate_only": True,
            "notes": [
                "TurboQuant artifact generated from bounded feature payload.",
                "Reconstruction remains approximate and will rereference lattice structure.",
            ],
        },
    )

    artifact_validation = validate_artifact(artifact)
    if not artifact_validation.ok:
        raise TurboQuantGuardError("Invalid TurboQuant artifact: " + ", ".join(artifact_validation.failures))

    return artifact


def record_turboquant_ledger_entry(
    *,
    artifact: TurboQuantArtifact,
    source_references: list[str] | None = None,
    lineage_references: list[str] | None = None,
    surfaced_output_or_null: str | None = None,
    notes: list[str] | None = None,
    timestamp: str | None = None,
) -> StewardLedgerTurboQuantEntry:
    """Port of ``recordTurboQuantLedgerEntry``.

    Re-validates the artifact (TQ-005 subject) before minting the ledger entry.
    """

    artifact_validation = validate_artifact(artifact)
    if not artifact_validation.ok:
        raise TurboQuantGuardError("Invalid TurboQuant artifact: " + ", ".join(artifact_validation.failures))

    ts = timestamp or artifact.created_at
    return StewardLedgerTurboQuantEntry(
        id=_build_steward_ledger_entry_id(artifact.session_id, ts),
        timestamp=ts,
        source_references=source_references or artifact.source_record_ids,
        surfaced_output_or_null=surfaced_output_or_null,
        lineage_references=lineage_references or artifact.lineage,
        target_tensor=artifact.target_tensor,
        artifact_id=artifact.id,
        recipe_id=artifact.recipe.id,
        lattice_ref_ids=artifact.lattice_ref_ids,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Orchestration (port of runTurboQuantRetirement / turboquant.pipeline.ts)
# ---------------------------------------------------------------------------


def run_turboquant_retirement(
    *,
    session_id: str,
    target_tensor: str,
    recipe: TurboQuantRecipe,
    source_records: list[dict[str, Any]],
    lattice_ref_ids_by_source: dict[str, list[str]],
    source_snapshot: str | None = None,
    timestamp: str | None = None,
    snapshot_anchor_ids: list[str] | None = None,
    steward_ledger_ref_ids: list[str] | None = None,
    notes: list[str] | None = None,
    backend: Any = None,
) -> RunTurboQuantRetirementResult:
    """Port of ``runTurboQuantRetirement``.

    Runs the full Stage-2 retirement over already-symbolic NCT/SPINE source
    records: prepare candidate -> apply -> mint steward ledger entry. Produces a
    quantized, reconstructive-only artifact plus its required steward ledger
    entry. The guard is enforced at every step; a PEER:/PCT: source can never
    reach the artifact.

    DRAFT: returns the artifact + ledger entry in memory. It does NOT append to
    any live DataQuad, does NOT prune any source tensor, and does NOT write to
    disk. Archival/prune of the retired source records is Stage-1's
    responsibility and a separately gated live operation.
    """

    candidate = prepare_candidate(
        session_id=session_id,
        target_tensor=target_tensor,
        source_records=source_records,
        lattice_ref_ids_by_source=lattice_ref_ids_by_source,
        source_snapshot=source_snapshot,
        snapshot_anchor_ids=snapshot_anchor_ids,
        steward_ledger_ref_ids=steward_ledger_ref_ids,
        notes=notes,
    )
    artifact = apply_turboquant(
        candidate=candidate,
        recipe=recipe,
        timestamp=timestamp,
        steward_ledger_ref_ids=steward_ledger_ref_ids,
        snapshot_anchor_ids=snapshot_anchor_ids,
        backend=backend,
    )
    ledger_entry = record_turboquant_ledger_entry(artifact=artifact, notes=notes)

    return RunTurboQuantRetirementResult(
        artifact=artifact,
        ledger_entry=ledger_entry,
        notes=[
            "TurboQuant candidate transformed into append-only artifact.",
            "Artifact includes planned steward ledger references and reconstructive-only guardrails.",
            "TurboQuant retirement orchestration completed (DRAFT: no live append / no prune).",
        ],
    )


# ---------------------------------------------------------------------------
# Approximate rehydration (port of ReconstructedContinuityView path)
# ---------------------------------------------------------------------------


def reconstruct(
    *,
    artifact: TurboQuantArtifact,
    lattice_ref_ids: list[str],
    snapshot_anchor_ids: list[str] | None = None,
) -> ReconstructedContinuityView:
    """Approximate rehydration of a retired continuity artifact.

    This is APPROXIMATE ONLY. The exact way back is the archived source records
    (Stage-1's hash-proof archive), never this derived view. Mirrors the TS
    ``ReconstructQuantizedContinuityInput`` -> ``ReconstructedContinuityView``
    intent and validates via ``validate_reconstruction_input`` first.
    """

    validation = validate_reconstruction_input(artifact, lattice_ref_ids)
    if not validation.ok:
        raise TurboQuantGuardError(
            "Invalid TurboQuant reconstruction input: " + ", ".join(validation.failures)
        )

    payload = artifact.quantized_payload.get("payload", {})
    derived_view: dict[str, Any] = {
        "target_tensor": artifact.target_tensor,
        "feature_summary": payload.get("feature_summary"),
        "reference_checksum": artifact.quantized_payload.get("reference_checksum"),
        "lattice_ref_ids": artifact.lattice_ref_ids,
        "snapshot_anchor_ids": snapshot_anchor_ids or artifact.snapshot_anchor_ids or [],
    }

    return ReconstructedContinuityView(
        artifact_id=artifact.id,
        source_record_ids=artifact.source_record_ids,
        derived_view=derived_view,
        notes=[
            "Approximate reconstruction from bounded TurboQuant artifact.",
            "Exact restore is via the Stage-1 archive, not this view.",
        ],
        approximate_only=True,
    )
