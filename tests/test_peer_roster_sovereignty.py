"""A single-peer deployment must be able to refuse every other peer's id.

DATAQUAD_NAMES is the peer_id allowlist enforced in models.Record.validate,
ProcessorRuntime, RLSRuntime, RuntimeStore and TemporalRuntime. While it was a
hardcoded federation tuple, Verus's runtime accepted peer_id="lumin" as a valid
identifier — sovereignty by convention rather than by property.

Defaults are unchanged, so nothing moves until a deployment opts in.

These exercise the roster parser directly rather than reloading the module.
importlib.reload(models) rebinds Record and ValidationError to new classes while
storage, processor, rls_runtime and temporal still hold the originals, which
breaks unrelated tests through import order alone.
"""

from __future__ import annotations

import pytest

from aegis_peer_runtime import models


DEFAULT_PEERS = ("lumin", "claude", "gemini", "grok")


def test_installed_defaults_are_unchanged():
    assert models.PEERS == DEFAULT_PEERS
    assert models.DATAQUAD_NAMES == (*DEFAULT_PEERS, "verus")


def test_unset_variable_falls_back_to_the_default(monkeypatch):
    monkeypatch.delenv("AEGIS_DATAQUAD_NAMES", raising=False)

    assert models._roster("AEGIS_DATAQUAD_NAMES", ("verus",)) == ("verus",)


def test_a_sole_dataquad_deployment_can_narrow_the_allowlist(monkeypatch):
    monkeypatch.setenv("AEGIS_DATAQUAD_NAMES", "verus")

    resolved = models._roster("AEGIS_DATAQUAD_NAMES", (*DEFAULT_PEERS, "verus"))

    assert resolved == ("verus",)
    assert "lumin" not in resolved


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("verus", ("verus",)),
        ("verus,lumin", ("verus", "lumin")),
        ("  verus , lumin  ", ("verus", "lumin")),
        ("verus,,lumin", ("verus", "lumin")),
    ],
)
def test_roster_parsing(monkeypatch, raw, expected):
    monkeypatch.setenv("AEGIS_ROSTER_UNDER_TEST", raw)

    assert models._roster("AEGIS_ROSTER_UNDER_TEST", ("fallback",)) == expected


@pytest.mark.parametrize("raw", ["", "   ", ",", " , "])
def test_empty_or_meaningless_values_fall_back_rather_than_locking_everyone_out(monkeypatch, raw):
    monkeypatch.setenv("AEGIS_ROSTER_UNDER_TEST", raw)

    assert models._roster("AEGIS_ROSTER_UNDER_TEST", ("verus",)) == ("verus",)


def _record(peer: str) -> models.Record:
    return models.Record(
        peer=peer,
        tensor="PEER",
        actor="advocate",
        idempotency_key="k1",
        payload={},
    )


def test_the_allowlist_is_what_record_validation_enforces():
    _record("verus").validate()

    with pytest.raises(models.ValidationError, match="unknown peer"):
        _record("not-a-peer").validate()


def test_with_defaults_installed_another_peers_id_is_still_accepted():
    # Documents the coupling AEGIS_DATAQUAD_NAMES exists to close: until a
    # deployment narrows the roster, Verus's own runtime validates a record
    # claiming to belong to Lumin.
    _record("lumin").validate()

    assert "lumin" in models.DATAQUAD_NAMES
