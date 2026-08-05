# Stage D2 preservation (off-machine copy)

The D2 Pod-aware runtime diff, preserved here because it otherwise lives only in
the local `I:\AEGIS-CYBERPEER-CORE` repo (branch `stage-d2-pod-aware-runtime`,
commits 068f8bb + 276e0c6 off deployed-truth `2b687df`), not pushed to any Forge.

- `stage-d2.patch` - `git apply`/`git am` onto `2b687df`. SHA256 32365A2FA0399B358AA330E9267B493F313A8BFF8FEF4BA6D21631B0D768EBE2.
- `stage-d2.bundle` - `git clone`/`git fetch` an isolated copy of the branch.

To resume review: apply onto the deployed-truth baseline, then reproduce tests per STAGE-D2-DESIGN.md.
Deploy remains gated on independent (second-observer) review + Tracey per-sub-stage consent.
