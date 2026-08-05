"""Dynamic entrypoint resolution — makes a Umbilical's `invocation.entrypoint`
dotted path (already declared in every real Umbilical tonight, but never read
by anything until this module existed) an actual attachment mechanism instead
of documentation nobody consults.
"""
from __future__ import annotations

import importlib
from typing import Any


def resolve_entrypoint(dotted_path: str) -> Any:
    """Resolve a dotted path like "pkg.module.ClassName" to the object it names.

    Tries progressively longer module-import prefixes (since there's no syntactic
    marker for where the module ends and the attribute chain begins), then
    getattr's the remainder. Raises ImportError/AttributeError with a clear
    message if no prefix imports or no attribute resolves — never silently
    returns something else.
    """
    if not dotted_path or "." not in dotted_path:
        raise ValueError(f"resolve_entrypoint requires a dotted path, got: {dotted_path!r}")

    parts = dotted_path.split(".")
    module = None
    split_index = None
    for i in range(len(parts), 0, -1):
        candidate = ".".join(parts[:i])
        try:
            module = importlib.import_module(candidate)
            split_index = i
            break
        except ImportError:
            continue

    if module is None:
        raise ImportError(f"Could not import any module prefix of entrypoint: {dotted_path!r}")

    obj: Any = module
    for attr in parts[split_index:]:
        obj = getattr(obj, attr)
    return obj
