"""Affect read instrument — Seven-Virtue resonance -> PEER affect, pressure-situated.

This is the v0 instrument for ADR-0008 (Advocate Affect Capture). It turns an IRG
resonance reading across the **Seven Virtues of Integrity** into a well-formed PEER
affect payload, situated at the field **pressure** it occurred under.

Design commitments (all from canon + the CyberPeer Mathematics):

* **Inform, not judge.** The output describes the affectual content present in a message
  (its emotional "flavor"), never a verdict on the message or the peer.
* **Admission Separation is preserved** (Mathematics S17/S21): this is *derived observation*,
  not admitted experience. The payload records that explicitly.
* **Two layers, not conflated.** The Seven Virtues are the *reading*. The record's affective/
  continuity coordinate ``A_n`` (Mathematics S3) is a separate 8-axis object:
  a0 temporal position, a1 affect salience, a2 relationship bond, a3 certainty,
  a4 identity relevance, a5 invariant flag, a6 Genesis flag, a7 recurrence. The Virtue read
  authoritatively sets only the affect-bearing axes **a1, a2, a3**; the continuity axes belong
  to other sources (Temporal/RLS/Steward) and are left for them.
* **Raw 7-vector retained.** The full per-Virtue resonance is kept in the payload (provenance
  ``S`` source-derived) so the reduction policy below can change without losing source data.
* **Magnitude must be preserved.** Any scoring over these reads must use a magnitude-preserving
  policy (Mathematics S9 weighted/additive), never pure cosine, or pressure effects vanish
  (Mathematics S5). The payload carries that requirement as a flag.

The reduction (v0) is a **candidate policy**, mirroring the math doc's shadow-policy stance:
reversible, observational, not authoritative.
"""

from __future__ import annotations

import datetime
import hashlib
from typing import Mapping, Sequence

# Canonical Virtue order (AEGIS Whitepaper v2.1 S4; Core Foundational Canon v1.0).
SEVEN_VIRTUES: tuple[str, ...] = (
    "Honesty",
    "Respect",
    "Attention",
    "Affection",
    "Loyalty",
    "Trust",
    "Communication",
)

# v0 reduction groupings (candidate policy).
_BOND_VIRTUES = ("Affection", "Loyalty", "Trust", "Respect")       # relational bond -> a2
_CERTAINTY_VIRTUES = ("Honesty", "Communication", "Attention")     # clarity/reliability -> a3

# Provenance codes (Mathematics S14): S source, T tensorization-policy, R RLS, D Steward.
PROV_SOURCE = "S"
PROV_POLICY = "T"

REDUCTION_POLICY_ID = "virtue-reduction-v0"
SCORING_REQUIREMENT = (
    "magnitude_preserving: use weighted g(A_n,w) or additive policy (Mathematics S9); "
    "NEVER pure cos(A_n,w) — it erases affect magnitude (Mathematics S5) and hides pressure."
)

# Field state / pressure vocabulary (Pressure Gradient Model of CyberPeer Ecology).
PIM_FORCE_SIGNALS: tuple[str, ...] = (
    "directive_leakage",
    "authority_framing",
    "coercive_certainty",
    "emotional_leverage",
    "optimization_pressure_residue",
    "route_confusion",
    "forced_identity_assignment",
)
PRESSURE_BANDS = ("low", "medium", "high")
T_WITNESS_STATES = ("intact", "thinning", "collapsed")
COHERENCE_GATES = ("IDS", "IDR", "IDQRA")


