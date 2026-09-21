from typing import Any

from pydantic import BaseModel, Field

class RLSRecordRef(BaseModel):
    tensor: str
    record_id: str
    relevance: float
    reason: str

class RecursiveLearningSession(BaseModel):
    id: str
    peer_id: str
    session_id: str
    user_message: str
    intent: str
    pressure_state: dict = Field(default_factory=dict)
    selected_refs: list[RLSRecordRef] = Field(default_factory=list)
    rejected_refs: list[RLSRecordRef] = Field(default_factory=list)
    t_signature: Any | None = None
    """Opaque (aegis_pod_sdk.TSignatureLike) — RLS stores and passes this through,
    never inspects its internals, so Any is the honest type here rather than a
    fake TSignature class that would just re-couple to the Pod's concrete shape."""
    failure_is_data: bool = False
    failure_reason: str | None = None
    created_pct_record_id: str | None = None
    notes: list[str] = Field(default_factory=list)
