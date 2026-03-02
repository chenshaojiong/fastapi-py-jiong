from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
from datetime import datetime

from app.core.database import get_db
# from app.core.security import get_current_active_user
from app.api.v1.endpoints.auth import get_current_active_user
from app.schemas.item import (
    ItemCreate, ItemUpdate, ItemResponse, ItemList,
    ItemSearchParams, ItemReview, ItemReviewCreate,
    ItemStatus, ItemCategory
)
from app.schemas.response import SuccessResponse, DataResponse
from app.services.item_service import ItemService
from app.services.user_service import UserService
from app.models.user import User
from app.core.forms import ItemForm, SearchForm, FileUploadForm
from app.core.validators import FileValidator

router = APIRouter()

# 配置文件上传目录
UPLOAD_DIR = "uploads"
IMAGE_DIR = os.path.join(UPLOAD_DIR, "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

@router.post("/", response_model=DataResponse[ItemResponse], status_code=status.HTTP_201_CREATED)
async def create_item(
    form_data: ItemForm = Depends(ItemForm.as_form),
    images: List[UploadFile] = File(None, description="商品图片"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新商品（支持表单和文件上传）"""
    
    # 处理图片上传
    image_urls = []
    if images:
        # 验证图片数量
        if len(images) > 9:
            return ErrorResponse(
                code=2001,
                msg="最多只能上传9张图片"
            )
        
        # 处理每张图片
        for image in images:
            # 验证图片格式
            await FileUploadForm.validate_upload(
                image,
                FileValidator.ALLOWED_IMAGE_EXTENSIONS
            )
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{current_user.id}_{timestamp}_{image.filename}"
            file_path = os.path.join(IMAGE_DIR, filename)
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            # 生成访问URL
            image_url = f"/static/images/{filename}"
            image_urls.append(image_url)
    
    # 创建商品
    item_in = ItemCreate(
        title=form_data.title,
        description=form_data.description,
        price=form_data.price,
        category=form_data.category,
        tags=form_data.get_tags_list(),
        images=image_urls
    )
    
    item = ItemService.create_item(db, item_in, current_user.id)
    
    # 添加所有者信息
    item_response = ItemResponse.model_validate(item)
    item_response.owner_username = current_user.username
    
    return SuccessResponse(
        data=item_response
    )

@router.get("/search", response_model=DataResponse[ItemList])
async def search_items(
    search_params: SearchForm = Depends(SearchForm.as_form),
    db: Session = Depends(get_db)
):
    """搜索商品（表单方式）"""
    # 构建搜索参数
    params = ItemSearchParams(
        keyword=search_params.keyword,
        min_price=search_params.min_price,
        max_price=search_params.max_price,
        sort_by=search_params.sort_by,
        sort_order=search_params.sort_order,
        page=search_params.page,
        page_size=search_params.page_size
    )
    
    # 执行搜索
    result = ItemService.search_items(db, params)
    
    return DataResponse(data=result)
    
@router.post("/{item_id}/reviews", response_model=DataResponse[ItemReview])
async def create_review(
    item_id: int,
    rating: int = Form(..., ge=1, le=5, description="评分"),
    comment: Optional[str] = Form(None, max_length=500, description="评论"),
    images: List[UploadFile] = File(None, description="评论图片"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建商品评论"""
    # 检查商品是否存在
    item = ItemService.get_item(db, item_id)
    if not item:
        return ErrorResponse(
            code=2002,
            msg="商品不存在"
        )
    
    # 处理评论图片
    image_urls = []
    if images:
        for image in images:
            # 验证图片
            await FileUploadForm.validate_upload(
                image,
                FileValidator.ALLOWED_IMAGE_EXTENSIONS
            )
            
            # 保存图片（简化处理）
            filename = f"review_{current_user.id}_{datetime.now().timestamp()}_{image.filename}"
            file_path = os.path.join(IMAGE_DIR, filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            image_urls.append(f"/static/images/{filename}")
    
    # 创建评论
    review_in = ItemReviewCreate(
        rating=rating,
        comment=comment,
        images=image_urls
    )
    
    review = ItemService.create_review(db, item_id, current_user.id, review_in)
    
    return SuccessResponse(
        data=review
    )

@router.post("/{item_id}/favorite")
async def favorite_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """收藏商品"""
    success = ItemService.toggle_favorite(db, item_id, current_user.id)
    
    if not success:
        return ErrorResponse(
            code=2003,
            msg="收藏失败"
        )
    
    return SuccessResponse(
        msg="收藏成功"
    )   

@router.post("/bulk-import")
async def bulk_import_items(
    file: UploadFile = File(..., description="批量导入文件(CSV/Excel)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """批量导入商品"""
    # 验证文件类型
    await FileUploadForm.validate_upload(
        file,
        {'.csv', '.xlsx', '.xls'}
    )
    
    # TODO: 解析文件并批量导入
    # 这里可以实现CSV/Excel解析逻辑
    
    return SuccessResponse(
        msg="批量导入任务已启动"
    )

@router.get("/export", response_model=DataResponse[List[Item]])
async def export_items(
    format: str = Query("csv", regex="^(csv|json)$", description="导出格式"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """导出商品数据"""
    items = ItemService.get_items(db, owner_id=current_user.id)
    
    if format == "csv":
        # 生成CSV
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "标题", "价格", "分类", "状态", "创建时间"])
        
        for item in items:
            writer.writerow([
                item.id, item.title, item.price, 
                item.category, item.status, item.created_at
            ])
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=items_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
    else:
        # 返回JSON
        return DataResponse(
            data=items
        )

from fastapi.responses import Response