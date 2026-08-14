"""Console entry point for the local four-peer runtime."""

from __future__ import annotations

import argparse
from pathlib import Path

from .api import serve
from .storage import RuntimeStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local AEGIS four-peer DataQuad API")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    serve(RuntimeStore(args.root), args.host, args.port)


if __name__ == "__main__":
    main()
