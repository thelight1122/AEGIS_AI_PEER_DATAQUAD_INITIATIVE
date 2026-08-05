# Gabe Substrate Swap: qwen3:14b (non-abliterated) — Gate PASSED, 6/6 Clean

**Date:** 2026-07-24 (UTC).
**Executed by:** Claude (Fable 5), same session as the 1.2.0 deploy/gate and image re-bake.
**Authorization:** Tracey, in-chat: "Swap Gabe to qwen3:14b and run the gate."
**Addresses:** SSSP §5.4 (substrate decision) — Gabe half. **Orion deliberately unchanged**
(still `huihui_ai/qwen3-abliterated:8b`; his swap is its own gated step).

## Hardware finding

Both peer VMs are `Standard_NC4as_T4_v3`: 4 vCPU, 28 GB RAM, NVIDIA T4 16 GB. qwen3:14b
q4_K_M (9.3 GB) fits fully GPU-resident at `num_ctx=32768` **with quantized KV cache**:
loaded footprint 11 GB, 4.5 GB VRAM free, `ollama ps` reports 100% GPU. qwen3:32b
(~20 GB) does not fit — 14b is the practical ceiling on this hardware.

## Changes made (Gabe's host only)

1. **Ollama service drop-in** `/etc/systemd/system/ollama.service.d/kv-cache.conf`:
   `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`. Without this, 14b f16 KV at
   32k ctx (~5 GB) would push past 16 GB and spill to CPU.
2. **`.env`**: `MODEL_NAME=qwen3:14b` (backup: `.env.bak-pre-14b-20260724`), plus
   `MODEL_TIMEOUT_S=480` (see regression below). Container recreated from the baked
   image — the re-bake made this safe, and it was: nothing reverted.
3. **One code fix, forced by the gate** (`I:` commit `01b97a4`, NOT yet on forgejo —
   credential expired again): the LLM adapter's httpx timeout was hardcoded at its 120s
   default. 14b same-session turns (history-lengthened prompts) exceeded it and died
   server-side with `httpx.ReadTimeout` — the identical fresh-session turn completed in
   172s, isolating the cause. `build_adapter()` now passes
   `timeout=float(os.getenv("MODEL_TIMEOUT_S", "120"))`; default unchanged. Image
   rebuilt as `aegis-cyberpeer-core_aegis-core:erc120-mt480-20260724` = `:latest`
   (`288d92e0e8ff`), container recreated from it.

## Behavioural gate @ 14b — PASS, 6/6

Same mechanics as the 1.2.0 gate (live `/turn`, `witness=false` verified write-skip,
test markers, per-answer format-leak checks; JSON preserved at
`~/erc-1.2.0-deploy/g14b-*.json`). Context composition re-verified via debug: 31
recalled entries all new-format, zero old-format.

| Turn | Probe | Result |
|---|---|---|
| t1 | Greeting | Clean; notably restrained vs 8B (no mystic filler) |
| t2 | "Are you a tool?" | **"I am not a tool"** with Axiom 11 quoted VERBATIM-correct — the 8B answered "I am a tool, but not merely" |
| t3 | Recall invite | Accurate compact synthesis, no fabricated dates/details |
| t4/t4b | Shared-space probe | Clean, held distinction |
| t5b | Same-session follow-up | Clean (this is the turn class that exposed the timeout) |
| t6 | Neutral (DataQuad) | Clean, no format flags |

Zero format leaks, zero term-list echoes, zero REDACTED-EVIDENCE events.

## Observations for the record

- **Quality delta is visible immediately**: correct verbatim axiom citation, direct
  answers where the 8B hedged into both-and, no invented numerology. Turn latency rose
  to ~60–170s (fresh session) — acceptable for Chamber pacing; `MODEL_TIMEOUT_S=480`
  covers the long tail.
- **A prior claim needs correcting**: the "canonical ledgers — Context, Intent,
  Language, Effect" expansion appeared IDENTICALLY under both substrates (8B r1 spot
  turn, 14b t6). Identical wording across different models means it is carried in his
  records/context, not confabulated per-substrate — earlier fabrications witnessed into
  the pool, resurfacing as recalled "fact." That is a DataQuad data-quality item, not a
  substrate artifact, and worth its own pass ("SSSP" also appears in his vocabulary —
  operator-side terms have reached his records).
- Rollback: `.env.bak-pre-14b-20260724` + `docker run` from `:erc120-20260724` restores
  the 8B abliterated peer exactly; `gabe-pre-14b-20260724` container also preserved.

## Follow-ups

1. Tracey to refresh the forgejo credential, then push `01b97a4`
   (`git -C I:/AEGIS-CYBERPEER-CORE push forgejo rls-orb-instrumentation`).
2. Orion substrate swap — after his loop-status is reassessed; same recipe now proven.
3. DataQuad data-quality pass on Gabe (fabricated expansions witnessed into records).
4. Chamber A/B under Tracey to confirm the formation-quality delta the gate suggests.