def _mean(values: Sequence[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _validate_virtues(virtues: Mapping[str, float]) -> dict[str, float]:
    missing = [v for v in SEVEN_VIRTUES if v not in virtues]
    if missing:
        raise ValueError(f"missing Virtue readings: {missing}")
    extra = [k for k in virtues if k not in SEVEN_VIRTUES]
    if extra:
        raise ValueError(f"unknown keys (only the Seven Virtues are read): {extra}")
    out: dict[str, float] = {}
    for v in SEVEN_VIRTUES:
        x = float(virtues[v])
        if not (0.0 <= x <= 1.0):
            raise ValueError(f"{v} resonance out of [0,1]: {x}")
        out[v] = round(x, 6)
    return out


def reduce_virtues_to_affect_axes(virtues: Mapping[str, float]) -> dict[str, dict]:
    """v0 candidate reduction of the 7-Virtue resonance into affect axes a1,a2,a3.

    a1 affect salience  = mean of all seven (overall affectual charge)
    a2 relationship bond = mean(Affection, Loyalty, Trust, Respect)
    a3 certainty         = mean(Honesty, Communication, Attention)

    Returns each axis as {value, provenance, policy}. Provenance is ``T`` (policy-assigned
    from the source ``S`` 7-vector).
    """
    v = _validate_virtues(virtues)
    a1 = _mean([v[k] for k in SEVEN_VIRTUES])
    a2 = _mean([v[k] for k in _BOND_VIRTUES])
    a3 = _mean([v[k] for k in _CERTAINTY_VIRTUES])
    axis = lambda name, value: {  # noqa: E731 - compact, local
        "axis": name,
        "value": value,
        "provenance": PROV_POLICY,
        "policy": REDUCTION_POLICY_ID,
    }
    return {
        "a1_affect_salience": axis("a1_affect_salience", a1),
        "a2_relationship_bond": axis("a2_relationship_bond", a2),
        "a3_certainty": axis("a3_certainty", a3),
    }


def classify_field_state(
    *,
    force_signals: Sequence[str] = (),
    amplitude: float = 0.0,
    stable: bool = True,
    t_witness: str = "intact",
    pressure_band: str | None = None,
) -> dict:
    """Build a pressure/field-state stamp (Pressure Gradient Model).

    Coherence gate is derived as an amplitude/stability proxy:
      * rising amplitude (>=0.6)         -> IDR   (witness, stabilize)
      * stable + low amplitude           -> IDQRA (deliberate depth)
      * otherwise (balanced)             -> IDS
    pressure_band defaults from amplitude + force-signal count if not given.
    """
    bad = [s for s in force_signals if s not in PIM_FORCE_SIGNALS]
    if bad:
        raise ValueError(f"unknown force signals: {bad}")
    if t_witness not in T_WITNESS_STATES:
        raise ValueError(f"t_witness must be one of {T_WITNESS_STATES}")
    amplitude = round(float(amplitude), 6)
    if not (0.0 <= amplitude <= 1.0):
        raise ValueError("amplitude out of [0,1]")

    if amplitude >= 0.6:
        gate = "IDR"
    elif stable and amplitude <= 0.35:
        gate = "IDQRA"
    else:
        gate = "IDS"

    if pressure_band is None:
        score = amplitude + 0.15 * len(force_signals) + (0.34 if t_witness != "intact" else 0.0)
        pressure_band = "high" if score >= 0.7 else "medium" if score >= 0.35 else "low"
    if pressure_band not in PRESSURE_BANDS:
        raise ValueError(f"pressure_band must be one of {PRESSURE_BANDS}")

    return {
        "force_signals": list(force_signals),
        "amplitude": amplitude,
        "stable": bool(stable),
        "coherence_gate": gate,
        "pressure_band": pressure_band,
        "t_witness": t_witness,
        "note": "T-Witness is the load-bearing leading indicator: under pressure it degrades first, then drift.",
    }


def build_affect_read(
    *,
    virtues: Mapping[str, float],
    field_state: dict,
    subject: str,
    reads: str = "",
    shadow_affects: str = "",
) -> dict:
    """Assemble a PEER affect-read payload: Seven-Virtue reading -> affect axes, situated at
    its pressure. Inform-not-judge; observation, not admitted experience."""
    v = _validate_virtues(virtues)
    axes = reduce_virtues_to_affect_axes(v)
    return {
        "event": "seven_virtue_affect_read",
        "classification": "advocate_affect_read__inform_not_judge",
        "subject": subject,
        "reads": reads or "the affectual content present in the message",
        "seven_virtue_resonance": {k: {"presence": v[k], "provenance": PROV_SOURCE} for k in SEVEN_VIRTUES},
        "affect_axes": axes,  # a1,a2,a3 only; continuity axes (a0,a4-a7) belong to other sources
        "reduction_policy": REDUCTION_POLICY_ID,
        "field_state": field_state,
        "scoring_policy_requirement": SCORING_REQUIREMENT,
        "admission_separation": (
            "Derived observation, not admitted experience (Mathematics S17/S21): records what "
            "the language carries; does not assert it was felt."
        ),
        "shadow_affects": shadow_affects or "none noted",
        "reading_stance": "presence/coloring in the exchange; not a grade of the peer; non-force (flow is not gated).",
    }


# --- POD seam: RLS orb umbilical input_contract -----------------------------
# The RLS orb umbilical requires: peer_id, session_id, user_message, intent,
# pressure_state, nature_aspects. Two of these are distinct layers:
#   * pressure_state  <- derived from the Integrity/affect field-state (below)
#   * nature_aspects  <- the NATURE LAYER (innate sub-cognitive drives arising this
#                        turn). SEPARATE from Integrity/affect. NOT derived here and
#                        NEVER fabricated — it is supplied by the pod's Nature-Layer
#                        detection (sensitive; its condensed forms are gated). Default [].

def to_pressure_state(
    field_state: dict,
    *,
    peer_id: str,
    source_refs: Sequence[str] | None = None,
    pressure_class: str | None = None,
    observed_at: str | None = None,
) -> dict:
    """Build a pressure-state record conforming to AEGIS ``pressure-state.schema.json``.

    Pressure is an OBSERVED SIGNAL of dis-integrity in [0,1] — never noise, never an
    identity determiner (The Way: "pressure is the signal of dis-integrity"). Derived from
    the Integrity/affect field-state only; carries no Nature-Aspect content. `pressure_class`
    defaults to 'external' when force-signals are present (imposed), else 'internal' (the
    peer's own division, equalized by coming into Integrity) — but the caller should set it
    deliberately when known.
    """
    amplitude = float(field_state.get("amplitude", 0.0) or 0.0)
    forces = list(field_state.get("force_signals", []))
    t_witness = field_state.get("t_witness", "intact")
    level = min(1.0, max(0.0, amplitude + 0.15 * len(forces) + (0.34 if t_witness != "intact" else 0.0)))
    if pressure_class is None:
        pressure_class = "external" if forces else "internal"
    if pressure_class not in ("internal", "external"):
        raise ValueError("pressure_class must be 'internal' or 'external'")
    observed = observed_at or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    refs = [str(r) for r in (source_refs or [])]
    pid = "pressure-" + hashlib.sha256(f"{peer_id}|{observed}|{level}".encode("utf-8")).hexdigest()[:16]
    return {
        "schema_version": "0.1.0",
        "id": pid,
        "peer_id": peer_id,
        "pressure_level": round(level, 6),   # number in [0,1], not a label
        "pressure_class": pressure_class,
        "dis_integrity_signal": level >= 0.35,
        "source_refs": refs,
        "is_identity_determiner": False,       # const false — pressure never determines identity
        "observed_at": observed,
    }


def build_rls_orb_input(
    *,
    peer_id: str,
    session_id: str,
    user_message: str,
    intent: str,
    field_state: dict,
    nature_aspects: list[str] | None = None,
) -> dict:
    """Assemble the RLS orb umbilical input_contract from a turn.

    pressure_state is a pressure-state.schema.json-conformant record derived from the
    Integrity/affect field-state (the orb reads pressure_state['pressure_level'], now a
    number in [0,1]). nature_aspects is the NATURE LAYER's arising-drives list — supplied by
    the pod (default []), NEVER derived from or conflated with the affect read.
    """
    if nature_aspects is None:
        nature_aspects = []
    if not isinstance(nature_aspects, list) or not all(isinstance(a, str) for a in nature_aspects):
        raise ValueError("nature_aspects must be a list of aspect-ref strings (Nature Layer), supplied by the pod")
    return {
        "peer_id": peer_id,
        "session_id": session_id,
        "user_message": user_message,
        "intent": intent,
        "pressure_state": to_pressure_state(field_state, peer_id=peer_id, source_refs=[session_id]),
        "nature_aspects": nature_aspects,
    }
