from fastapi import HTTPException, status
from app.schemas import SuccessResponse, ErrorResponse, UnauthorizedResponse, DataResponse
from typing import Optional, Any, TypeVar

T = TypeVar('T')

class ResponseHandler:
    @staticmethod
    def success(data=None, msg="操作成功"):
        return SuccessResponse(data=data, msg=msg)

    @staticmethod
    def success_with_data(data: T, msg="操作成功"):
        return DataResponse(data=data, msg=msg)

    @staticmethod
    def error(msg="操作失败", code=-1):
        return ErrorResponse(data=None, msg=msg, code=code)

    @staticmethod
    def unauthorized(msg="无效的认证凭证"):
        return UnauthorizedResponse(data=None, msg=msg)

    @staticmethod
    def raise_error(msg="操作失败", code=status.HTTP_400_BAD_REQUEST):
        raise HTTPException(status_code=code, detail=msg)

    @staticmethod
    def raise_unauthorized(msg="无效的认证凭证"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
            headers={"WWW-Authenticate": "Bearer"},
        )

__all__ = ["ResponseHandler"]
