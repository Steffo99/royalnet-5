from starlette.responses import JSONResponse


def shoot(code: int, description: str) -> JSONResponse:
    """Create a error :class:`JSONResponse` with the passed error code and description."""
    return JSONResponse({
        "error": description
    }, status_code=code)
