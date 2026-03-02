from pydantic import BaseModel, Field
from typing import Optional, Any, Generic, TypeVar

T = TypeVar('T')

class BaseResponse(BaseModel):
    code: int = Field(..., description="响应状态码")
    msg: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")

class SuccessResponse(BaseResponse):
    code: int = Field(0, description="成功状态码")
    msg: str = Field("操作成功", description="成功消息")

class ErrorResponse(BaseResponse):
    code: int = Field(-1, description="错误状态码")
    msg: str = Field("操作失败", description="错误消息")

class UnauthorizedResponse(BaseResponse):
    code: int = Field(401, description="未授权状态码")
    msg: str = Field("无效的认证凭证", description="未授权消息")

class DataResponse(BaseModel, Generic[T]):
    code: int = Field(0, description="成功状态码")
    msg: str = Field("操作成功", description="成功消息")
    data: Optional[T] = Field(None, description="响应数据")

__all__ = [
    'BaseResponse',
    'SuccessResponse',
    'ErrorResponse',
    'UnauthorizedResponse',
    'DataResponse',
]