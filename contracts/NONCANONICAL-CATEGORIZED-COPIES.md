# Noncanonical: categorized contract copies

**Governing decision:** [ADR-0002](../docs/decisions/ADR-0002-flat-contracts-canonical-for-p0.md)

The flat `*.schema.json` files in this directory are canonical. The implementation and the test
suite resolve contracts from the flat layout.

These subdirectories hold noncanonical duplicates produced by the migration script's selection
heuristic:

```text
contracts/orb/
contracts/pod/
contracts/portal/
contracts/tensor/
contracts/umbilical/
```

No architecture decision ratified that hierarchy. Nothing reads from it.

They are not removed during P0, because P0's commitment is behavioral preservation. Removal happens
later through a recorded, hash-verified cleanup.

**While both layouts are present, any contract edit applies to the flat files only.** Editing a
subdirectory copy creates drift between two trees that look equally authoritative and are not.
