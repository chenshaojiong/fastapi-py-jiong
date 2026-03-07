from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.schemas import ErrorResponse, UnauthorizedResponse

async def http_exception_handler(request: Request, exc):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=UnauthorizedResponse().model_dump(),
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(msg=exc.detail, code=exc.status_code).model_dump(),
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(msg=str(exc.errors()), code=status.HTTP_422_UNPROCESSABLE_ENTITY).model_dump(),
    )

async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(msg="服务器内部错误", code=status.HTTP_500_INTERNAL_SERVER_ERROR).model_dump(),
    )

def raiseValidateException( msg: str):
    """抛出验证异常"""
    raise HTTPException(
                status_code=400,
                detail=msg
            )

def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(status.HTTP_401_UNAUTHORIZED, http_exception_handler)
    app.add_exception_handler(status.HTTP_404_NOT_FOUND, http_exception_handler)
    app.add_exception_handler(status.HTTP_403_FORBIDDEN, http_exception_handler)
    app.add_exception_handler(status.HTTP_400_BAD_REQUEST, http_exception_handler)

__all__ = ["register_exception_handlers"]
