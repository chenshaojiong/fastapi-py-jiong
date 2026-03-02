from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime, date
from app.core.validators import (
    PasswordValidator, PhoneValidator, 
    UsernameValidator, EmailValidator
)

# 基础用户模型
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="电子邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")
    phone: Optional[str] = Field(None, description="手机号码")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    birth_date: Optional[date] = Field(None, description="出生日期")
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$", description="性别")
    
    @field_validator('username')
    def validate_username(cls, v):
        if not UsernameValidator.validate_username(v):
            from app.schemas.response import ErrorResponse
            raise ValueError(ErrorResponse(msg=UsernameValidator.get_username_requirements(), code=-1).model_dump_json())
        return v   
    
    @field_validator('phone')
    def validate_phone(cls, v):
        if v and not PhoneValidator.validate_chinese_phone(v):
            from app.schemas.response import ErrorResponse
            raise ValueError(ErrorResponse(msg="无效的手机号码", code=-1).model_dump_json())
        return v
    
    @field_validator('birth_date')
    def validate_age(cls, v):
        if v:
            today = date.today()
            age = today.year - v.year
            if today.month < v.month or (today.month == v.month and today.day < v.day):
                age -= 1
            
            if age < 18 or age > 100:
                from app.schemas.response import ErrorResponse
                raise ValueError(ErrorResponse(msg="年龄必须在18-100岁之间", code=-1).model_dump_json())
        return v

# 用户更新
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")
    email: Optional[EmailStr] = Field(None, description="电子邮箱")
    phone: Optional[str] = Field(None, description="手机号码")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    birth_date: Optional[date] = Field(None, description="出生日期")
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$", description="性别")
    avatar: Optional[str] = Field(None, description="头像URL")
    
    @field_validator('phone')
    def validate_phone(cls, v):
        if v and not PhoneValidator.validate_chinese_phone(v):
            from app.schemas.response import ErrorResponse
            raise ValueError(ErrorResponse(msg="无效的手机号码", code=-1).model_dump_json())
        return v

# 用户创建（注册）
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="密码")
    confirm_password: str = Field(..., description="确认密码")
    agree_terms: bool = Field(..., description="同意条款")
    
    @field_validator('password')
    def validate_password_strength(cls, v):
        if not PasswordValidator.validate_password_strength(v):
            from app.schemas.response import ErrorResponse
            raise ValueError(ErrorResponse(msg=PasswordValidator.get_password_requirements(), code=-1).model_dump_json())
        return v
    
    @field_validator('confirm_password')
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            from app.schemas.response import ErrorResponse
            raise ValueError(ErrorResponse(msg='两次输入的密码不一致', code=-1).model_dump_json())
        return v
    
    @field_validator('agree_terms')
    def terms_accepted(cls, v):
        if not v:
            from app.schemas.response import ErrorResponse
            raise ValueError(ErrorResponse(msg='必须同意服务条款', code=-1).model_dump_json())
        return v


# 密码修改
class PasswordChange(BaseModel):
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=8, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @field_validator('new_password')
    def validate_new_password(cls, v):
        if not PasswordValidator.validate_password_strength(v):
            from app.schemas.response import ErrorResponse
            raise ValueError(ErrorResponse(msg=PasswordValidator.get_password_requirements(), code=-1).model_dump_json())
        return v
    
    @field_validator('confirm_password')
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            from app.schemas.response import ErrorResponse
            raise ValueError(ErrorResponse(msg='两次输入的新密码不一致', code=-1).model_dump_json())
        return v

# 用户登录
class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")

# 邮箱验证
class EmailVerification(BaseModel):
    email: EmailStr = Field(..., description="电子邮箱")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")

# 手机验证
class PhoneVerification(BaseModel):
    phone: str = Field(..., description="手机号码")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")
    
    @field_validator('phone')
    def validate_phone(cls, v):
        if not PhoneValidator.validate_chinese_phone(v):
            raise HTTPException(
                status_code=400,
                detail="无效的手机号码"
            )
        return v

# 密码重置请求
class PasswordResetRequest(BaseModel):
    email: Optional[EmailStr] = Field(None, description="电子邮箱")
    phone: Optional[str] = Field(None, description="手机号码")
    
    @field_validator('phone')
    def validate_phone(cls, v):
        if v and not PhoneValidator.validate_chinese_phone(v):
            raise HTTPException(
                status_code=400,
                detail="无效的手机号码"
            )
        return v
    
    @model_validator(mode='after')
    def check_at_least_one(self):
        if not self.email and not self.phone:
            raise HTTPException(
                status_code=400,
                detail="必须提供邮箱或手机号"
            )
        return self

# 密码重置
class PasswordReset(BaseModel):
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @field_validator('new_password')
    def validate_new_password(cls, v):
        if not PasswordValidator.validate_password_strength(v):
            raise HTTPException(
                status_code=400,
                detail=PasswordValidator.get_password_requirements()
            )
        return v
    
    @field_validator('confirm_password')
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise HTTPException(
                status_code=400,
                detail="两次输入的新密码不一致"
            )
        return v

# 数据库中的用户模型（响应）
class UserInDB(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 用户响应模型（API返回）
class UserResponse(UserInDB):
    """用户响应模型，继承自UserInDB"""
    pass

# Token 响应
class Token(BaseModel):
    access_token: str
    token_type: str

# Token 数据
class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

# 导出所有模型
__all__ = [
    'UserBase',
    'UserCreate',
    'UserUpdate',
    'UserInDB',
    'UserResponse',
    'UserLogin',
    'PasswordChange',
    'PasswordReset',
    'PasswordResetRequest',
    'EmailVerification',
    'PhoneVerification',
    'Token',
    'TokenData',
]