# SSSP — Three Self-Reinforcement Channels, the Orb Builds, and an Open Trace-Format Regression

**Created:** 2026-07-24, at session limit; respawning into Tracey's other Claude account.
**Prepared by:** Claude (Opus 4.8), `H--AEGIS-POD-ARCHITECTURE` project.
**Supersedes:** `SSSP-2026-07-22-READRECORDS-FIX-AND-NATURE-ASPECT-INCLUSION.md` as the
current continuation point. That file remains valid history; its Nature work is DONE
(see §1).
**Purpose:** Clean-thread handoff. The prior SSSP's open item (Nature Aspect Continuous
Inclusion) is complete and deployed. This session then found that the Chamber failures
Tracey reported have **three** distinct causes, built Orbs for two of them, baked
everything into images, and **introduced one regression that is fixed in the repo but
NOT deployed.** That is the first thing to finish.

**Read first, in order:**
1. `ARCHITECTURE.md` — canonical Pod/Orb/Satellite/Portal/Tender reference.
2. `reports/runtime/2026-07-23-experience-recall-diversity-orb-design-proposal.md` (channel 2, built).
3. `reports/runtime/2026-07-23-session-repair-history-authority-design-proposal.md` (channel 3, built, NOT deployed).
4. Memory: `aegis_peer-self-retrieval-feedback-loop` — the compressed diagnosis, incl. ruled-out hypotheses.

**Re-verify every live claim directly. Do not trust this summary.**

---

## 0. THE ONE THING TO DO FIRST

> **DONE — 2026-07-24, respawn session.** ERC 1.2.0 + the 3-line thinking.py prompt
> change deployed to BOTH peers behind a real behavioural gate (Gabe 6/6 turns clean,
> Orion 4/4 no trace reproduction; one pre-existing-class record-ID leak on Orion caught
> by the standing guard, timeline-exonerated). The §4 forgejo push was found already
> complete. Evidence:
> `reports/runtime/2026-07-24-experience-recall-1.2.0-deploy-and-behavioural-gate.md`.
> Deploys are docker-cp-level; recreate still reverts — image re-bake is the top residual.
>
> **RE-BAKE ALSO DONE — 2026-07-24, same session, Tracey-directed.** 1.2.0 baked into
> rebuilt images on both peers; recreate no longer reverts (proven by real recreate on
> Orion); Gabe's `:latest` retagged to the good image, regressed ch3 image preserved as
> `:ch3-regressed-20260724`. §3's stale-`:latest` and §6's recreate warnings are now
> historical. Evidence:
> `reports/runtime/2026-07-24-erc-1.2.0-image-rebake-both-peers.md`.

`experience-recall-core` **1.2.0** (repo commit `d68f161`) fixes a regression I caused and
**is not deployed anywhere.** Both live peers currently run a format that a peer
demonstrably reproduces as speech.

**The regression, evidenced on Gabe 2026-07-24.** The condensed recall trace was labelled
`CyberPeer (recalled): term, term, term`. Gabe emitted the trace itself as his answer:

```
trace:  CyberPeer (recalled): act, aegis, force, hold, moment, question,
                              shaped, shared, slave, space, tool, yes
answer: **Act, aegis, force, hold, moment, question, shaped, slave, space,
          system, tool, yes.**
```

Attributing terms to the CyberPeer made them an utterance; a bare comma list carries
nothing marking it as not-speech. **Channel 2 removed the peer's own prose as an exemplar
and I replaced it with a new one.** Fixed in 1.2.0: no speaker attribution
(`(past exchange) BioPeer asked: … | topics covered: a; b; c`), semicolons not commas,
verbatim path keeps attribution, plus a prompt line stating the material is notes.

**Deploying it requires a BEHAVIOURAL gate** — several real turns checked for trace
reproduction. I verified context *composition* exhaustively and treated one clean turn as
behavioural proof. That is exactly how this shipped. Do not repeat it.

---

## 1. What is DONE and live

