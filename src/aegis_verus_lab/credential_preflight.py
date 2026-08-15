"""Metadata-only preflight for runtime credential source files."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
from typing import Callable


class CredentialPreflightRefused(RuntimeError):
    pass


def validate_credential_source(
    path: str | Path,
    *,
    expected_owner_uid: int = 0,
    lstat: Callable[[Path], os.stat_result] = os.lstat,
) -> None:
    source = Path(path)
    try:
        metadata = lstat(source)
    except OSError as error:
        raise CredentialPreflightRefused(f"credential source is unavailable: {source}") from error
    if stat.S_ISLNK(metadata.st_mode):
        raise CredentialPreflightRefused(f"credential source must not be a symlink: {source}")
    if not stat.S_ISREG(metadata.st_mode):
        raise CredentialPreflightRefused(f"credential source must be a regular file: {source}")
    if metadata.st_uid != expected_owner_uid:
        raise CredentialPreflightRefused(f"credential source owner must be root: {source}")
    mode = stat.S_IMODE(metadata.st_mode)
    if mode not in (0o400, 0o600):
        raise CredentialPreflightRefused(
            f"credential source permissions must be 0400 or 0600: {source}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    try:
        for path in args.paths:
            validate_credential_source(path)
    except CredentialPreflightRefused as error:
        parser.error(str(error))
    print(f"credential metadata accepted for {len(args.paths)} source files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
