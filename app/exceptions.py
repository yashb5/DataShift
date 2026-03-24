from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "timestamp": datetime.utcnow().isoformat(),
            "status": exc.status_code,
            "error": get_error_name(exc.status_code),
            "message": exc.detail,
            "path": str(request.url.path),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "timestamp": datetime.utcnow().isoformat(),
            "status": 400,
            "error": "Bad Request",
            "message": str(exc.errors()),
            "path": str(request.url.path),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "timestamp": datetime.utcnow().isoformat(),
            "status": 500,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "path": str(request.url.path),
        },
    )


def get_error_name(status_code: int) -> str:
    error_names = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
    }
    return error_names.get(status_code, "Unknown Error")
