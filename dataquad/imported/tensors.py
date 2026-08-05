try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):  # noqa: N818
        pass

class TensorKind(StrEnum):
    PEER = "PEER"
    PCT = "PCT"
    NCT = "NCT"
    SPINE = "SPINE"

class CustodianKind(StrEnum):
    STEWARD = "steward"
    ADVOCATE = "advocate"
