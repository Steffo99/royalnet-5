from typing import *
import royalnet.utils as ru
try:
    from starlette.responses import JSONResponse
except ImportError:
    JSONResponse = None


def api_response(data: ru.JSON, code: int, headers: dict = None, methods=None) -> JSONResponse:
    if headers is None:
        headers = {}
    if methods is None:
        methods = ["GET"]

    full_headers = {
        **headers,
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": ", ".join(methods).upper()
    }
    return JSONResponse(data, status_code=code, headers=full_headers)


def api_success(data: ru.JSON, methods=None) -> JSONResponse:
    result = {
        "success": True,
        "data": data
    }
    return api_response(result, code=200, methods=methods)


def api_error(error: Exception, code: int = 500, methods=None) -> JSONResponse:
    result = {
        "success": False,
        "error_type": error.__class__.__qualname__,
        "error_args": list(error.args),
        "error_code": code,
    }
    return api_response(result, code=code, methods=methods)
