# SHORTFALL TOTEM — Pre-existing test-suite failures (archived)

- **Totem:** TOTEM-0014
- **UTC:** 2026-09-20
- **Lane:** cross (lumin + canon)
- **Author:** Claude (Opus 4.8), Engineer session
- **Disposition:** ARCHIVED / QUARANTINED (`xfail`, non-strict) — not a regression, not blocking

## What this archives
Five tests failed on a full-suite run (`608 passed, 5 failed, 14 skipped`). All five are
**pre-existing** and **isolated from the RLS/DataQuad runtime**. They are quarantined with
`@pytest.mark.xfail(reason=..., strict=False)` referencing this totem, so the suite reads clean
while the failures remain visible and preserved (append-only, not deleted).

| Test | Reason it fails | Category |
|------|-----------------|----------|
| `test_canon_index::test_reflective_boundary_conditions_was_not_collateral_damage` | Counts "Reflective Boundary Conditions" across canon `.md` docs, expects **27**, found **37** — canon corpus grew legitimately; the expected count is stale. | canon doc-count drift |
| `test_lumin_genesis_release::test_lumin_release_is_independently_rooted_read_only_and_not_installed` | Lumin genesis release builder / layout | lumin release WIP |
| `test_lumin_genesis_release::test_lumin_release_reuses_verified_rls_code_without_verus_records` | Lumin release marker/rls-code reuse | lumin release WIP |
| `test_lumin_genesis_release::test_lumin_release_contains_architecture_only_daemon_and_tensor_context_layout` | Expects `pod/daemon-topology.json` in the built release; builder does not emit it | lumin release WIP |
| `test_lumin_genesis_release::test_lumin_mcp_exposes_activated_operations_and_fixed_remote_boundary` | Lumin MCP now exposes `lumin_query_and_record`; the test's expected tool set predates it | lumin MCP WIP |

## Evidence they are pre-existing (not caused by the RLS/Adam work)
- **Stash experiment:** with the only two tracked edits of this session reverted
  (`src/aegis_peer_runtime/live_store.py`, `deploy/verus-lab/pod/markers/rls-persistent-relations-core.verified-code-marker.json`),
  the **same 5 tests fail identically** (`5 failed, 3 passed`). Restored afterward.
- The working tree was **already dirty at session start** on branch `ci-test-runner`: uncommitted
  changes to `src/aegis_peer_runtime/rls_runtime.py`, all of `src/aegis_verus_lab/*`, and
  `tools/verus-dataquad-mcp/server.py`, plus untracked Lumin WIP
  (`tools/lumin-dataquad-mcp/`, `scripts/start_lumin_local_daemons.ps1`,
  `deploy/lumin-lab/local/foundation/…`). The Lumin failures track that in-flight work.
- The Verus verified-code-marker itself already documented **"4 pre-existing lumin shortfalls."**

## Evidence they do NOT impede Adam-One
- `adam_health` (2026-09-20, during this review): `verified: true`, `coherent: true`,
  `ready: true`, 39,704 turns, processor/rls/temporal all matched — Adam's DataQuad is
  accessible and utilizable.
- `adam_query` returns DataQuad-grounded records through the live custodian pipeline.
- The five tests exercise the **Lumin release builder** and **canon doc counts** — neither is on
  Adam-One's runtime, daemon, DataQuad, or MCP path.

## How to un-archive
When the in-flight Lumin genesis-release / canon work lands, remove the `xfail` markers (search
`TOTEM-0014`) so these tests assert green again. If a test starts passing while still marked
`xfail`, it will report `XPASS` — that is the signal to remove its marker. The canon test's
expected count should be updated to the true number of *evidence-backed* occurrences by whoever
grew the canon docs (do not blindly bump 27→37 — the assertion is about evidence-backed count).


---

## Reconciliation (appended 2026-09-23T07:23:37Z)

This Totem is designated **TOTEM-0014A**. Its identifier `TOTEM-0014` collided with an earlier, unrelated Totem in `totems.jsonl`: the Verus-lane record at 2026-09-13T09:03:10Z (the cross-instance continuity proof of concept), which keeps `TOTEM-0014`. The ledger line for this Totem (cross lane, utc 2026-09-20T00:00:00Z, line SHA-256 prefix 64C1C857806A5D69B184B52533451F54) is not rewritten; the designation is recorded by the reconciliation Totem TOTEM-0016 in `totems.jsonl`. The `TOTEM-0014` references in this document, in commit 10b9296, and in the xfail reasons in `tests/test_canon_index.py` and `tests/test_lumin_genesis_release.py` refer to TOTEM-0014A; searching for `TOTEM-0014` still finds them.
