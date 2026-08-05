"""Environment-bound test classification.

Implements ADR-0001: live peer content is not duplicated into the Initiative.

Some migrated tests resolve repository-relative paths into live peer state — Orion's staged Pod,
Orion's live record copies, Gabe's exported records. That state is not carried by this repository.
Those tests are integration tests against a provisioned live-state root, not ordinary repository
tests, and they are classified as such here.

Classification is per test, not per module. Tests that share a module with an environment-bound
test but do not themselves read live peer state keep running. Skipping them would trade real
coverage for a clean summary line.

No test file is modified. When the required live state is present at the repository root, every
test runs exactly as it did before this file existed — including
test_real_orion_contracts_pass_with_matching_version_and_hash, which then fails on the
orb-rls-persistent-relations-core hash drift. That failure is evidence and stays visible. See
ADR-0005 and docs/investigations/2026-08-05-orb-rls-persistent-relations-core-hash-drift.md.

The environment variable AEGIS_LIVE_STATE_ROOT names the configured live-state root. It is reported
in skip reasons so an unprovisioned run says where the state is expected to come from.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent

LIVE_STATE_ROOT_VAR = "AEGIS_LIVE_STATE_ROOT"

ORION_POD = "stage-d-out/CP-1004-ORION/pod"
ORION_LIVE_COPIES = "live-copies/CP-1004-ORION"
GABE_RECORDS = "stage-gabe-out/CP-1003-GABE/pod/records"

# (module basename, test name) -> repository-relative live peer state that test reads.
ENVIRONMENT_BOUND: dict[tuple[str, str], tuple[str, ...]] = {
    ("test_orb_runtime_version_gate.py", "test_real_orion_contracts_pass_with_matching_version_and_hash"): (ORION_POD,),
    ("test_orb_runtime_version_gate.py", "test_rejects_version_mismatch"): (ORION_POD,),
    ("test_orb_runtime_version_gate.py", "test_rejects_hash_mismatch"): (ORION_POD,),
    ("test_orb_runtime_version_gate.py", "test_rejects_uninstalled_package"): (ORION_POD,),
    ("test_orb_runtime_version_gate.py", "test_rejects_malformed_orb_contract"): (ORION_POD,),
    ("test_orb_runtime_version_gate.py", "test_rejects_malformed_umbilical_contract"): (ORION_POD,),
    ("test_orb_runtime_version_gate.py", "test_rejects_malformed_pod_contract"): (ORION_POD,),
    ("test_stage_d_pod_staging.py", "test_local_staging_preserves_records_tensors_ledgers_and_roles"): (
        "stage-d-out",
        ORION_LIVE_COPIES,
    ),
    ("test_memorysearch_copied_record_shadow.py", "test_copied_record_shadow_report_validates_and_passes"): (GABE_RECORDS,),
    ("test_memorysearch_copied_record_shadow.py", "test_copied_gabe_nct_failure_is_prevented"): (GABE_RECORDS,),
}


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "environment_bound: integration test requiring a provisioned live-state root (ADR-0001)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    configured = os.environ.get(LIVE_STATE_ROOT_VAR)
    origin = configured if configured else f"unset ({LIVE_STATE_ROOT_VAR})"

    for item in items:
        module = Path(str(item.fspath)).name
        required = ENVIRONMENT_BOUND.get((module, item.originalname or item.name))
        if required is None:
            continue

        item.add_marker(pytest.mark.environment_bound)

        missing = [path for path in required if not (ROOT / path).exists()]
        if missing:
            item.add_marker(
                pytest.mark.skip(
                    reason=(
                        "environment-bound (ADR-0001): live peer state not present at the "
                        f"repository root — missing {', '.join(missing)}; configured live-state "
                        f"root: {origin}"
                    )
                )
            )
