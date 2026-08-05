from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from core.api.dependencies import get_store
from core.custodians.advocate import Advocate
from core.custodians.steward import Steward
from core.dataquad.ledgers import DataQuadStore
from core.dataquad.twitness import witness_event
from core.orbs.rls_loader import resolve_rls_engine_class

router = APIRouter()

class RLSSessionRequest(BaseModel):
    peer_id: str = "CP-1004-ORION"
    session_id: str = "cp-1004-orion-session"
    user_message: str
    intent: str = "recall"
    pressure_state: dict = Field(default_factory=dict)
    nature_aspects: list[str] = Field(default_factory=list)

@router.post("/rls/session")
async def execute_rls_session(
    req: RLSSessionRequest,
    store: DataQuadStore = Depends(get_store)
):
    engine_class = resolve_rls_engine_class(store, req.peer_id)
    engine = engine_class(
        store=store,
        steward_factory=Steward,
        advocate_factory=Advocate,
        witness_event=witness_event,
    )
    session = await engine.execute_session(
        peer_id=req.peer_id,
        session_id=req.session_id,
        user_message=req.user_message,
        intent=req.intent,
        pressure_state=req.pressure_state,
        nature_aspects=req.nature_aspects
    )
    return session.model_dump()
