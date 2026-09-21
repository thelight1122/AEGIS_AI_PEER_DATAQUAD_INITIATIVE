"""P0 verification for Verus's own clean RLS orb attachment.

Replicates aegis_pod.orb_runtime.validate_orb_version_and_hash (the pre-invocation
version/hash gate) against Verus's vendored authoritative source and clean umbilical
pin. Read-only: no mutation, no DataQuad writeback, no live RLS. Proves the pin is
clean (no drift) and the orb attaches disabled at P0.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

POD_ROOT = Path(__file__).resolve().parent
UMBILICAL = POD_ROOT / "umbilicals" / "rls-persistent-relations-core.umbilical.json"
ORB = POD_ROOT / "orbs" / "rls-persistent-relations-core.orb.json"
VENDOR_SRC = POD_ROOT / "vendor" / "orb-rls-persistent-relations-core" / "src" / "orb_rls_persistent_relations_core"
_SOURCE_FILES = ("engine.py", "scoring.py", "relevance.py")


def _parts(version: str) -> tuple[int, ...]:
    return tuple(int(piece) for piece in version.split("."))


def _satisfies(version: str, spec: str) -> bool:
    """Evaluate a ">=X.Y.Z,<A.B.C" range rather than comparing a literal string."""
    if not version or not spec:
        return False
    try:
        target = _parts(version)
        for clause in spec.split(","):
            clause = clause.strip()
            if clause.startswith(">="):
                if target < _parts(clause[2:]):
                    return False
            elif clause.startswith("<"):
                if target >= _parts(clause[1:]):
                    return False
            else:
                return False
    except ValueError:
        return False
    return True


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def compute_runtime_hash(src: Path) -> str:
    cat = "".join((src / n).read_text(encoding="utf-8") for n in _SOURCE_FILES)
    return hashlib.sha256(cat.encode("utf-8")).hexdigest().upper()


def main() -> int:
    umbilical = load(UMBILICAL)
    orb = load(ORB)

    checks: list[tuple[str, bool, str]] = []

    # 1. identity coherence
    checks.append((
        "umbilical.orb_id == orb.orb_id",
        umbilical.get("orb_id") == orb.get("orb_id"),
        f"{umbilical.get('orb_id')} / {orb.get('orb_id')}",
    ))

    # 2. version satisfies spec. This asserted the literal string "1.0.0", which tested
    #    the version rather than the claim its own label makes. A superseding orb version
    #    is exactly what the spec range exists to admit, so evaluate the range.
    ver = umbilical.get("invocation", {}).get("orb_version", "")
    spec = orb.get("runtime", {}).get("package", {}).get("version_spec", "")
    checks.append(("orb_version satisfies version_spec", _satisfies(ver, spec), f"{ver} vs {spec}"))

    # 3. THE GATE: pinned orb_runtime_hash == computed hash of the vendored source
    pin = umbilical.get("invocation", {}).get("orb_runtime_hash", "")
    actual = compute_runtime_hash(VENDOR_SRC)
    gate_ok = pin == actual
    checks.append(("version/hash GATE: pin == vendored source hash", gate_ok, f"pin={pin[:16]}... actual={actual[:16]}..."))

    # 4. not the stale ORION pin (drift superseded, evidence preserved)
    stale = "B8788191862853F762DB38AF72E8BA516E21CE7BDBDB5FD35100A40A4675CF18"
    checks.append(("pin supersedes (not equal to) the stale ORION pin", pin != stale, f"stale={stale[:16]}..."))

    # 5. P0 read-only: orb attaches disabled, no mutation authority
    b = umbilical.get("working_parameters", {}).get("boundaries", {})
    p0_ok = (orb.get("enabled") is False and b.get("mutation") is False
             and b.get("dataquad_writeback") is False and b.get("live_rls_invoked") is False)
    checks.append(("P0 read-only: orb disabled, mutation/writeback/live-RLS all False", p0_ok, f"enabled={orb.get('enabled')} boundaries={b}"))

    print("=== Verus RLS Orb P0 attachment verification ===")
    print(f"pod_id     : {umbilical.get('pod_id')}")
    print(f"orb_id     : {umbilical.get('orb_id')}")
    print(f"umbilical  : {umbilical.get('umbilical_id')}")
    print(f"attach_pt  : {umbilical.get('attachment_point')}")
    print(f"vendored   : {VENDOR_SRC}")
    print("-" * 60)
    all_ok = True
    for name, ok, detail in checks:
        all_ok = all_ok and ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}  ({detail})")
    print("-" * 60)
    print("RESULT:", "PASS - Verus clean RLS orb verified at P0 (read-only, no drift)" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
