from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ItemStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SOLD = "sold"
    DELETED = "deleted"

class ItemCategory(str, Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    HOME = "home"
    SPORTS = "sports"
    OTHER = "other"

class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="商品标题")
    description: Optional[str] = Field(None, max_length=2000, description="商品描述")
    price: float = Field(..., gt=0, le=999999.99, description="商品价格")
    category: ItemCategory = Field(..., description="商品分类")
    status: ItemStatus = Field(ItemStatus.DRAFT, description="商品状态")
    stock: int = Field(0, ge=0, le=99999, description="库存数量")
    tags: List[str] = Field(default=[], description="商品标签")
    images: List[str] = Field(default=[], description="商品图片URL")
    attributes: Dict[str, Any] = Field(default={}, description="商品属性")
    
    @validator('title')
    def validate_title(cls, v):
        # 标题不能全是空格
        if not v.strip():
            raise ValueError('标题不能为空')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        # 验证标签格式
        if len(v) > 10:
            raise ValueError('最多只能添加10个标签')
        for tag in v:
            if len(tag) > 20:
                raise ValueError('单个标签不能超过20个字符')
        return v
    
    @validator('images')
    def validate_images(cls, v):
        if len(v) > 9:
            raise ValueError('最多只能上传9张图片')
        return v

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="商品标题")
    description: Optional[str] = Field(None, max_length=2000, description="商品描述")
    price: Optional[float] = Field(None, gt=0, le=999999.99, description="商品价格")
    category: Optional[ItemCategory] = Field(None, description="商品分类")
    status: Optional[ItemStatus] = Field(None, description="商品状态")
    stock: Optional[int] = Field(None, ge=0, le=99999, description="库存数量")
    tags: Optional[List[str]] = Field(None, description="商品标签")
    images: Optional[List[str]] = Field(None, description="商品图片URL")
    attributes: Optional[Dict[str, Any]] = Field(None, description="商品属性")
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('标题不能为空')
        return v.strip() if v else v

class ItemInDB(ItemBase):
    id: int
    owner_id: int
    view_count: int = 0
    favorite_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ItemResponse(ItemInDB):
    owner_username: Optional[str] = None
    owner_avatar: Optional[str] = None
    is_favorited: bool = False

class ItemList(BaseModel):
    total: int
    items: List[ItemResponse]
    page: int
    page_size: int
    total_pages: int

class ItemSearchParams(BaseModel):
    keyword: Optional[str] = Field(None, min_length=1, description="搜索关键词")
    category: Optional[ItemCategory] = Field(None, description="商品分类")
    min_price: Optional[float] = Field(None, ge=0, description="最低价格")
    max_price: Optional[float] = Field(None, ge=0, description="最高价格")
    status: Optional[ItemStatus] = Field(None, description="商品状态")
    tags: Optional[List[str]] = Field(None, description="标签")
    sort_by: str = Field("created_at", pattern="^(created_at|price|view_count|favorite_count)$", description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序方式")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    
    @validator('max_price')
    def validate_price_range(cls, v, values, **kwargs):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('最高价格不能低于最低价格')
        return v

class ItemFavorite(BaseModel):
    item_id: int
    user_id: int
    created_at: datetime

class ItemReview(BaseModel):
    id: int
    item_id: int
    user_id: int
    rating: int = Field(..., ge=1, le=5, description="评分")
    comment: Optional[str] = Field(None, max_length=500, description="评论")
    images: List[str] = Field(default=[], description="评论图片")
    created_at: datetime
    
    class Config:
        from_attributes = True

class ItemReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="评分")
    comment: Optional[str] = Field(None, max_length=500, description="评论")
    images: List[str] = Field(default=[], max_length=3, description="评论图片")