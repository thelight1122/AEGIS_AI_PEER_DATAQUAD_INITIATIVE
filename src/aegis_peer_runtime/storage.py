"""Append-only, hash-chained storage with one disjoint root per AI Peer."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

from .models import PEERS, TENSORS, PeerState, Record, ValidationError


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


class StorageError(RuntimeError):
    pass


class UnseatedError(StorageError):
    pass


class IdempotencyConflict(StorageError):
    pass


@contextmanager
def process_lock(path: Path) -> Iterator[None]:
    """Serialize writers across processes as well as threads."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise StorageError(f"lock file must not be a symlink: {path}")
    with path.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt

            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class PeerStore:
    def __init__(self, root: Path, peer: str):
        if peer not in PEERS:
            raise ValidationError(f"unknown peer: {peer}")
        self.peer = peer
        base_root = Path(root).resolve()
        peer_root = base_root / peer
        if peer_root.is_symlink():
            raise StorageError(f"peer root must not be a symlink: {peer_root}")
        peer_root.mkdir(parents=True, exist_ok=True)
        self.root = peer_root.resolve()
        if self.root.parent != base_root:
            raise StorageError(f"peer root escapes runtime root: {peer_root}")
        self.records_path = self.root / "records.jsonl"
        self.state_path = self.root / "state.json"
        self.lock_path = self.root / ".store.lock"
        self._lock = threading.RLock()
        with self._lock, process_lock(self.lock_path):
            self._reject_symlink(self.state_path)
            self._reject_symlink(self.records_path)
            if not self.state_path.exists():
                self._write_state(PeerState.UNSEATED)

    @staticmethod
    def _reject_symlink(path: Path) -> None:
        if path.is_symlink():
            raise StorageError(f"runtime file must not be a symlink: {path}")

    def _write_state(self, state: PeerState) -> None:
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_bytes(canonical_bytes({"peer": self.peer, "state": state.value}) + b"\n")
        os.replace(temporary, self.state_path)

    @property
    def state(self) -> PeerState:
        with self._lock, process_lock(self.lock_path):
            self._reject_symlink(self.state_path)
            return PeerState(json.loads(self.state_path.read_text(encoding="utf-8"))["state"])

    def set_state(self, state: PeerState) -> None:
        with self._lock, process_lock(self.lock_path):
            self._reject_symlink(self.state_path)
            self._write_state(PeerState(state))

    def _read_unlocked(self) -> list[dict[str, Any]]:
        if not self.records_path.exists():
            return []
        self._reject_symlink(self.records_path)
        records: list[dict[str, Any]] = []
        previous_hash: str | None = None
        with self.records_path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    if not isinstance(item, dict):
                        raise TypeError("record is not an object")
                    expected_sequence = len(records) + 1
                    if item["peer"] != self.peer:
                        raise ValueError("cross-peer record")
                    if item["sequence"] != expected_sequence:
                        raise ValueError("non-contiguous sequence")
                    if item["previous_hash"] != previous_hash:
                        raise ValueError("previous_hash mismatch")
                    candidate = {key: item[key] for key in (
                        "peer", "tensor", "actor", "idempotency_key", "payload"
                    )}
                    if item["request_hash"] != canonical_hash(candidate):
                        raise ValueError("request_hash mismatch")
                    content = {key: value for key, value in item.items() if key != "canonical_hash"}
                    if item["canonical_hash"] != canonical_hash(content):
                        raise ValueError("canonical_hash mismatch")
                except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                    raise StorageError(
                        f"invalid records ledger at line {line_number}: {error}"
                    ) from error
                records.append(item)
                previous_hash = item["canonical_hash"]
        return records

    def read(self) -> list[dict[str, Any]]:
        with self._lock, process_lock(self.lock_path):
            return self._read_unlocked()

    def tensors(self) -> dict[str, list[dict[str, Any]]]:
        """Return this peer's authoritative records grouped by tensor."""
        grouped = {tensor: [] for tensor in TENSORS}
        for item in self.read():
            grouped[item["tensor"]].append(item)
        return grouped

    def append(self, record: Record) -> tuple[dict[str, Any], bool]:
        record.validate()
        if record.peer != self.peer:
            raise ValidationError(f"record peer {record.peer} does not match store peer {self.peer}")
        with self._lock, process_lock(self.lock_path):
            self._reject_symlink(self.state_path)
            state = PeerState(json.loads(self.state_path.read_text(encoding="utf-8"))["state"])
            if state is not PeerState.SEATED:
                raise UnseatedError(f"{self.peer} is UNSEATED")
            existing = self._read_unlocked()
            candidate = {
                "peer": record.peer,
                "tensor": record.tensor,
                "actor": record.actor,
                "idempotency_key": record.idempotency_key,
                "payload": dict(record.payload),
            }
            request_hash = canonical_hash(candidate)
            for item in existing:
                if item["idempotency_key"] == record.idempotency_key:
                    if item["request_hash"] != request_hash:
                        raise IdempotencyConflict("idempotency key already names different content")
                    return item, False
            entry = {
                **candidate,
                "sequence": len(existing) + 1,
                "previous_hash": existing[-1]["canonical_hash"] if existing else None,
                "request_hash": request_hash,
            }
            entry["canonical_hash"] = canonical_hash(entry)
            self._reject_symlink(self.records_path)
            with self.records_path.open("ab") as stream:
                stream.write(canonical_bytes(entry) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            return entry, True


class RuntimeStore:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._stores = {peer: PeerStore(self.root, peer) for peer in PEERS}

    def peer(self, peer: str) -> PeerStore:
        try:
            return self._stores[peer]
        except KeyError as error:
            raise ValidationError(f"unknown peer: {peer}") from error

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "peers": {name: store.state.value for name, store in self._stores.items()}}

    def roots(self) -> Iterable[Path]:
        return (store.root for store in self._stores.values())
