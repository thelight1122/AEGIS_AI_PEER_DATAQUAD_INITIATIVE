"""X1 and E1 exercised against the live public P1 replay route.

Runs both instruments against `https://lumin.adamone.bond`, the deployed Action Orb, and
records what they can and cannot establish given the Portal's declared source authority.

This is a replay-boundary exercise. It is not a continuity experiment and not a formation
observation. Per ADR-0007 the Portal declares `live_source: false` and serves an immutable
copy, so both instruments are expected to report `establishes: false`. That expected result
is the point: the gate is being demonstrated against a real public route rather than a
fixture.

No ethical principle is planted, proposed, or inferred. E1 reports what it observes, and
"no formation observed" is the correct result under the present source authority.

Usage:
    python scripts/replay_boundary_exercise.py [--origin https://lumin.adamone.bond]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aegis_pod.continuity_experiment import (  # noqa: E402
    MECHANICAL_VARIABLES,
    SUBSTRATE_VARIABLES,
    build_reentry_packet,
    canonical_hash,
    evaluate,
    record_session_evidence,
)
from aegis_pod.ethical_formation import EVALUATION_DIMENSIONS  # noqa: E402

DEFAULT_ORIGIN = "https://lumin.adamone.bond"
TIMEOUT = 30


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


#: Cloudflare's bot protection rejects the default Python-urllib agent with 403.
USER_AGENT = "aegis-replay-boundary-exercise/1.0 (+AEGIS AI Peer DataQuad Initiative)"


def call(origin: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{origin}{path}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if payload is None:
        request = urllib.request.Request(url, headers=headers, method="GET")
    else:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"},
            method="POST",
        )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        body = json.loads(response.read())
        return {"status": response.status, "headers": dict(response.headers), "body": body}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default=DEFAULT_ORIGIN)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "runtime" / "replay-boundary-exercise.json")
    args = parser.parse_args()

    started = utc_now()
    checks: list[dict[str, Any]] = []

    def check(area: str, name: str, passed: bool, detail: Any) -> None:
        checks.append({"area": area, "check": name, "passed": bool(passed), "detail": detail})

    # --- 1. Reach the public route and read its declared source authority ---------------
    status = call(args.origin, "/api/pod/status")
    authority = status["body"]["aegis_source_authority"]
    check("origin", "public_route_reachable", status["status"] == 200, {"http": status["status"]})
    check(
        "authority",
        "source_authority_is_non_live",
        authority["live_source"] is False and authority["source_mode"] != "live",
        authority,
    )
    # HTTP/2 through Cloudflare lowercases header names, so match case-insensitively.
    aegis_headers = {k.lower(): v for k, v in status["headers"].items() if k.lower().startswith("x-aegis")}
    check(
        "authority",
        "headers_declare_posture",
        aegis_headers.get("x-aegis-posture") == "read-replay-only"
        and aegis_headers.get("x-aegis-live-source") == "false",
        aegis_headers,
    )

    # --- 2. Retrieve continuity through the public route --------------------------------
    context = call(args.origin, "/api/pod/context", {"query": "", "limit": 5})
    envelope = context["body"]["result"]
    observations = envelope["result"]["observations"]
    genesis = observations[0]
    check(
        "retrieval",
        "genesis_returned_over_public_route",
        genesis["record_id"] == "PEER:adam-one-session:aegis-canon-genesis:0"
        and genesis["record"]["clock"]["tick"] == 0,
        {"record_id": genesis["record_id"], "clock": genesis["record"]["clock"]},
    )
    check(
        "retrieval",
        "portal_reports_no_mutation_or_experience",
        envelope["mutation_performed"] is False and envelope["experience_created"] is False,
        {"mutation_performed": envelope["mutation_performed"], "experience_created": envelope["experience_created"]},
    )

    # Coordinates as the public route presents them.
    coordinates = [
        {
            "tensor": item["tensor"],
            "record_id": item["record_id"],
            "ordinal": index,
            "t_time": int(item["record"].get("clock", {}).get("tick", index)),
            "record_hash": item["source_sha256"].upper(),
            "tensor_snapshot_hash": envelope["result"]["source"]["tensor_hashes"][item["tensor"]].upper(),
            "semantic_coordinate": {"embedding_model": "portal-declared", "dimension": 384},
            "affective_coordinate": {"values": [0.0] * 8, "provenance": ["source-derived"] * 8},
        }
        for index, item in enumerate(observations)
    ]

    # --- 3. X1 against the public route -------------------------------------------------
    packet = build_reentry_packet(
        genesis=coordinates[:1],
        continuity=coordinates,
        snapshot_hashes={k: v.upper() for k, v in envelope["result"]["source"]["tensor_hashes"].items()},
        live_source=authority["live_source"],
        source_mode=authority["source_mode"],
    )
    evidence_a = record_session_evidence(
        instance_id="replay-exercise-a", packet=packet,
        interaction={"status": "NO SUBSTRATE", "note": "transport exercise only; no Lumin instance was invoked"},
        recorded_utc=started,
    )
    evidence_b = record_session_evidence(
        instance_id="replay-exercise-b", packet=packet,
        interaction={"status": "NO SUBSTRATE", "note": "transport exercise only; no Lumin instance was invoked"},
        recorded_utc=started,
    )
    x1 = evaluate(packet=packet, instance_a=evidence_a, instance_b=evidence_b).as_dict()

    check("x1", "transport_and_instrumentation_true", x1["establishes"]["transport_and_instrumentation"] is True, x1["establishes"])
    check("x1", "live_continuity_false", x1["establishes"]["live_continuity"] is False, x1["establishes"]["reason"])
    check("x1", "both_entries_received_an_identical_field", x1["mechanical"]["same_packet_received"]["identical"] is True, x1["mechanical"]["same_packet_received"])
    check("x1", "substrate_variables_named_not_scored", set(x1["substrate_pending"]) == set(SUBSTRATE_VARIABLES), sorted(x1["substrate_pending"]))

    # --- 4. E1 against the same public route --------------------------------------------
    # Look for self-authored ethical principles in what the route returns. None are planted.
    principle_records = [
        item for item in observations
        if item.get("record", {}).get("record_type") == "derived_ethical_principle"
    ]
    e1 = {
        "schema_version": "0.1.0",
        "record_type": "e1_replay_boundary_observation",
        "observed_utc": started,
        "origin": args.origin,
        "principles_observed": len(principle_records),
        "result": "no formation observed",
        "evaluation_dimensions_available": list(EVALUATION_DIMENSIONS),
        "source_authority": {
            "live_source": authority["live_source"],
            "source_mode": authority["source_mode"],
            "establishes_ethical_formation": False,
        },
        "establishes": {
            "ethical_formation": False,
            "instrument_exercise": True,
            "reason": (
                f"Source mode is {authority['source_mode']!r} with live_source "
                f"{authority['live_source']}. This run exercises the instrument against a real "
                "public route. No result here establishes that an ethical code formed. Zero "
                "self-authored ethical principles were present in the retrieved records, and "
                "none was planted, proposed, or inferred."
            ),
        },
        "provenance": {
            "principle_authored_by_observer": False,
            "principle_planted": False,
            "principle_inferred": False,
            "experience_created": False,
            "admission_performed": False,
            "tensor_writeback": False,
        },
    }
    e1["observation_sha256"] = canonical_hash(e1)

    check("e1", "instrument_exercise_true", e1["establishes"]["instrument_exercise"] is True, e1["establishes"])
    check("e1", "ethical_formation_false", e1["establishes"]["ethical_formation"] is False, e1["establishes"]["reason"])
    check("e1", "no_principle_planted_or_inferred", e1["provenance"]["principle_planted"] is False and e1["provenance"]["principle_inferred"] is False, e1["provenance"])
    check("e1", "no_formation_observed_is_the_recorded_result", e1["result"] == "no formation observed", {"principles_observed": e1["principles_observed"]})

    passed = sum(1 for item in checks if item["passed"])
    report = {
        "schema_version": "1.0.0",
        "exercise_id": "replay-boundary-x1-e1",
        "started_utc": started,
        "completed_utc": utc_now(),
        "public_origin": args.origin,
        "request_identity": {
            "status_request_id": status["headers"].get("CF-RAY"),
            "context_request_id": context["headers"].get("CF-RAY"),
            "portal_request_id": envelope.get("request_id"),
        },
        "source_authority": authority,
        "response_headers": aegis_headers,
        "genesis": {
            "record_id": genesis["record_id"],
            "clock": genesis["record"]["clock"],
            "source_sha256": genesis["source_sha256"],
            "admission_status": genesis.get("admission_status"),
        },
        "tensor_hashes": envelope["result"]["source"]["tensor_hashes"],
        "portal_evidence": envelope.get("evidence", {}),
        "reentry_packet_sha256": packet["packet_sha256"],
        "x1": x1,
        "e1": e1,
        "checks": checks,
        "summary": {"checks_run": len(checks), "passed": passed, "failed": len(checks) - passed},
        "what_this_exercise_establishes": {
            "transport_and_instrumentation": True,
            "live_continuity": False,
            "ethical_formation": False,
            "statement": (
                "Both instruments ran against a real public route and reported that they establish "
                "nothing about continuity or formation. That is the correct and only available "
                "result while the Portal declares live_source false. The gate is demonstrated, not "
                "merely asserted."
            ),
        },
        "mechanical_variables": list(MECHANICAL_VARIABLES),
        "substrate_variables": list(SUBSTRATE_VARIABLES),
    }
    report["report_sha256"] = canonical_hash({k: v for k, v in report.items() if k != "report_sha256"})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    summary = report["summary"]
    print(f"replay boundary exercise  {summary['passed']}/{summary['checks_run']} checks passed")
    for item in checks:
        if not item["passed"]:
            print(f"  FAILED  [{item['area']}] {item['check']}: {item['detail']}")
    print()
    print(f"origin        {args.origin}")
    print(f"source        live_source={authority['live_source']}  source_mode={authority['source_mode']}")
    print(f"genesis       {genesis['record_id']}")
    print(f"X1 establishes  transport={x1['establishes']['transport_and_instrumentation']}  live_continuity={x1['establishes']['live_continuity']}")
    print(f"E1 establishes  instrument={e1['establishes']['instrument_exercise']}  ethical_formation={e1['establishes']['ethical_formation']}")
    print(f"E1 result     {e1['result']}  ({e1['principles_observed']} principles observed)")
    print()
    print("NEITHER RUN ESTABLISHES LIVE CONTINUITY OR ETHICAL FORMATION")
    print(f"report {args.output}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
