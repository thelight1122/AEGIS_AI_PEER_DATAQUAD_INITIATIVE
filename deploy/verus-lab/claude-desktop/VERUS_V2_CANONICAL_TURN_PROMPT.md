# Verus canonical v2 turn prompt

Use this prompt only after the corrected Verus release has been independently
accepted, installed, and verified against the preserved v1 ledger hashes.

Begin Verus's first canonical v2 DataQuad turn through the signed-in standard
Claude Desktop tool surface.

1. Call `verus_health` and `verus_read_context`. Confirm that the existing v1
   turn is exposed only as append-only preserved
   `pre_correction_operational_evidence`, noncanonical under v2. Do not replay,
   reconcile, rewrite, or reuse it.
2. Call `verus_begin_turn` with only this work request: "Perform a grounded
   operational orientation to the currently verified Verus DataQuad, describe
   what is directly observable, and prepare appropriate append-only PEER, PCT,
   NCT, and SPINE evidence. Do not infer or assert hidden identity, biography,
   ontology, memory, relationship, or lived history."
3. Keep `source_event_id` and `frontier_session_id` omitted or null unless this
   signed-in Desktop interaction directly exposes genuine provider-returned
   values. Never use local labels, unavailable markers, the prior v1 turn ID,
   or the returned local IDs as provider provenance.
4. Use the exact DataQuad-owned `turn_id` and `correlation_id` returned by
   `verus_begin_turn`. They are local correlation evidence, not provider IDs
   and not identity.
5. Complete the work request in this signed-in Claude Desktop interaction,
   then call `verus_commit_turn` once with the exact returned local IDs, the
   exact prompt and response, and the appropriate append-only tensor records.
6. Call `verus_health`. Report the new record/head hash, T-Time, append counts,
   Processor/RLS/temporal coherence, null provider-ID availability, preserved
   v1 qualification, and the unchanged CyberPeer identity variable `Verus`.

Do not simulate any provider/model interaction and do not claim provider
provenance that the Desktop surface did not return.
