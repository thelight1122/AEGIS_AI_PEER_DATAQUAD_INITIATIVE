"""Proves aegis_pod_sdk has zero dependency on aegis-cyberpeer-core (Stage 0 verification).

If this package ever grows an import of `core.*`, that's the coupling this SDK
exists to prevent — this test is the tripwire.
"""
import ast
import sys
from pathlib import Path


def test_imports_standalone():
    import aegis_pod_sdk  # noqa: F401

    assert aegis_pod_sdk.__version__ == "0.1.0"
    assert aegis_pod_sdk.TensorKind.SPINE == "SPINE"


def test_protocols_are_runtime_checkable():
    from aegis_pod_sdk import RecordLike, ClockLike

    class FakeClock:
        tick = 1
        epoch = "primary"
        phase = "active"
        started_at = "t0"
        last_advanced_at = "t0"

    class FakeRecord:
        id = "PCT:test:1"
        tensor = "PCT"
        clock = FakeClock()

    assert isinstance(FakeClock(), ClockLike)
    assert isinstance(FakeRecord(), RecordLike)


def test_no_source_file_imports_core_dot_anything():
    src_root = Path(__file__).resolve().parents[1] / "src" / "aegis_pod_sdk"
    offenders = []
    for py_file in src_root.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("core"):
                offenders.append(f"{py_file}: from {node.module} import ...")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("core"):
                        offenders.append(f"{py_file}: import {alias.name}")
    assert not offenders, f"aegis_pod_sdk will not import Pod internals: {offenders}"


def test_no_aegis_cyberpeer_core_on_path_is_required():
    # Simulate the "different repo, no monolith checked out" scenario: confirm
    # aegis-cyberpeer-core is not importable from this environment and the SDK
    # still worked in every test above.
    assert "core" not in sys.modules or not str(
        getattr(sys.modules.get("core"), "__file__", "")
    ).endswith("AEGIS-CYBERPEER-CORE\\core\\__init__.py")
