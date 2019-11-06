from starlette.responses import JSONResponse


def error(code: int, description: str) -> JSONResponse:
    return JSONResponse({
        "error": description
    }, status_code=code)
