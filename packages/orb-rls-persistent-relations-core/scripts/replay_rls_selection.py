from __future__ import annotations

import argparse
import asyncio
import os
from collections import Counter
from pathlib import Path

from aegis_pod_sdk import TensorKind
from orb_rls_persistent_relations_core.relevance import (
    MAX_SELECTED_REFS,
    RELEVANCE_THRESHOLD,
)
from orb_rls_persistent_relations_core.scoring import compute_relevance

from core.dataquad.ledgers import DataQuadStore
from core.dataquad import stm as _stm


class ReplayStore(DataQuadStore):
    def __init__(self, *, data_dir: Path | None = None, peer_root: Path | None = None):
        super().__init__(data_dir=str(data_dir or peer_root.parent))
        self._replay_peer_root = peer_root

    def _peer_root(self, peer_id: str) -> Path:
        if self._replay_peer_root is not None:
            return self._replay_peer_root
        return super()._peer_root(peer_id)


async def _score(
    data_dir: Path | None,
    peer_root: Path | None,
    peer_id: str,
    query: str,
    intent: str,
) -> None:
    os.environ["AEGIS_STORAGE_MODE"] = "pod"
    _stm.evict(peer_id)
    store = ReplayStore(data_dir=data_dir, peer_root=peer_root)

    selected = []
    rejected = []
    loaded_counts = {}
    for tensor in TensorKind:
        records = await store.read_records(peer_id, tensor)
        loaded_counts[tensor.value] = len(records)
        for record in records:
            score, reason = compute_relevance(
                record,
                query,
                intent,
                {"pressure_level": "low"},
                [],
            )
            ref = {
                "tensor": record.tensor.value,
                "record_id": record.id,
                "relevance": score,
                "reason": reason,
            }
            if score >= RELEVANCE_THRESHOLD:
                selected.append(ref)
            else:
                rejected.append(ref)

    selected.sort(key=lambda ref: ref["relevance"], reverse=True)
    pre_bound = len(selected)
    overflow = selected[MAX_SELECTED_REFS:]
    selected = selected[:MAX_SELECTED_REFS]

    print(f"data_dir: {data_dir}")
    print(f"peer_root: {peer_root}")
    print(f"peer_id: {peer_id}")
    print(f"query: {query}")
    print(f"intent: {intent}")
    print(f"loaded_counts: {dict(sorted(loaded_counts.items()))}")
    print(f"pre_bound_selected: {pre_bound}")
    print(f"post_bound_selected: {len(selected)}")
    print(f"rejected_below_threshold: {len(rejected)}")
    print(f"overflow_rejected_by_bound: {len(overflow)}")
    print(f"selected_tensor_counts: {dict(Counter(ref['tensor'] for ref in selected))}")
    print("top_selected:")
    for ref in selected[:10]:
        print(
            f"- {ref['relevance']:.3f} {ref['tensor']} {ref['record_id']} :: {ref['reason']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay RLS selection through the real Pod DataQuad loader."
    )
    root = parser.add_mutually_exclusive_group(required=True)
    root.add_argument("--data-dir", type=Path)
    root.add_argument("--peer-root", type=Path)
    parser.add_argument("--peer-id", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--intent", default="recall")
    args = parser.parse_args()

    asyncio.run(_score(args.data_dir, args.peer_root, args.peer_id, args.query, args.intent))


if __name__ == "__main__":
    main()
