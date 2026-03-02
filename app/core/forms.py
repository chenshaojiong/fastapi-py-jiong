from fastapi import Form, File, UploadFile, HTTPException
from typing import Optional, List, Any, Type
from pydantic import BaseModel, Field, field_validator, model_validator
import json

class FormMixin:
    """表单混入类，用于处理表单数据"""
    
    @classmethod
    def as_form(cls, **data):
        """将表单数据转换为Pydantic模型"""
        return cls(**data)
    
    @classmethod
    def from_form_data(cls, form_data: dict):
        """从表单数据创建实例"""
        return cls(**form_data)

class LoginForm(BaseModel, FormMixin):
    """登录表单"""
    username: str
    password: str
    remember_me: bool = False
    
    @classmethod
    def as_form(
        cls,
        username: str = Form(..., description="用户名"),
        password: str = Form(..., description="密码"),
        remember_me: bool = Form(False, description="记住我")
    ):
        return cls(username=username, password=password, remember_me=remember_me)

class RegistrationForm(BaseModel, FormMixin):
    """注册表单"""
    username: str
    email: str
    password: str
    confirm_password: str
    phone: Optional[str] = None
    agree_terms: bool = False
    
    @classmethod
    def as_form(
        cls,
        username: str = Form(..., min_length=3, max_length=50, description="用户名"),
        email: str = Form(..., description="电子邮箱"),
        password: str = Form(..., min_length=8, description="密码"),
        confirm_password: str = Form(..., description="确认密码"),
        phone: Optional[str] = Form(None, description="手机号码"),
        agree_terms: bool = Form(..., description="同意条款")
    ):
        return cls(
            username=username,
            email=email,
            password=password,
            confirm_password=confirm_password,
            phone=phone,
            agree_terms=agree_terms
        )
    
    @field_validator('confirm_password')
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('两次输入的密码不一致')
        return v
    
    @field_validator('agree_terms')
    def terms_accepted(cls, v):
        if not v:
            raise ValueError('必须同意服务条款')
        return v

class ItemForm(BaseModel, FormMixin):
    """商品表单（支持文件上传）"""
    title: str
    description: Optional[str] = None
    price: float
    category: str
    tags: Optional[str] = None  # JSON字符串
    
    @classmethod
    def as_form(
        cls,
        title: str = Form(..., min_length=1, max_length=200, description="商品标题"),
        description: Optional[str] = Form(None, description="商品描述"),
        price: float = Form(..., gt=0, description="商品价格"),
        category: str = Form(..., description="商品分类"),
        tags: Optional[str] = Form(None, description="标签（JSON数组）")
    ):
        return cls(
            title=title,
            description=description,
            price=price,
            category=category,
            tags=tags
        )
    
    def get_tags_list(self) -> List[str]:
        """获取标签列表"""
        if self.tags:
            try:
                return json.loads(self.tags)
            except:
                return []
        return []
    
    @field_validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('价格必须大于0')
        return v

class ProfileForm(BaseModel, FormMixin):
    """用户资料表单"""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    
    @classmethod
    def as_form(
        cls,
        full_name: Optional[str] = Form(None, max_length=100, description="姓名"),
        bio: Optional[str] = Form(None, max_length=500, description="个人简介"),
        birth_date: Optional[str] = Form(None, description="出生日期（YYYY-MM-DD）"),
        gender: Optional[str] = Form(None, pattern="^(男|女|其他)$", description="性别"),
        address: Optional[str] = Form(None, max_length=200, description="地址")
    ):
        return cls(
            full_name=full_name,
            bio=bio,
            birth_date=birth_date,
            gender=gender,
            address=address
        )

class SearchForm(BaseModel, FormMixin):
    """搜索表单"""
    keyword: str
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 20
    
    @classmethod
    def as_form(
        cls,
        keyword: str = Form(..., min_length=1, description="搜索关键词"),
        category: Optional[str] = Form(None, description="商品分类"),
        min_price: Optional[float] = Form(None, ge=0, description="最低价格"),
        max_price: Optional[float] = Form(None, ge=0, description="最高价格"),
        sort_by: str = Form("created_at", description="排序字段"),
        sort_order: str = Form("desc", description="排序方式"),
        page: int = Form(1, ge=1, description="页码"),
        page_size: int = Form(20, ge=1, le=100, description="每页数量")
    ):
        return cls(
            keyword=keyword,
            category=category,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )
    
    @model_validator(mode='after')
    def validate_price_range(self):
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError('最低价格不能高于最高价格')
        return self

# 文件上传表单助手
class FileUploadForm:
    """文件上传表单处理"""
    
    @staticmethod
    async def validate_upload(
        file: UploadFile,
        allowed_extensions: set,
        max_size: int = 10 * 1024 * 1024
    ):
        """验证上传的文件"""
        from app.core.validators import FileValidator
        
        # 验证文件扩展名
        if not FileValidator.validate_file_extension(file.filename, allowed_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。允许的类型: {allowed_extensions}"
            )
        
        # 验证文件大小
        import os
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if not FileValidator.validate_file_size(file_size, max_size):
            raise HTTPException(
                status_code=400,
                detail=f"文件太大。最大允许: {max_size / 1024 / 1024}MB"
            )
        
        return True
    
    @staticmethod
    async def process_images(files: List[UploadFile], max_files: int = 5):
        """处理多图片上传"""
        if len(files) > max_files:
            raise HTTPException(
                status_code=400,
                detail=f"最多只能上传 {max_files} 张图片"
            )
        
        processed_files = []
        for file in files:
            from app.core.validators import FileValidator
            await FileUploadForm.validate_upload(
                file,
                FileValidator.ALLOWED_IMAGE_EXTENSIONS
            )
            processed_files.append(file)
        
        return processed_files