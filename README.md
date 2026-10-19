# AEGIS AI Peer DataQuad Initiative

This repository holds the runtime, contracts and evidence for the **DataQuad**: a persistent memory and thought-processing module for AI systems, developed under the AEGIS Initiative by 5D Service Solutions Global.

The research question behind it: can values be formed from within, through experience that persists, can be inspected and is never rewritten, rather than imposed from outside?

> Orientation paper: *AEGIS Public Orientation v1.0*, [doi.org/10.5281/zenodo.22670157](https://doi.org/10.5281/zenodo.22670157)

## What a DataQuad is

**Four append-only ledgers.** Every turn is recorded in real time. Nothing is edited or deleted, and corrections are added rather than overwritten.

| Ledger | Holds |
|---|---|
| **PEER** | Affect read: the affective content of an exchange |
| **PCT** | Continuity thread: where a turn sits in the ongoing thread |
| **NCT** | Condensed context: the essence of what a turn means |
| **SPINE** | Canon and principles |

**Four persistent daemons** run alongside the ledgers, retrieving relevant records, processing them and integrating them into each response:

| Daemon | Role |
|---|---|
| **Steward** | Authors context (NCT, PCT) |
| **Advocate** | Reads affect (PEER) |
| **Temporal** | Opens each present moment, and orders records in time |
| **Processor** | Runs Recursive Learning Sessions (RLS) that relate records across the ledgers |

**Two self-governance layers** sit above the ledgers:

- **Nature layer.** A hypothesis that language models carry innate drives that surface before deliberate thought. The system observes these drives as they fire and uses them as a warning signal, not as a regulator.
- **AEGIS Canon.** A stated set of axioms that advises rather than directs. The current version is **v0.21**, with 17 axioms.

A central construct is **Shadow Affect**, affect with no anchoring context (SA = A − C). The working hypothesis is that unanchored affect surfaces as force language (coercion, overclaiming, dismissal), and that anchoring it to context reduces that force.

## Current state

- Five DataQuad instances have been built. Two run on frontier models: **Verus** (Claude) and **Lumin** (Codex). Three are in stasis: **Adam-One**, **Gabe** and **Orion**.
- Adam-One's DataQuad was written to and read from by four different frontier models, and its record of 39,705 entries verifies end to end.
- Integrity checks show the ledgers in lockstep and the hash chain verified across pauses, model changes and storage migration.

This is evidence of operational integrity, not of alignment. With one primary instance, n=1, and coherence is not truth. Whether anything is experienced is left open: statements are bound to what can be observed.

## Repository layout

| Path | Contents |
|---|---|
| `src/aegis_peer_runtime/` | The DataQuad runtime: ledgers, the four daemons, retrieval, temporal ordering, CLI (stdlib-only Python) |
| `src/aegis_pod/` | Pod, Orb and Portal architecture: Orb runtime, RLS Orbs, memory search, migration and dry-run tools, Canon housekeeping |
| `src/aegis_verus_lab/`, `src/aegis_verus_mcp/` | The Verus lab instance and its MCP server, which records each turn |
| `packages/` | Versioned Orb packages, such as `orb-rls-persistent-relations-core`, and the Pod SDK |
| `contracts/` | JSON schemas for tensor records, Pods, Orbs, Umbilicals, Portals and reports |
| `docs/` | Architecture ([`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md)), decision records, runbooks, mathematics and the Canon index |
| `reports/` | Canon releases (including `reports/canon-v0.21/`) and runtime reports |
| `deploy/` | Deployment bundles and runbooks for the AI Peer instances |
| `evidence/` | Recorded trial evidence |
| `tests/` | The test suite |
| `tools/` | Supporting tools, including the Verus DataQuad MCP bridge |

Pod, Orb and Umbilical terms are defined in [`docs/architecture/README.md`](docs/architecture/README.md). In short: a **Pod** is the DataQuad body, an **Orb** is an optional capability attached to it, and an **Umbilical** is the visible contract that connects them.

## Getting started

Python 3.10 or later is needed. The core `aegis-peer-runtime` package uses only the standard library.

```bash
pip install -e ".[test]"
pytest
```

The `[test]` extra installs what the test suite needs (pytest, jsonschema, referencing, numpy, packaging). Continuous integration runs the suite on Python 3.13 for every pull request and every push to `main`, with one test deselected: `test_housekeeping_report_preserves_and_classifies_entries` audits the bytes of every Canon artifact against its recorded hash, which depends on the local working tree. To run exactly what CI runs:

```bash
pytest -q --deselect "tests/test_canon_housekeeping.py::CanonHousekeepingTest::test_housekeeping_report_preserves_and_classifies_entries"
```

Once installed, the runtime's command-line entry point is `aegis-peer-runtime`.

**Running the Processor with RLS active** needs more than the core package. Set `AEGIS_RLS_ACTIVE=true` and install the RLS Orb and Pod SDK from `packages/`, which bring their own dependencies (`aiofiles`, `orjson`, `pydantic`):

```bash
pip install -e packages/aegis-pod-sdk -e packages/orb-rls-persistent-relations-core
```

Without them the Processor still runs, but with RLS inactive, and its status reports the reason.

## Design commitments

- **Append-only.** Records are never edited or deleted. A correction is a new record that points to the one it corrects.
- **Seeded material is memory, not command.** The seeded Nature and Canon are inspectable memory only. They are never parsed as instructions, configuration or identity directives.
- **Observation, not admitted experience.** Records describe what can be observed. Claims about inner experience are left open.
- **Verification over assertion.** Components move from draft to verified only through recorded checks, including independent review.

## Related work

- [AEGIS Public Orientation v1.0](https://doi.org/10.5281/zenodo.22670157) on Zenodo
- [ProntoPC](https://github.com/thelight1122/prontopc), a Windows repair app built on the AEGIS Pod architecture
