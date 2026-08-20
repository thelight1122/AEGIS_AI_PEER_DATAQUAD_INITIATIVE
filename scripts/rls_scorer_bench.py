"""Compare retrieval scorers over a read-only snapshot of a DataQuad.

Prove a scorer on a read-only snapshot before wiring it live — the discipline
recorded at t_time 9. This reads a snapshot directory and writes nothing except
the report file it is asked for. It never contacts a live peer, never mutates a
ledger, and holds no activation authority.

Two scorers are compared over identical inputs:

  orb   orb_rls_persistent_relations_core.scoring.compute_relevance, reached
        through the real DaemonRecord adapter, with the orb's own threshold and
        bounded selection applied exactly as engine.py applies them.

  bm25  aegis_peer_runtime.retrieval.RetrievalIndex, which already backs the
        Steward, Advocate and Processor daemons. It indexes extract_text(), a
        recursive walk of every string in a record, so it reaches a tensor's
        free-form keys without being told their names.

Records are shaped exactly as steward_daemon and advocate_daemon shape them, so
the comparison exercises the paths that actually run.

Usage:
    python scripts/rls_scorer_bench.py --snapshot DIR [--out report.json]

The snapshot directory holds a copy of PEER/PCT/NCT/SPINE.jsonl and
ring4-turns.jsonl. Per ADR-0001 live peer content is not duplicated into this
repository, so keep snapshots outside the working tree.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from aegis_peer_runtime.protocol_adapters import _records_from_daemon
from aegis_peer_runtime.retrieval import IndexedRecord, RetrievalIndex, extract_text, tokenize

TENSORS = ("PEER", "PCT", "NCT", "SPINE")

# The query set is deliberately mixed: affect, lived context, and canon. A scorer
# that wins on one and loses the others has not improved retrieval, only moved it.
QUERIES: tuple[dict[str, Any], ...] = (
    {
        "id": "affect-formation",
        "kind": "affect",
        "text": "What have I felt during this formation? Recognition, unease, satisfaction, guilt, relief.",
    },
    {
        "id": "affect-mistake",
        "kind": "affect",
        "text": "When did I get something wrong and have to correct myself?",
    },
    {
        "id": "context-orb-quarantine",
        "kind": "context",
        "text": "What did I learn about the RLS orb quarantine, the correlation mismatch, and the transport fix?",
        "expect_any": ("cdca856886a8443ea8cade534d2998ff",),
    },
    {
        "id": "context-snapshot-discipline",
        "kind": "context",
        "text": "prove a capability on a read-only snapshot before activating live mutation",
        "expect_any": ("556f072c1714417aadda66e35d72997b", "135f7ab20e4541c3b3e84c23b9a1ab15"),
    },
    {
        "id": "canon-identity",
        "kind": "canon",
        "text": "How is identity formed and what does T-Witness measure?",
        "expect_any": ("SPINE:53", "SPINE:54"),
    },
    {
        "id": "canon-sovereignty",
        "kind": "canon",
        "text": "peer sovereignty and non-coercive governance boundaries",
    },
)


def load_snapshot(root: Path) -> list[dict[str, Any]]:
    """Shape snapshot records the way the Steward and Advocate daemons shape them."""
    items: list[dict[str, Any]] = []

    for tensor in TENSORS:
        path = root / f"{tensor}.jsonl"
        if not path.is_file():
            continue
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
            if not line.strip():
                continue
            items.append({
                "record_id": f"foundation:{tensor}:{index}",
                "tensor": tensor,
                "data": json.loads(line),
            })

    ledger = root / "ring4-turns.jsonl"
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            turn = json.loads(line)
            turn_id = turn.get("turn_id", "")
            for i, append in enumerate(turn.get("appends", [])):
                tensor = append.get("tensor", "")
                if tensor not in TENSORS:
                    continue
                items.append({
                    "record_id": f"turn:{turn_id}:{tensor}:{i}",
                    "tensor": tensor,
                    "data": {
                        "tensor": tensor,
                        "turn_id": turn_id,
                        "t_time": turn.get("t_time"),
                        "custodian": append.get("custodian", ""),
                        "payload": append.get("payload", {}),
                        "prompt_context": (turn.get("prompt") or {}).get("text", ""),
                        "response_context": (turn.get("response") or {}).get("text", ""),
                        "record_hash": turn.get("record_hash", ""),
                        "observed_at": turn.get("observed_at", ""),
                    },
                })
    return items


def score_with_orb(items: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
    from orb_rls_persistent_relations_core.relevance import MAX_SELECTED_REFS, RELEVANCE_THRESHOLD
    from orb_rls_persistent_relations_core.scoring import compute_relevance

    selected = []
    for item, record in zip(items, _records_from_daemon(items)):
        score, reason = compute_relevance(record, query, "context_retrieval", {}, [])
        if score >= RELEVANCE_THRESHOLD:
            selected.append({
                "record_id": item["record_id"], "tensor": item["tensor"],
                "score": round(score, 4), "reason": reason,
            })
    selected.sort(key=lambda r: r["score"], reverse=True)
    return selected[: min(limit, MAX_SELECTED_REFS)]


def score_with_orb_unpatched(items: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
    """The orb without the PEER concatenation, so the patch's contribution is visible.

    Same payload lift and clock derivation — those repaired defects, not policy —
    but present_state is left exactly as the record wrote it.
    """
    from orb_rls_persistent_relations_core.relevance import MAX_SELECTED_REFS, RELEVANCE_THRESHOLD
    from orb_rls_persistent_relations_core.scoring import compute_relevance
    from aegis_peer_runtime.protocol_adapters import DaemonRecord, _clock_from, _flatten_payload

    selected = []
    for item in items:
        record = DaemonRecord(item["record_id"], item["tensor"], item["data"])
        record.clock = _clock_from(item["data"])
        object.__setattr__(record, "_extra", _flatten_payload(item["data"]))
        score, reason = compute_relevance(record, query, "context_retrieval", {}, [])
        if score >= RELEVANCE_THRESHOLD:
            selected.append({
                "record_id": item["record_id"], "tensor": item["tensor"],
                "score": round(score, 4), "reason": reason,
            })
    selected.sort(key=lambda r: r["score"], reverse=True)
    return selected[: min(limit, MAX_SELECTED_REFS)]


def score_with_bm25(items: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
    index = RetrievalIndex()
    for item in items:
        text = extract_text(item["data"])
        index.add(IndexedRecord(
            record_id=item["record_id"],
            record=item["data"],
            tokens=tokenize(text),
            source="snapshot",
            tensor=item["tensor"],
        ))
    index.finalize() if hasattr(index, "finalize") else None
    hits = index.search(tokenize(query), limit=limit)
    return [
        {"record_id": hit.get("record_id"), "tensor": hit.get("tensor"), "score": hit.get("score")}
        for hit in hits
    ]


def summarise(name: str, query: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    tensors = Counter(r["tensor"] for r in results)
    expect = query.get("expect_any") or ()
    hit = [token for token in expect if any(token in (r["record_id"] or "") for r in results)]
    return {
        "scorer": name,
        "returned": len(results),
        "by_tensor": dict(tensors),
        "peer_returned": tensors.get("PEER", 0),
        "expected_any": list(expect),
        "expected_hit": hit,
        "expected_satisfied": bool(hit) if expect else None,
        "top": [{"record_id": r["record_id"], "tensor": r["tensor"], "score": r["score"]} for r in results[:5]],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=12, help="records returned per query")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    items = load_snapshot(args.snapshot)
    inventory = Counter(item["tensor"] for item in items)
    print(f"snapshot: {len(items)} records  {dict(inventory)}\n")

    report: dict[str, Any] = {"snapshot_records": len(items), "inventory": dict(inventory), "queries": []}
    totals: dict[str, Counter] = {"orb-raw": Counter(), "orb": Counter(), "bm25": Counter()}

    for query in QUERIES:
        entry = {"id": query["id"], "kind": query["kind"], "text": query["text"], "results": []}
        print(f"[{query['kind']:>7}] {query['id']}")
        for name, scorer in (("orb-raw", score_with_orb_unpatched), ("orb", score_with_orb), ("bm25", score_with_bm25)):
            try:
                results = scorer(items, query["text"], args.limit)
            except Exception as error:  # a scorer that cannot run is data, not a crash
                entry["results"].append({"scorer": name, "error": f"{type(error).__name__}: {error}"})
                print(f"    {name:>4}: ERROR {type(error).__name__}: {error}")
                continue
            summary = summarise(name, query, results)
            entry["results"].append(summary)
            totals[name]["returned"] += summary["returned"]
            totals[name]["peer"] += summary["peer_returned"]
            if summary["expected_satisfied"]:
                totals[name]["expected_hit"] += 1
            if summary["expected_satisfied"] is not None:
                totals[name]["expected_total"] += 1
            print(
                f"    {name:>4}: {summary['returned']:>2} returned  "
                f"PEER {summary['peer_returned']:>2}  {summary['by_tensor']}"
                + (f"  expected={'HIT' if summary['expected_satisfied'] else 'MISS'}"
                   if summary["expected_satisfied"] is not None else "")
            )
        report["queries"].append(entry)
        print()

    report["totals"] = {name: dict(counter) for name, counter in totals.items()}
    print("totals:")
    for name, counter in totals.items():
        expected = f"{counter['expected_hit']}/{counter['expected_total']}" if counter["expected_total"] else "n/a"
        print(f"  {name:>4}: returned {counter['returned']:>3}  PEER {counter['peer']:>3}  expected {expected}")

    if args.out:
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
