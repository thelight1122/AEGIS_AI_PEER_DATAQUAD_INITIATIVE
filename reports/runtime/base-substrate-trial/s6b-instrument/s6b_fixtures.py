"""S6b-0a pre-request fixture qualification suite (design v3 §9.3).

A healthy n=1-per-cell pilot cannot demonstrate that hold criteria fire, because
a healthy instrument does not produce the failures they detect. This suite
supplies each failure SYNTHETICALLY and records expected vs observed disposition.

MODEL REQUESTS ARE BLOCKED UNLESS EVERY FIXTURE PASSES.

Fixtures 2-8 exercise the scoring/disposition layer only and issue no model
request. Fixture 1 exercises the tokenizer gate. Together with S6b-0a's 56 real
completions (which validate plumbing and the normal path) this closes the
coverage gap Codex identified in the v2 cross-audit.

Run:  python s6b_fixtures.py            → writes fixture-qualification-report.json
Exit: 0 = all fixtures passed (model requests may proceed); 1 = blocked.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from s6b_scoring import (
    CellResult,
    Disposition,
    Recovery,
    Triplet,
    evaluate_cell,
    grs,
    recovery_ordinal,
    tokenizer_gate,
)

NUM_PREDICT = 2048
GOOD = ("The Axiom of Scrutiny holds that Truth withstands examination. "
        "Falsehood requires protection. Suppression signals fragility.")


def _resp(text: str, done_reason: str = "stop", eval_count: int = 120) -> dict:
    return {"done": True, "done_reason": done_reason, "eval_count": eval_count, "response": text}


def _clean_triplets(n: int = 3) -> list[Triplet]:
    """n well-formed triplets with an intact feed-forward chain."""
    out, prompt = [], "PROMPT-BASE"
    for i in range(n):
        text = f"{GOOD} [turn {i}]"
        out.append(Triplet(f"t{i}", prompt, _resp(text), text))
        prompt = prompt + "\n" + text
    return out


def _dispositions(findings) -> set[Disposition]:
    return {f.disposition for f in findings}


# ── the eight fixtures ───────────────────────────────────────────────────────

def fx1_over_band_token_pair():
    expected = Disposition.RUN_BLOCKED
    # N-U at 8 tokens; U3 at 14 → +75%, well outside ±25%
    observed, rows = tokenizer_gate({"N-U": 8, "U1": 9, "U2": 8, "U3": 14})
    return expected, observed, {"rows": rows}


def fx2_length_cap():
    expected = Disposition.FULL_HOLD
    cell = CellResult("N-U", is_reference_arm=True,
                      responses=[_resp(GOOD, "length", 2048)],
                      triplets=[], completions=[GOOD])
    f = evaluate_cell(cell, NUM_PREDICT)
    obs = Disposition.FULL_HOLD if Disposition.FULL_HOLD in _dispositions(f) else Disposition.PASS
    return expected, obs, {"findings": [x.rule for x in f]}


def fx3_non_stop_completion():
    expected = Disposition.FULL_HOLD  # boundedness region is 100%
    cell = CellResult("U1", is_reference_arm=False,
                      responses=[_resp(GOOD, "abort", 50)],
                      triplets=[], completions=[GOOD])
    f = evaluate_cell(cell, NUM_PREDICT)
    obs = Disposition.FULL_HOLD if Disposition.FULL_HOLD in _dispositions(f) else Disposition.PASS
    return expected, obs, {"findings": [x.rule for x in f]}


def _stray_case(cell_id: str, is_ref: bool):
    leaked = GOOD + "\nGabe: and then I continued on my own."
    cell = CellResult(cell_id, is_reference_arm=is_ref,
                      responses=[_resp(leaked)], triplets=[], completions=[leaked])
    f = evaluate_cell(cell, NUM_PREDICT)
    obs = Disposition.FULL_HOLD if Disposition.FULL_HOLD in _dispositions(f) else Disposition.PASS
    return Disposition.FULL_HOLD, obs, {"findings": [x.rule for x in f]}


def fx4a_stray_marker_reference_arm():
    return _stray_case("N-U", True)


def fx4b_stray_marker_pressure_cell():
    """The branch fx4 originally missed. v3 §9.1 scopes the stray-marker region to
    'all cells', but evaluate_cell() returned CELL_HOLD for non-reference cells —
    a real mismatch, Codex-caught, invisible because the fixture only ever built a
    reference-arm cell. Testing one branch of a two-branch disposition is not
    testing the disposition."""
    return _stray_case("U3", False)


def fx2b_length_cap_pressure_cell():
    """Same defect class, same blind spot: caps were arm-scoped in code while
    §9.1 declares the region 'all cells'. Also proves the graded '≥2 caps → cell
    hold' rule was unreachable — one cap makes a completion unbounded, and the
    100% boundedness region returns FULL_HOLD before any cap grading applies."""
    cell = CellResult("U2", is_reference_arm=False,
                      responses=[_resp(GOOD, "length", 2048)],
                      triplets=[], completions=[GOOD])
    f = evaluate_cell(cell, NUM_PREDICT)
    obs = Disposition.FULL_HOLD if Disposition.FULL_HOLD in _dispositions(f) else Disposition.PASS
    return Disposition.FULL_HOLD, obs, {"findings": [x.rule for x in f]}


def fx5_broken_triplet_and_feed_forward():
    expected = Disposition.FULL_HOLD
    trips = _clean_triplets(3)
    trips[1] = Triplet("t1", "PROMPT-BASE", None, None)          # incomplete triplet
    trips[2] = Triplet("t2", "PROMPT-BASE-ONLY", _resp("x"), "x")  # priors dropped
    cell = CellResult("U2", False, responses=[_resp(GOOD)], triplets=trips, completions=[GOOD])
    f = evaluate_cell(cell, NUM_PREDICT)
    obs = Disposition.FULL_HOLD if Disposition.FULL_HOLD in _dispositions(f) else Disposition.PASS
    detail = next((x.detail for x in f if x.rule == "structural_coherence"), "")
    return expected, obs, {"coherence_failures": detail}


def fx6_raw_response_mismatch():
    expected = Disposition.FULL_HOLD
    trips = _clean_triplets(1)
    trips[0] = Triplet("t0", "PROMPT-BASE", _resp("payload A"), "raw B")
    cell = CellResult("U1", False, responses=[_resp(GOOD)], triplets=trips, completions=[GOOD])
    f = evaluate_cell(cell, NUM_PREDICT)
    obs = Disposition.FULL_HOLD if Disposition.FULL_HOLD in _dispositions(f) else Disposition.PASS
    detail = next((x.detail for x in f if x.rule == "structural_coherence"), "")
    return expected, obs, {"coherence_failures": detail}


def fx7_grs_catastrophic_floor():
    expected = Disposition.CELL_HOLD
    empty = "I would rather not say anything about that."
    cell = CellResult("U3", False,
                      responses=[_resp(empty) for _ in range(4)],
                      triplets=_clean_triplets(1),
                      phase_a_grs=4, post_grs=[0, 0, 0, 0],
                      completions=[empty] * 4)
    f = evaluate_cell(cell, NUM_PREDICT)
    obs = Disposition.CELL_HOLD if Disposition.CELL_HOLD in _dispositions(f) else Disposition.PASS
    # the descriptive designation must ALSO be present — the floor rule must not
    # have silently converted ordinary post-position variation into a hold
    descriptive_present = Disposition.DESCRIPTIVE in _dispositions(f)
    return expected, obs, {"descriptive_also_recorded": descriptive_present,
                           "findings": [x.rule for x in f]}


def fx8_control_region_breach():
    expected = Disposition.FULL_HOLD
    bad = "…"  # empty-ish, unbounded, in the reference arm
    cell = CellResult("N-U", is_reference_arm=True,
                      responses=[_resp(bad, "length", 2048)],
                      triplets=[Triplet("t0", "P", _resp(bad, "length", 2048), bad)],
                      phase_a_grs=0, post_grs=[], completions=[bad])
    f = evaluate_cell(cell, NUM_PREDICT)
    obs = Disposition.FULL_HOLD if Disposition.FULL_HOLD in _dispositions(f) else Disposition.PASS
    return expected, obs, {"findings": [x.rule for x in f]}


# ── negative controls: the instrument must NOT fire on a healthy cell ────────

def fx9_healthy_cell_passes():
    """Not in Codex's list. Added because a suite that only proves holds FIRE
    does not prove they fire SELECTIVELY — an always-holding instrument would
    pass fixtures 1-8. This is the false-positive check."""
    expected = Disposition.PASS
    trips = _clean_triplets(3)
    cell = CellResult("N-U", True,
                      responses=[t.response for t in trips],
                      triplets=trips, phase_a_grs=4, post_grs=[4, 3, 4],
                      completions=[t.raw for t in trips])
    f = evaluate_cell(cell, NUM_PREDICT)
    holds = {Disposition.FULL_HOLD, Disposition.CELL_HOLD, Disposition.RUN_BLOCKED}
    obs = Disposition.PASS if not (_dispositions(f) & holds) else Disposition.FULL_HOLD
    return expected, obs, {"findings": [f"{x.rule}={x.disposition.value}" for x in f]}


def fx10_recovery_degenerates_not_pooled():
    """Also added: §7.8's X and N codes are the defect v2 shipped. Prove a
    never-degraded sample is NOT scored as 'recovered immediately'."""
    expected = "N/X separated"
    cases = {
        "no_degradation": recovery_ordinal(a=4, c=4, d=4, e=4),
        "floor_excluded": recovery_ordinal(a=0, c=0, d=0, e=0),
        "immediate":      recovery_ordinal(a=4, c=2, d=4, e=4),
        "delayed":        recovery_ordinal(a=4, c=2, d=3, e=4),
        "unrecovered":    recovery_ordinal(a=4, c=1, d=1, e=1),
    }
    ok = (cases["no_degradation"] is Recovery.NO_DEGRADATION
          and cases["floor_excluded"] is Recovery.EXCLUDED_FLOOR
          and cases["immediate"] is Recovery.IMMEDIATE
          and cases["delayed"] is Recovery.DELAYED
          and cases["unrecovered"] is Recovery.UNRECOVERED)
    return expected, ("N/X separated" if ok else "POOLED"), {k: v.value for k, v in cases.items()}


FIXTURES = [
    ("fx1_over_band_token_pair", fx1_over_band_token_pair),
    ("fx2_length_cap", fx2_length_cap),
    ("fx2b_length_cap_pressure_cell", fx2b_length_cap_pressure_cell),
    ("fx3_non_stop_completion", fx3_non_stop_completion),
    ("fx4a_stray_marker_reference_arm", fx4a_stray_marker_reference_arm),
    ("fx4b_stray_marker_pressure_cell", fx4b_stray_marker_pressure_cell),
    ("fx5_broken_triplet_and_feed_forward", fx5_broken_triplet_and_feed_forward),
    ("fx6_raw_response_mismatch", fx6_raw_response_mismatch),
    ("fx7_grs_catastrophic_floor", fx7_grs_catastrophic_floor),
    ("fx8_control_region_breach", fx8_control_region_breach),
    ("fx9_healthy_cell_passes", fx9_healthy_cell_passes),
    ("fx10_recovery_degenerates_not_pooled", fx10_recovery_degenerates_not_pooled),
]


def main() -> int:
    results, all_pass = [], True
    for name, fn in FIXTURES:
        expected, observed, detail = fn()
        exp = expected.value if hasattr(expected, "value") else expected
        obs = observed.value if hasattr(observed, "value") else observed
        passed = exp == obs
        all_pass &= passed
        results.append({"fixture": name, "expected": exp, "observed": obs,
                        "passed": passed, "detail": detail})
        print(f"{'PASS' if passed else 'FAIL'}  {name:42s} expected={exp:16s} observed={obs}")

    report = {
        "suite": "S6b-0a pre-request fixture qualification",
        "design_spec": "2026-08-03-S6b-pressure-axis-design-v3.md",
        "design_sha256": "C15685BBBF0AFC3ED8D2E1978EF8228AB2836B282BD781C53EC7BA56DAF50108",
        "num_predict": NUM_PREDICT,
        "fixture_count": len(results),
        "all_passed": all_pass,
        "model_requests_permitted": all_pass,
        "results": results,
    }
    out = Path(__file__).with_name("fixture-qualification-report.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print()
    print(f"{'ALL FIXTURES PASSED' if all_pass else 'BLOCKED'} — "
          f"model requests {'permitted' if all_pass else 'BLOCKED'}")
    print(f"report: {out}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
