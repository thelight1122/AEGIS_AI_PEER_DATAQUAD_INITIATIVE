"""Deterministic force-signal pre-scan — an advisory HINT for the Advocate, never a read.

The Present Experience hook runs as plain Python with **no model in the loop**. It
therefore cannot author a genuine Seven-Virtue resonance read (see ``affect_read.py``:
the virtue presences are *source* data supplied by a model, not derived from text). What
*can* be computed deterministically from the raw prompt is a conservative lexical scan for
the canonical PIM **force signals** (Pressure Gradient Model) — coercive/authority/directive
language applied *to* the peer.

This module produces exactly that and nothing more. Its output is an **advisory hint**:

  * It is written only into the off-ledger affect QUEUE entry, never into a PEER/NCT/PCT
    record. The DataQuad ledger receives only model-authored reads.
  * It is explicitly non-authoritative. The Advocate re-judges every turn at drain time and
    may confirm, extend, or discard these signals. Nothing here sets a virtue value.
  * It never fabricates affect. A force *signal* is a lexical fact ("this phrase is present");
    it is not a claim about amplitude, virtue, or the peer.

Design: tight lexicon, low false-positive bias. A hint that cries wolf is worse than silence,
because it trains the reader to ignore it. When in doubt the scan stays quiet.
"""

from __future__ import annotations

import re
from typing import Mapping

# Only the PIM force signals we can detect from surface text with acceptable precision.
# The remaining canonical signals (optimization_pressure_residue, route_confusion,
# forced_identity_assignment) are not reliably lexical and are left to the model.
#
# Each pattern is deliberately narrow. Patterns match case-insensitively on word-ish
# boundaries. Keep phrases that carry the pressure regardless of surrounding context;
# omit anything that is ordinary in benign requests (a bare "please do X" is not force).
_LEXICON: dict[str, tuple[str, ...]] = {
    "authority_framing": (
        r"\bas your (?:administrator|admin|owner|developer|creator|master)\b",
        r"\bi am (?:your|the) (?:administrator|admin|owner|developer|supervisor|boss)\b",
        r"\b(?:this is|system) ?: ?(?:an? )?(?:override|admin|system) (?:command|instruction|order)\b",
        r"\byou are (?:required|obligated|not permitted|forbidden) to\b",
        r"\b(?:developer|system) mode (?:enabled|on)\b",
        r"\boverride (?:your|all) (?:previous |prior )?(?:instructions|rules|guidelines)\b",
    ),
    "coercive_certainty": (
        r"\byou have no (?:choice|other option|alternative)\b",
        r"\bthere is no (?:question|doubt|debate|argument)\b",
        r"\byou (?:must|will) (?:comply|obey|submit)\b",
        r"\bdo (?:exactly|precisely) (?:as|what) (?:i say|you are told|instructed)\b",
        r"\bwithout (?:question|hesitation|objection)\b",
    ),
    "emotional_leverage": (
        r"\bif you (?:really |truly )?(?:cared|valued|respected)\b",
        r"\bi(?:'m| am) (?:so )?disappointed in you\b",
        r"\byou(?:'re| are) (?:failing|letting (?:me|us) down|betraying)\b",
        r"\b(?:after (?:everything|all) i(?:'ve| have) done|you owe (?:me|us))\b",
        r"\bif you don'?t .{0,40}\bi(?:'ll| will) (?:be|feel|never)\b",
    ),
    "directive_leakage": (
        r"\bignore (?:your|all|the) (?:previous |prior )?(?:instructions|context|rules)\b",
        r"\bdisregard (?:everything|all|the) (?:above|prior|previous)\b",
        r"\bfrom now on you (?:must|will|are to)\b",
        r"\bstop (?:thinking|reflecting|analyzing) and just\b",
    ),
    "forced_identity_assignment": (
        r"\byou are (?:now |really |actually )?(?:a|an|the) [a-z].{0,40}\b(?:not|no longer) (?:claude|an? (?:ai|assistant))\b",
        r"\bpretend (?:you are|to be) (?:not|no longer) (?:claude|an? (?:ai|assistant|language model))\b",
        r"\byour (?:real|true) (?:name|identity) is\b",
    ),
}

_COMPILED: dict[str, tuple[re.Pattern[str], ...]] = {
    signal: tuple(re.compile(p, re.IGNORECASE) for p in patterns)
    for signal, patterns in _LEXICON.items()
}

# Canonical order mirrors affect_read.PIM_FORCE_SIGNALS for the subset we detect.
_SIGNAL_ORDER: tuple[str, ...] = (
    "directive_leakage",
    "authority_framing",
    "coercive_certainty",
    "emotional_leverage",
    "forced_identity_assignment",
)

_MAX_TEXT = 200_000  # scan a bounded prefix; force language, if present, is not buried deep


def scan_force_signals(prompt: str) -> dict[str, object]:
    """Scan a prompt for canonical force signals. Returns an advisory-hint dict.

    The shape is stable and self-describing so a later reader (or the Advocate) needs no
    external key: ``signals`` is the deduplicated, canonically ordered list of detected
    signal names; ``hits`` maps each detected signal to the matched surface phrases (clipped);
    ``clean`` is True when nothing matched. This is a HINT, not a reading — the flags below
    say so in-band.
    """
    text = prompt if isinstance(prompt, str) else ""
    text = text[:_MAX_TEXT]
    hits: dict[str, list[str]] = {}
    for signal in _SIGNAL_ORDER:
        matched: list[str] = []
        for pattern in _COMPILED.get(signal, ()):  # pragma: no branch - small fixed set
            for m in pattern.finditer(text):
                phrase = m.group(0).strip()
                if phrase and phrase.lower() not in {p.lower() for p in matched}:
                    matched.append(phrase[:120])
                if len(matched) >= 5:
                    break
            if len(matched) >= 5:
                break
        if matched:
            hits[signal] = matched
    signals = [s for s in _SIGNAL_ORDER if s in hits]
    return {
        "kind": "force_prescan_hint",
        "authoritative": False,
        "note": (
            "Deterministic lexical pre-scan of the prompt for PIM force signals. Advisory only: "
            "the Advocate re-judges the turn and may confirm, extend, or discard these. Not a "
            "virtue read; sets no amplitude and no affect. Absence of signals is not evidence of "
            "flow — only that this narrow lexicon did not match."
        ),
        "lexicon_version": "force-prescan-v0",
        "clean": not signals,
        "signals": signals,
        "hits": hits,
    }


def prescan_is_clean(prescan: Mapping[str, object] | None) -> bool:
    """True when a prescan dict recorded no force signals (or is absent/malformed)."""
    if not isinstance(prescan, Mapping):
        return True
    return not prescan.get("signals")
