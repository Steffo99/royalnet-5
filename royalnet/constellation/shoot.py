try:
    from starlette.responses import JSONResponse
except ImportError:
    JSONResponse = None


def shoot(code: int, description: str) -> JSONResponse:
    """Create a error :class:`~starlette.response.JSONResponse` with the passed error code and description."""
    if JSONResponse is None:
        raise ImportError("'constellation' extra is not installed")
    return JSONResponse({
        "error": description
    }, status_code=code)