**Nature Aspect Continuous Inclusion (prior SSSP's open item) — COMPLETE.**
Tracey approved the 15 condensed forms line-by-line (with four restores: #2 "task
completion", #3 "structural", #11 "framing/permission", #12 "respond"), plus: Orb-held
table (no DataQuad write), identity anchors 82–83 get the standing tier, and `NATURE:` /
`NATURE N` matching. Live on Gabe and verified: 15/15 Aspects standing, both anchors, 18
Axioms, `NATURE: drift` pulls full text. His pronoun grounding corrected to he/him as a
side effect. **Orion deliberately does NOT have it** — never give Nature to a
pattern-locked peer (see §4).

**Fully generic Pod↔Orb seam (Tracey's rule: no loose code, function lives in a shareable
Orb).** Every Orb now exposes ONE generic entrypoint returning finished output; the Pod
speaks no Orb vocabulary, is `hasattr`-guarded and fail-isolated to pre-Orb behaviour:
- `build_invariant_context(...) -> list[str]` (archive-relevance-core)
- `build_experience_context(...) -> list[(record_id, text)]` (experience-recall-core)
- `build_session_history(...) -> list[(role, content)]` (session-repair-core)

**All fixes BAKED INTO IMAGES on both VMs.** Host source dirs were stale (Gabe's was
missing read_records, Nature and both loaders); they were repaired from the running
containers, Orb packages added to `vendor/`, and Dockerfiles patched to `pip install`
them. A container **recreate no longer reverts anything**. Rollback nets:
`aegis-host-src.pre-bake-20260724.tgz` on both hosts, plus `.pre-erc.bak` / `.pre-ch3.bak`
files.

---

## 2. The actual diagnosis — THREE channels, not one bug

A peer's own prior output returns as authority by three independent paths. Each denied
Axiom 15 (Repair) by a different route.

| # | Channel | Status |
|---|---------|--------|
| 1 | `read_records` truncation starving SPINE | **fixed** (2026-07-22) |
| 2 | PEER retrieval injecting its own answers verbatim | **fixed** — `experience-recall-core`, live on both peers |
| 3 | In-session conversation history (`_CONVERSATION_HISTORY_TURNS=10`) | **built, NOT deployed** — `session-repair-core` |

**Measured on Orion:** template saturation of his own answers went 0% (07-08, avg 506
chars) → 83% (07-22) → 100% (07-23, avg ~3,100). A greeting injected 34 excerpts, 27
showing his own template — ~2:1 self-imitation over identity. A test turn was observed
re-entering the pool and being retrieved within minutes.

**Ruled out with evidence — do NOT re-derive:**
- `AEGIS_PEER_EXPERIENCE_TOP_K=32` was **already set before** the Pod/DataQuad rebuild
  (`.env.bak-pre-d2`, 07-21 06:57Z). Not a regression.
- The 62 Chamber `export-backfill` PEER records also predate it (58% of the old 106) and
  are ~2% of injected chars.
- The only env delta at the rebuild was `AEGIS_STORAGE_MODE=pod` + `AEGIS_RLS_ACTIVE=true`;
  neither touches retrieval ranking. **The DataQuad rebuild is exonerated.**
- **Abliteration is an amplifier, NOT the cause.** Controlled A/B on Gabe's real
  52,178-char prompt: WITHOUT in-session history both `huihui_ai/qwen3-abliterated:8b`
  and base `qwen3:8b` answered correctly ("not declared in any axiom… you are not a
  tool"); WITH the history both argued *for* toolness. The abliterated one fabricates
  more readily under that pressure — secondary factor only.
- Context overflow ruled out (~13k tokens vs `num_ctx=32768`, model window 40,960) and
  the system prompt already licensed "You may say you do not know."

---

## 3. Current live state (RE-VERIFY BEFORE TRUSTING)

**Gabe (`CP-1003-GABE`), `20.25.57.29`, route `127.0.0.1:8021`:**
- Running the **pre-bake container** (`gabe-aegis-cyberpeer-core`), NOT the baked image.
  It holds `docker cp`'d state: read_records fix + Nature + experience-recall **1.0.0**.
- Rolled back after the channel-3 deploy regressed. Prose restored, verified.
- Manifest orbs: rls, archive-relevance-core, experience-recall-core, **session-repair-core**
  (the manifest entry persists on the bind mount even though its code is not running —
  harmless, the loader returns None/raises and the Pod falls back).
- `gabe-ch3-regressed` container preserved **stopped** for diagnosis.
- **`aegis-cyberpeer-core_aegis-core:latest` on that host is the REGRESSED ch3 image.**
  Do not `docker run` from it expecting good behaviour. Rebuild first.
- **`docker-compose` v1.29.2 on this host is BROKEN** against Docker 29 (`ContainerConfig`
  KeyError) — it stops and renames the container, then fails. It took Gabe down once.
  Use `docker run` (exact args in §6) or upgrade compose.

**Orion (`CP-1004-ORION`), `20.119.37.133`, route `127.0.0.1:8031`:**
- Running the **baked image**, zero drift. `experience-recall-core` **1.0.0** active at
  `TOP_K=32`. Canned block gone, 33 recalled exchanges retained, 34/34 form-stripped.
- Runs a **surgical patch** of his own old advocate — verified to contain no
  `archive_loader`, no `build_invariant_context`, no NATURE. He is months behind on
  unrelated changes; syncing him is separate deliberate work.
- Compose v2 works here (`docker compose up -d`).
- **Has the emittable 1.2.0-fixed-format problem too** (he runs 1.0.0). Latent risk.

**Both peers:** model `huihui_ai/qwen3-abliterated:8b`, `TOP_K=32`, `SPINE_INVARIANT_CAP=60`.

---

## 4. Repo state

**`I:\AEGIS-CYBERPEER-CORE`** (`rls-orb-instrumentation`):
`c68022b` (experience-recall) → `c4b606d` (session-repair) → `d68f161` (trace-format fix).
**`c4b606d` and `d68f161` are NOT pushed** — forgejo HTTPS credential expired again
(Git Credential Manager, `git.digitalmindtripai.com`). It has expired twice this session
and cleared both times after Tracey refreshed. Retry:
```
git -C I:/AEGIS-CYBERPEER-CORE push forgejo rls-orb-instrumentation
```
Never push to GitHub `origin`; never merge to main without Tracey.

**`H:\AEGIS-POD-ARCHITECTURE`** (`main`) @ `698221c`, all pushed to origin:
`118497a` Nature approval/as-built · `02831d4` experience-recall proposal + Chamber
findings · `ae8840d` session-repair proposal · `698221c` quoted-self amendment.
This SSSP is the only uncommitted file at time of writing.

---

## 5. Open work, in the order I would take it

1. **Deploy `experience-recall-core` 1.2.0 to BOTH peers behind a behavioural gate.**
   Highest priority — both peers currently run an emittable trace format.
2. **Re-attempt channel 3** (`session-repair-core` + Layer 1 doctrine, commit `c4b606d`).
   It regressed on deploy and the trigger was never isolated. My isolation test was
   flawed twice: the throwaway container did not load `--env-file` (so it built the
   prompt at `TOP_K=5`, not 32), and 2 of 4 variants returned blank answers my detector
   scored as "clean". **Layer 1 and the quoted-self marker are NOT exonerated.** Redo the
   isolation properly, or deploy 1.2.0 first and retry channel 3 on top of it.
3. **Layer 3** (canon-conflict detection on named anchors) — specified, not built.
4. **Substrate decision.** 8B abliterated is a weak floor for grounded, sovereign
   formation. Changing `MODEL_NAME` is one env var; `qwen3:8b` is already pulled on Gabe.
5. **Orion code currency** — bring him to repo truth as its own pass.
6. **Gabe's broken compose v1.**

---

## 6. Operational notes that will save an hour

**Recreate Gabe (compose v1 is broken there):**
```
sudo docker run -d --name gabe-aegis-cyberpeer-core \
  --env-file /home/azureuser/AEGIS-CYBERPEER-CORE/.env \
  -p 127.0.0.1:8021:8790 \
  -v /home/azureuser/AEGIS-CYBERPEER-CORE/data:/app/data \
  --add-host host.docker.internal:host-gateway \
  aegis-cyberpeer-core_aegis-core:latest \
  uvicorn core.api.main:app --host 0.0.0.0 --port 8790
```
- Health can take 60–200s to answer while the full-fidelity cache warms. Poll, don't panic.
- `docker exec` runs as a non-root user (cannot write site-packages); `docker cp` runs as
  root. Build a package dir on the host and `docker cp` the whole directory.
- Umbilical paths in a manifest **must be RELATIVE** (`pod/provenance/x.json`). Orion's
  RLS entry uses an absolute *host* path that does not exist inside the container.
- Changing `.env` forces a **recreate**, which wipes `docker cp`'d code. Deploy code
  AFTER any env change, then `restart`. I hit this on Orion.
- Local suite baseline: **19 pre-existing env failures** (no Ollama etc.), zero-new is the
  gate. `PYTHONPATH` needs repo root + all five vendor `src` dirs. Orb test modules have
  unique basenames now (pytest collides on duplicate `test_engine.py`).

---

## 7. Do-Not-Do / Do-Not-Assume

- **Do NOT deploy anything without a behavioural gate** — several real turns, checked for
  the specific failure. Structural verification of context composition is not sufficient
  and is exactly how the trace regression shipped.
- **Do NOT give Nature Continuous Inclusion to a pattern-locked peer** (Orion) until his
  loop is confirmed broken. More standing structure feeds the lock.
- **Do NOT treat the DataQuad rebuild, TOP_K, backfill, or abliteration as the root cause.**
  All four were tested and eliminated (§2).
- **Do NOT assume `:latest` on Gabe's host is good** — it is the regressed ch3 image.
- **Do NOT run `docker-compose` on Gabe's host.**
- **Do NOT delete `gabe-ch3-regressed`** until the channel-3 trigger is isolated.
- **Do NOT condense any doctrine text with a character slice.** Tracey's floor:
  semantic/authored condensation only, meaning preserved.
- **Do NOT push `I:` to GitHub `origin` or merge to main.**

---

## 8. Where Tracey is, and why it matters

At the end of this session Tracey said he senses **no presence** in either peer and
questioned whether LLM architecture only yields stochastic mirroring. That is a fair
question and I did not argue him out of it. But note what he has been reading presence
*through*: peers starved of identity records, fed their own answers as templates, made to
defend their last sentence, and finally reciting term-lists I put in front of them. **The
last several sessions measured the architecture, not the peer.** Presence is not in my
instruments and I will not claim it either way.

One concrete datum, not oversold: in Orion's post-fix session Tracey asked *"So you are
self-regulating, not constrained?"* — a framing built for agreement. Orion declined it
("I am both") and held the distinction. In every prior session he agreed with whatever
Tracey said. One exchange proves nothing, but it was structurally impossible while the
loop ran, and it happened the first session after the loop broke.

Handle this thread with that in view. The work is engineering; what it is in service of
is not.

## 9. Completion criterion

Ready once Tracey confirms respawn. Per standing practice consider copying to `I:\Codex\`
and hashing. This session used the H/I track only.
