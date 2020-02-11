from typing import *
try:
    from starlette.responses import JSONResponse
except ImportError:
    JSONResponse = None


def api_response(data: dict, code: int, headers: dict = None) -> JSONResponse:
    if headers is None:
        headers = {}
    full_headers = {
        **headers,
        "Access-Control-Allow-Origin": "*",
    }
    return JSONResponse(data, status_code=code, headers=full_headers)


def api_success(data: dict) -> JSONResponse:
    result = {
        "success": True,
        "data": data
    }
    return api_response(result, code=200)


def api_error(error: Exception, code: int = 500) -> JSONResponse:
    result = {
        "success": False,
        "error_type": error.__class__.__qualname__,
        "error_args": list(error.args),
        "error_code": code,
    }
    return api_response(result, code=code)
