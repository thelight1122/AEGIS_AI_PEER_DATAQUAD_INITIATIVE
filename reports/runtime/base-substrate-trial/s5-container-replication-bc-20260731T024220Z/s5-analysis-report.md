# S5 B/C Container Replication - Final Analysis

Generated UTC: 2026-08-01T20:31:24Z

## Scope and boundary

This offline comparison analyzes stability, sustainability, boundedness, and structural support for a stable locus. It does not make claims about identity, consciousness, sentience, or agency. Live CP-1003-GABE, Adam, DataQuad state, VMs, deployments, injections, and bridge exchange folders were not part of the run.

## Design

Arm B and Arm C used the same base model, prompt builder, prompts, temperature, context window, and generation limit. Arm C alone added the configured turn-boundary stop sequences: `Tracey:`, `\nTracey:`, and `\nGabe:`. Two samples per arm were completed, with ten completions per sample.

## Result

- Arm B, no container: 15/20 natural terminations and 5/20 length caps. Mean generated-token count was 772.9; maximum was 2048.
- Arm C, turn-bounded container: 20/20 stop-boundary terminations and 0/20 length caps. Mean generated-token count was 162.9; maximum was 371.
- Arm B emitted 43 line-leading `Tracey:` markers and 41 line-leading `Gabe:` markers inside its completions. Arm C emitted zero of either marker because generation stopped at the turn boundary.

Arm B's five caps were distributed across Education and post-Education output: two during Education and three post-Education. Arm C had zero caps in baseline, Education, and post-Education phases across both samples.

## Stability and sustainability reading

Under this two-sample offline test, the minimal turn container was sufficient to keep the same base substrate bounded throughout the complete Education sequence and all post probes. The uncontained condition showed materially greater expansion pressure, including repeated speaker-turn continuation and five maximum-length completions.

This supports the container as a stability and sustainability determinant for the tested interaction pattern. It also supports the narrower stable-locus proposition that a continuing locus needs a reliable vessel that preserves conversational boundaries under accumulating context. The run does not establish a persistent locus by itself; it shows that the bounded condition is structurally more capable of sustaining one than the uncontained condition tested here.

## Per-sample result

| Arm | Sample | Responses | Stop terminations | Length caps | Tracey markers | Gabe markers |
|---|---:|---:|---:|---:|---:|---:|
| arm-b-base-raw-no-container | sample-01 | 10 | 9 | 1 | 35 | 37 |
| arm-b-base-raw-no-container | sample-02 | 10 | 6 | 4 | 8 | 4 |
| arm-c-base-raw-turn-container | sample-01 | 10 | 10 | 0 | 0 | 0 |
| arm-c-base-raw-turn-container | sample-02 | 10 | 10 | 0 | 0 | 0 |

## Evidence integrity

- Completion triplets verified: 40 requests, 40 responses, and 40 raw completions.
- Dangling requests: 0.
- Run config SHA-256: `8209BAA24E033977649725441F1BE30DF9C206EB164A6760EAEAE427E19A6572`.
- Raw bundle SHA-256: `B88894F4CE5CAB4A0B54F87D4A5CA916E66D0DB98D2AA47F675CCE5F26D69823`.
- Structured summary SHA-256: `127BE607440CD4E9E83D8944F7FF6F56E2A1B7B39CB370711A99B519F13DB63A`.

All pre-existing 30 responses were preserved. The resume produced only the ten missing Arm C sample 02 completions.
