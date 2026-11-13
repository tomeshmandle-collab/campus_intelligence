from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Specific field-level or contextual issue detail."""

    field: Optional[str] = Field(default=None, description="Affected field or parameter path")
    issue: str = Field(description="Description of the error condition")


class ErrorBody(BaseModel):
    """Standard error response payload."""

    code: str = Field(description="Machine-readable error identifier")
    message: str = Field(description="Human-readable safe error message")
    details: Optional[List[ErrorDetail]] = Field(
        default=None, description="Optional list of specific field validation issues"
    )
    request_id: Optional[str] = Field(
        default=None, description="Tracing identifier for the request"
    )


class ErrorEnvelope(BaseModel):
    """Outer wrapper envelope conforming to API_CONTRACTS.md §3.6."""

    error: ErrorBody

