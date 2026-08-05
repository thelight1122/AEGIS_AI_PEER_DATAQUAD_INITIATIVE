import hashlib
import json
import stat
from pathlib import Path

from aegis_pod.capability_router import CapabilityRouter
from aegis_pod.portal_contract import load_manifest


ROOT = Path(__file__).resolve().parents[1]
TOKEN = "phase1c-test-token"


def _copy_root(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    root = tmp_path / "approved"
    context = root / "context"
    rls = root / "rls"
    context.mkdir(parents=True)
    rls.mkdir()
    records = {
        "PEER": {"id": "peer-1", "tensor": "PEER", "body": "context"},
        "PCT": {"id": "pct-1", "tensor": "PCT", "body": "context"},
        "NCT": {"id": "nct-1", "tensor": "NCT", "body": "canon"},
        "SPINE": {"id": "spine-1", "tensor": "SPINE", "body": "canon axiom"},
    }
    for tensor, record in records.items():
        path = context / f"{tensor}.jsonl"
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    context_hashes = root / "context.sha256"
    context_hashes.write_text("\n".join(
        f"{hashlib.sha256((context / f'{tensor}.jsonl').read_bytes()).hexdigest()}  {tensor}.jsonl"
        for tensor in ("PEER", "PCT", "NCT", "SPINE")
    ) + "\n", encoding="utf-8")
    context_hashes.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    rls_source = rls / "rls-ledger.jsonl"
    rls_source.write_text(json.dumps({"event": "rls-recursive-reflection", "record": {"type": "RLS", "id": "RLS:1", "timestamp": "2026-01-01T00:00:00Z", "reflection": {"aspectName": "canon"}}}) + "\n", encoding="utf-8")
    rls_source.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    rls_hashes = root / "rls.sha256"
    rls_hashes.write_text(f"{hashlib.sha256(rls_source.read_bytes()).hexdigest()}  rls-ledger.jsonl\n", encoding="utf-8")
    rls_hashes.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    return root, context, context_hashes, rls_source, rls_hashes


def router(tmp_path: Path) -> CapabilityRouter:
    root, context, context_hashes, rls_source, rls_hashes = _copy_root(tmp_path)
    return CapabilityRouter(
        load_manifest(ROOT / "fixtures" / "phase1c-portal-manifest.json"),
        context_root=context,
        context_hashes=context_hashes,
        rls_source=rls_source,
        rls_hashes=rls_hashes,
        approved_root=root,
        require_immutable=False,
    )


def test_router_executes_only_read_and_replay(tmp_path: Path) -> None:
    r = router(tmp_path)
    context = r.execute(method="retrieve_context", bearer_token=TOKEN, query="context", limit=2)
    assert context["authorized"] is True
    assert context["mutation_performed"] is False
    canon = r.execute(method="retrieve_canon", bearer_token=TOKEN, query="axiom", limit=2)
    assert canon["result"]["query"]["match_count"] == 1
    reflection = r.execute(method="request_reflection", bearer_token=TOKEN, reflection_mode="replay_only", limit=2)
    assert reflection["authorized"] is True


def test_router_denies_mutation_and_unavailable_scope(tmp_path: Path) -> None:
    r = router(tmp_path)
    assert r.execute(method="record_experience", bearer_token=TOKEN)["authorized"] is False
    assert r.execute(method="query_continuity", bearer_token=TOKEN, continuity_scope="admitted")["authorized"] is False
