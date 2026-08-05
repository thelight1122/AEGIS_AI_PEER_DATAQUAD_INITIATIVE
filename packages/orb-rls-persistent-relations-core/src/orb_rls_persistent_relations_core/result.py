from pydantic import BaseModel
from .session import RecursiveLearningSession

class RLSResult(BaseModel):
    session: RecursiveLearningSession
    ok: bool
    summary: str
