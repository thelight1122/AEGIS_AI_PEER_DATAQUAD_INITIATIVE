"""Tripwire: this package will never import AEGIS-CYBERPEER-CORE's `core.*`
modules. If it ever does, the extraction from Stage 1 has regressed."""
import ast
from pathlib import Path


def test_no_source_file_imports_core_dot_anything():
    src_root = Path(__file__).resolve().parents[1] / "src" / "orb_rls_persistent_relations_core"
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
    assert not offenders, f"Orb will not import Pod internals: {offenders}"
