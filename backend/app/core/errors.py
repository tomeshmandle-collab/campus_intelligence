import uuid
from typing import List
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.error import ErrorBody, ErrorDetail, ErrorEnvelope


def get_request_id(request: Request) -> str:
    """Retrieve or generate a stable request ID for tracing."""
    return request.headers.get("x-request-id") or str(uuid.uuid4())


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Transform FastAPI request validation errors (422) into standard error envelope."""
    request_id = get_request_id(request)
    details: List[ErrorDetail] = []

    for err in exc.errors():
        loc = err.get("loc", ())
        # Filter out common prefixes ("body", "query", "path") if followed by field names
        filtered_loc = [str(x) for x in loc if x not in ("body", "query", "path")]
        field_str = ".".join(filtered_loc) if filtered_loc else ".".join(str(x) for x in loc)

        details.append(
            ErrorDetail(
                field=field_str or None,
                issue=err.get("msg", "Invalid value"),
            )
        )

    envelope = ErrorEnvelope(
        error=ErrorBody(
            code="VALIDATION_ERROR",
            message="The request could not be processed due to validation errors.",
            details=details if details else None,
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        content=envelope.model_dump(),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Transform Starlette / FastAPI HTTP exceptions into standard error envelope."""
    request_id = get_request_id(request)

    # Status 422 compatibility (HTTP_422_UNPROCESSABLE_CONTENT in newer starlette)
    http_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

    status_code_map = {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
        status.HTTP_409_CONFLICT: "CONFLICT",
        422: "VALIDATION_ERROR",
        http_422: "VALIDATION_ERROR",
        status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
    }

    code = status_code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
    message = str(exc.detail) if exc.detail else "An error occurred."

    envelope = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            details=None,
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=envelope.model_dump(),
    )
