"""Structural interface boundary an Orb depends on instead of a Pod's concrete classes.

Every Protocol here was derived from the ACTUAL calls the live rls-persistent-relations-core
Orb makes today (I:\\AEGIS-CYBERPEER-CORE\\core\\rls\\{engine,scoring,session,orb_evidence}.py,
read 2026-07-21) — not a speculative abstraction. Nothing is here that the Orb doesn't
genuinely call; nothing the Orb calls is missing.

One deliberate reshaping versus today's code: PCT-record construction (id/timestamp/
ContinuityClock assembly) moves from the Orb (engine.py currently does
`PCTRecord(id=..., clock=ContinuityClock(...), ...)` directly) into
`StewardProtocol.build_and_append_pct`. Steward already holds the boundary check for
append_pct; holding construction too means the Orb never imports a Pod's concrete
record classes at all, which is the actual point of this boundary. A Pod's own
Steward implementation is responsible for translating these calls into its concrete
PCTRecord/ContinuityClock types.
"""
from __future__ import annotations

from typing import Any, Callable, ContextManager, Protocol, runtime_checkable

from .tensors import TensorKind

TSignatureLike = Any
"""Opaque — the Orb stores and passes this through (`rls_session.t_signature = t_sig`)
but never inspects its internals. No protocol needed beyond "some value"."""


@runtime_checkable
class ClockLike(Protocol):
    tick: int
    epoch: str
    phase: str
    started_at: str
    last_advanced_at: str


@runtime_checkable
class RecordLike(Protocol):
    """Guarantees only what scoring.py's compute_relevance unconditionally reads
    (`record.tensor`, `record.id`, `record.clock`). Every other field it inspects
    (present_state, working_context, distilled_summary, essence_memory, pattern,
    nature_aspect_refs) is read defensively via getattr/hasattr in the original
    code and stays that way here — Protocol does not, and should not, force every
    record variant (PEER/PCT/NCT/SPINE) to declare fields only some of them have."""

    id: str
    tensor: TensorKind
    clock: ClockLike | None


class StewardProtocol(Protocol):
    async def read_pct(self) -> list[RecordLike]: ...

    async def read_nct(self) -> list[RecordLike]: ...

    async def build_and_append_pct(
        self,
        *,
        session_id: str,
        working_context: dict[str, Any],
        retrieved_record_ids: list[str] | None,
        rls_session_id: str,
        pressure_state: dict[str, Any],
    ) -> RecordLike:
        """Construct a PCT record (id, timestamp, clock — Pod's concern) and
        append it through the boundary, returning the written record so the
        caller can read back its `.id`."""
        ...


class AdvocateProtocol(Protocol):
    async def read_peer(self) -> list[RecordLike]: ...

    async def read_spine(self) -> list[RecordLike]: ...


class DataQuadStoreProtocol(Protocol):
    async def get_next_tick(self, peer_id: str) -> int: ...

    async def append_ledger(self, peer_id: str, ledger_name: str, entry: dict[str, Any]) -> None: ...

    async def record_relation(
        self,
        peer_id: str,
        from_id: str,
        to_id: str,
        *,
        relation: str,
        tags: list[str],
        written_by: str,
    ) -> None: ...

    def is_active(self, capability: str) -> bool:
        """Generalizes the Pod-side `AEGIS_RLS_ACTIVE` gate (core.dataquad.pod.rls_active())
        into a per-capability check any Orb can use, instead of one Orb owning a
        globally-named flag function."""
        ...

    def peer_root(self, peer_id: str) -> Any:  # pathlib.Path in practice
        """Generalizes `store.data_dir / "peers" / peer_id`, so an Orb never needs
        to know the Store's internal attribute layout."""
        ...


class WitnessEventFactory(Protocol):
    def __call__(
        self, tick: int, *, witness_mode: str, pressure_level: str
    ) -> ContextManager[Callable[[], TSignatureLike]]: ...
