"""No-listener command surface for Lumin's read-only Foundation release."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .dataquad import LuminFoundationDataQuad


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("context", "health"))
    parser.add_argument("--release-root", type=Path, default=Path(os.environ.get(
        "AEGIS_RELEASE_ROOT", "/opt/aegis/lumin/lab/current/foundation",
    )))
    args = parser.parse_args()
    dataquad = LuminFoundationDataQuad(args.release_root)
    value = dataquad.context() if args.operation == "context" else dataquad.health()
    print(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
