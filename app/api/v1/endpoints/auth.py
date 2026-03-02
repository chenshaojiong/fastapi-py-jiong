from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any, Optional
from jose import jwt, JWTError
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.core.config import settings
from app.schemas.response import SuccessResponse, DataResponse
from app.core.forms import LoginForm, RegistrationForm
from app.schemas.user import (
    UserCreate, UserResponse, Token, UserUpdate,
    PasswordChange, PasswordReset, PasswordResetRequest,
    EmailVerification, PhoneVerification, UserLogin
)
from app.schemas.response import SuccessResponse, ErrorResponse, UnauthorizedResponse
from app.services.user_service import UserService
from app.models.user import User
from app.core.validators import EmailValidator, PhoneValidator
from app.core.dependencies import ResponseHandler

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 依赖项：获取当前用户
async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = UserService.get_user(db, int(user_id))
    if user is None:
        raise credentials_exception
    
    return user

# 依赖项：获取当前活跃用户
async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    return current_user

# 依赖项：获取当前超级用户
async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限"
        )
    return current_user

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=DataResponse[UserResponse])
async def register(
    form_data: RegistrationForm = Depends(RegistrationForm.as_form),
    db: Session = Depends(get_db)
) -> Any:
    """用户注册（表单方式）"""

    
    # 检查用户名是否存在
    user = UserService.get_user_by_username(db, username=form_data.username)
    if user:
        return ErrorResponse(
            code=1000,
            msg="用户名已存在"
        )
    
    # 检查邮箱是否存在
    user = UserService.get_user_by_email(db, email=form_data.email)
    if user:
        return ErrorResponse(
            code=1001,
            msg="邮箱已被注册"
        )
    
    # 检查手机号是否存在
    if form_data.phone:
        user = UserService.get_user_by_phone(db, phone=form_data.phone)
        if user:
            return ErrorResponse(
                code=1002,
                msg="手机号已被注册"
            )
    
    # 创建用户
    user_in = UserCreate(
        username=form_data.username,
        email=form_data.email,
        password=form_data.password,
        confirm_password=form_data.confirm_password,
        phone=form_data.phone,
        agree_terms=form_data.agree_terms
    )
    
    user = UserService.create_user(db, user_in)
    return DataResponse(
        data=user
    )

@router.post("/login/form", response_model=DataResponse[TokenResponse])
async def login_form(
    form_data: LoginForm = Depends(LoginForm.as_form),
    db: Session = Depends(get_db)
) -> Any:
    """用户登录（表单方式）"""
    user = UserService.authenticate_user(
        db, username=form_data.username, password=form_data.password
    )

    if not user:
        print(user)
        return ErrorResponse(
            code=1003,
            msg="用户名或密码错误"
        )

    if not user.is_active:
        return ErrorResponse(
            code=1004,
            msg="用户已被禁用"
        )
      
    # 根据remember_me设置token过期时间
    expires_delta = timedelta(days=30) if form_data.remember_me else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=expires_delta
    )
    
    return DataResponse(
        data = TokenResponse(access_token=access_token)
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """用户登录（OAuth2标准方式）"""
    user = UserService.authenticate_user(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        return ErrorResponse(
            code=1003,
            msg="用户名或密码错误"
        )
    
    if not user.is_active:
        return ErrorResponse(
            code=1004,
            msg="用户已被禁用"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return DataResponse(
        data = TokenResponse(access_token=access_token)
    )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """用户登出"""
    # 这里可以添加黑名单逻辑
    return SuccessResponse()

@router.get("/me", response_model=DataResponse[UserResponse])
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return DataResponse(
        data = current_user
    )

@router.put("/me", response_model=DataResponse[UserResponse])
async def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新当前用户信息"""
    user = UserService.update_user(db, current_user.id, user_update)
    return DataResponse(
        data = user
    )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.hashed_password):
        return ErrorResponse(
            code=1005,
            msg="旧密码错误"
        )
    
    # 更新密码
    success = UserService.update_password(
        db, current_user.id, password_data.new_password
    )
    
    if not success:
        return ErrorResponse(
            code=1006,
            msg="密码修改失败"
        )
    
    return SuccessResponse()

@router.post("/reset-password/request")
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """请求密码重置"""
    user = None
    if request_data.email:
        user = UserService.get_user_by_email(db, request_data.email)
    elif request_data.phone:
        user = UserService.get_user_by_phone(db, request_data.phone)
    
    if not user:
        # 为了安全，即使用户不存在也返回成功
        return SuccessResponse(
            msg="如果邮箱或手机号存在，重置链接将发送"
        )
    
    # 生成重置令牌
    reset_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=30)
    )
    
    # TODO: 发送重置邮件/短信
    # send_reset_email(user.email, reset_token)
    
    return SuccessResponse(
        msg="重置链接已发送"
    )

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """重置密码"""
    try:
        # 验证令牌
        payload = jwt.decode(
            reset_data.token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id = int(payload.get("sub"))
    except JWTError:
        return ErrorResponse(
            code=1007,
            msg="无效或已过期的重置令牌"
        )
    
    # 更新密码
    success = UserService.update_password(db, user_id, reset_data.new_password)
    
    if not success:
        return ErrorResponse(
            code=1006,
            msg="密码重置失败"
        )
    
    return SuccessResponse()

@router.post("/verify-email")
async def verify_email(
    verification: EmailVerification,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """验证邮箱"""
    # TODO: 实现邮箱验证逻辑
    return SuccessResponse()

@router.post("/verify-phone")
async def verify_phone(
    verification: PhoneVerification,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """验证手机号"""
    # 验证手机号格式
    if not PhoneValidator.validate_chinese_phone(verification.phone):
        return ErrorResponse(
            code=1008,
            msg="无效的手机号码"
        )
    
    # TODO: 实现手机验证逻辑
    
    return SuccessResponse()    

@router.get("/users", response_model=DataResponse[list[UserResponse]])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)  # 只有超级用户可以查看所有用户
):
    """获取所有用户（仅超级用户）"""
    users = UserService.get_users(db, skip=skip, limit=limit)
    return DataResponse(
        data=users
    )

@router.get("/users/{user_id}", response_model=DataResponse[UserResponse])
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)  # 只有超级用户可以查看其他用户
):
    """获取指定用户信息（仅超级用户）"""
    user = UserService.get_user(db, user_id)
    if not user:
        return ErrorResponse(
            code=1009,
            msg="用户不存在"
        )
    return DataResponse(
        data=user
    )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)  # 只有超级用户可以删除用户
):
    """删除用户（仅超级用户）"""
    # 不能删除自己
    if user_id == current_user.id:
        return ErrorResponse(
            code=1010,
            msg="不能删除自己的账号"
        )
    
    success = UserService.delete_user(db, user_id)
    if not success:
        return ErrorResponse(
            code=1009,
            msg="用户不存在"
        )
    
    return SuccessResponse(
        msg="用户删除成功"
    )
