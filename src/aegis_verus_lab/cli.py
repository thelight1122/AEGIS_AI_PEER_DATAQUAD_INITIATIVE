"""Start the Verus-only localhost LAB Bridge."""

from __future__ import annotations

import argparse
from pathlib import Path

from .api import serve
from .dataquad import VerusDataQuad
from .frontier import AnthropicMessagesAdapter, FileSecretLoader
from .runtime import VerusLabRuntime


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--model", required=True, help="exact Anthropic model identifier; provenance only")
    parser.add_argument("--anthropic-credential-file", type=Path, required=True)
    parser.add_argument("--bridge-credential-file", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8791)
    args = parser.parse_args()
    dataquad = VerusDataQuad(args.release_root, args.state_root)
    adapter = AnthropicMessagesAdapter(
        model=args.model,
        secret_loader=FileSecretLoader(args.anthropic_credential_file),
    )
    serve(
        VerusLabRuntime(dataquad, adapter),
        FileSecretLoader(args.bridge_credential_file),
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
