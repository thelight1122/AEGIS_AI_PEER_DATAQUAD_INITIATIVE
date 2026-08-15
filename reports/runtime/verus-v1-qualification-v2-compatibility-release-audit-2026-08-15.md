# Verus v1 Qualification and v2 Compatibility Release Audit

Date: 2026-08-15
Status: READY FOR INDEPENDENT CLAUDE AUDIT / LIVE UPDATE HELD

## Source lineage

- identifier-contract source commit:
  `599ee0e8a61039c60e001ce83140fe2fef7d6fb6`
- compatibility/qualification source commit:
  `91388c1e7638af25aa02ce3de122388c97347ef9`
- compatibility source tree:
  `5f0cb03dccd26552b7e589112afe4f178953d332`
- compatibility commit scope: 10 paths, 416 insertions, 45 deletions
- source worktree after commit/build: clean

Append-only qualification report:

- path:
  `reports/runtime/verus-first-turn-v1-provenance-reconciliation-2026-08-15.md`
- SHA-256:
  `1B4DF143C7B9625ED0BFE7F3ADE75019A9D182A7C03203A9253660656D32FC76`

Prepared but not executed canonical v2 Desktop prompt:

- path:
  `deploy/verus-lab/claude-desktop/VERUS_V2_CANONICAL_TURN_PROMPT.md`
- SHA-256:
  `AFFBAB16AB93369D667DFCF2F3F5AA2EFFC5E967B11ACF202A3B30CE227199BB`

## Corrected compatibility contract

The v2 reader accepts only the two known turn schemas. A v1 record is
hash/chain/digest/custodian validated using its original contract. It is not
rewritten, assigned new fields, or silently upgraded. Context exposes a
derived qualification with:

- classification: `pre_correction_operational_evidence`;
- `canonical_under_v2_contract=false`;
- preservation: `append_only_do_not_rewrite`;
- caller-supplied turn-ID-without-DataQuad-classification reason;
- literal provider-identifier-placeholder reason when present; and
- absent provider availability/classification reason.

For v1 records, Processor and RLS comparison material retains the exact v1
shape so existing derived evidence continues to match. New turns use v2 only,
with DataQuad-owned local IDs and null/optional provider provenance. A new v2
turn can continue the chain after a v1 record without modifying the first
line.

Health separately reports pre-correction v1 and canonical v2 counts and keeps
the canonical-first-v2-turn pending while the v2 count is zero. CyberPeer
identity remains only `Verus`.

The systemd service remains oneshot. `active (exited)` proves only that its
health command succeeded. Runtime components are invoked by the Verus-owned
command surface; this audit does not claim continuously running daemons.

## Verification

- focused Desktop/MCP suite: 12 passed
- bounded Verus/release/deployment suites: 61 passed
- full repository suite: 480 passed, 14 skipped
- one pre-existing `jsonschema.RefResolver` deprecation warning only
- deployment shell syntax: passed
- Python AST validation: 59 files passed without bytecode generation
- diff checks: clean
- source cache/build residue: none

The preservation test constructs a valid v1 turn, retains its first-line bytes,
re-materializes exact v1 derived evidence, verifies coherent health, appends a
separate v2 test turn, and confirms that the original first line remains
byte-identical.

## Exact deterministic release

Release directory:

`H:\AEGIS_AI_PEER_DATAQUAD_RELEASES\verus-desktop-91388c1e7638`

Build inputs:

- source commit:
  `91388c1e7638af25aa02ce3de122388c97347ef9`
- preserved Foundation seating timestamp: `2026-08-15T13:28:28Z`

Release evidence:

- release manifest SHA-256:
  `B79F3AA35DCD84AC75551799C68FE4EB61969727B2F7A13E3FD90EDCA6748522`
- Foundation receipt SHA-256:
  `B5405FEA606F8FE686C7F74B464C2D5B1589481F73F37CBD85B6B4D6B1ED4D4A`
- shipped files: 27
- two-build relative-path/hash differences: 0
- activation status: `NOT_INSTALLED`
- credentials included: false
- other-peer state included: false
- forbidden HTTP/Bearer/provider-key/public-bind surface strings: 0

The temporary deterministic comparison output was removed after verification.
The exact named release remains local and has not been transferred.

## Exact live-v1 compatibility smoke

The four live state ledgers were read from Gabe without replay or reconcile and
copied into an isolated local temporary state root. The exact new release ran
health and context against that copy only.

Result:

- status ok / ready true / coherent true / verified true;
- committed turns 1;
- pre-correction v1 turns 1;
- canonical v2 turns 0;
- canonical first v2 turn pending true;
- temporal / Processor / RLS records: 1 / 1 / 1;
- missing, orphan, and mismatched derived evidence: none;
- record/head hash:
  `2306cc87f7886885732b57a55a562bee88cb4e6b28f8cfde07f4243acf5ffb35`;
- context classification: `pre_correction_operational_evidence`;
- canonical under v2: false;
- preservation: `append_only_do_not_rewrite`.

Copied ledger hashes after new-release health remained equal to the live
read-only values:

- Ring 4:
  `264349BE59B0B3E730644551B75C6C4E9AEBDF6112253AA8A3ADB929B224D3F2`
- temporal:
  `62503149ECD16B3932E8FA016FB409F6BBCFDCCE56178F0B156B4D1C665B31FC`
- Processor:
  `37ECEDADC57158799BBA954DA84B55E2343CA81BDF77341890FD218FEB42CB73`
- RLS:
  `ADCA5029836EFF4CBB5C46FB7B5D18C76A3FA904BE00C2E3DCD52A91952490C6`

The isolated compatibility state root was removed after the check. No live
file changed.

## Independent audit request and hold

Claude is asked to audit both source commits, the exact release manifest, the
append-only v1 qualification, and the prepared-but-unexecuted v2 prompt.
Acceptance should explicitly confirm:

1. the immutable v1 turn is preserved as operational evidence but is
   noncanonical under v2;
2. literal unavailable markers are not treated as genuine provider IDs;
3. old Processor/RLS evidence remains coherent without rewrite;
4. new v2 turns use DataQuad-owned local IDs and null/optional provider fields;
5. the new release can safely read the exact existing live state;
6. the oneshot command language does not imply continuously running daemons;
7. the release remains Desktop/stdio/SSH command-only with no provider-key,
   HTTP, or public-listener surface; and
8. no second/canonical turn should be generated during deployment verification.

No Gabe update, Desktop configuration mutation, model interaction, or new turn
is authorized until a new explicit Claude `ACCEPT` cites compatibility commit
`91388c1e7638af25aa02ce3de122388c97347ef9` and release manifest SHA-256
`B79F3AA35DCD84AC75551799C68FE4EB61969727B2F7A13E3FD90EDCA6748522`.
