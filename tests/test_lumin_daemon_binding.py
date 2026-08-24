"""Lumin daemon binding must never inherit the Verus peer default."""

from pathlib import Path

from aegis_peer_runtime.processor_daemon import ProcessorDaemon


def test_processor_preserves_historical_default(tmp_path: Path) -> None:
    daemon = ProcessorDaemon(tmp_path / "processor.sock", tmp_path / "release", tmp_path)
    assert daemon._peer_id == "verus"


def test_processor_accepts_explicit_peer_binding(tmp_path: Path) -> None:
    daemon = ProcessorDaemon(
        tmp_path / "processor.sock", tmp_path / "release", tmp_path,
        peer_id="example-peer",
    )
    assert daemon._peer_id == "example-peer"
