try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):  # noqa: N818
        pass

class RLSFailureReason(StrEnum):
    NO_RECORDS_FOUND = "no_records_found"
    WEAK_RELEVANCE = "weak_relevance"
    PRESSURE_DEGRADED = "pressure_degraded"
    TIMEOUT = "timeout"
    BOUND_ERROR = "boundary_error"
