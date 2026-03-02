from sqlalchemy.orm import Session
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate, ItemSearchParams, ItemResponse
from typing import Optional, List, Dict, Any
from app.core.redis_client import redis_client
import json
from datetime import datetime

class ItemService:
    CACHE_PREFIX = "item:"
    CACHE_EXPIRE = 3600  # 1小时
    
    @staticmethod
    def _get_cache_key(item_id: int) -> str:
        return f"{ItemService.CACHE_PREFIX}{item_id}"
    
    @staticmethod
    def get_item(db: Session, item_id: int) -> Optional[Item]:
        """获取单个商品"""
        # 尝试从缓存获取
        cache_key = ItemService._get_cache_key(item_id)
        cached_item = redis_client.get(cache_key)
        
        if cached_item:
            return Item(**cached_item)
        
        # 从数据库获取
        item = db.query(Item).filter(Item.id == item_id).first()
        if item:
            # 存入缓存
            redis_client.set(cache_key, {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "price": item.price,
                "is_active": item.is_active,
                "owner_id": item.owner_id
            }, ItemService.CACHE_EXPIRE)
        
        return item
    
    @staticmethod
    def get_items(db: Session, owner_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Item]:
        """获取商品列表"""
        query = db.query(Item)
        if owner_id:
            query = query.filter(Item.owner_id == owner_id)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def create_item(db: Session, item: ItemCreate, owner_id: int) -> Item:
        """创建商品"""
        db_item = Item(**item.model_dump(), owner_id=owner_id)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        # 缓存新创建的商品
        cache_key = ItemService._get_cache_key(db_item.id)
        redis_client.set(cache_key, {
            "id": db_item.id,
            "title": db_item.title,
            "description": db_item.description,
            "price": db_item.price,
            "is_active": db_item.is_active,
            "owner_id": db_item.owner_id
        }, ItemService.CACHE_EXPIRE)
        
        return db_item
    
    @staticmethod
    def update_item(db: Session, item_id: int, item_update: ItemUpdate, owner_id: int) -> Optional[Item]:
        """更新商品"""
        db_item = db.query(Item).filter(Item.id == item_id, Item.owner_id == owner_id).first()
        if db_item:
            update_data = item_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_item, field, value)
            
            db.commit()
            db.refresh(db_item)
            
            # 更新缓存
            cache_key = ItemService._get_cache_key(item_id)
            redis_client.delete(cache_key)
            redis_client.set(cache_key, {
                "id": db_item.id,
                "title": db_item.title,
                "description": db_item.description,
                "price": db_item.price,
                "is_active": db_item.is_active,
                "owner_id": db_item.owner_id
            }, ItemService.CACHE_EXPIRE)
        
        return db_item
    
    @staticmethod
    def delete_item(db: Session, item_id: int, owner_id: int) -> bool:
        """删除商品"""
        db_item = db.query(Item).filter(Item.id == item_id, Item.owner_id == owner_id).first()
        if db_item:
            db.delete(db_item)
            db.commit()
            
            # 删除缓存
            cache_key = ItemService._get_cache_key(item_id)
            redis_client.delete(cache_key)
            return True
        return False
    
    @staticmethod
    def search_items(db: Session, params: ItemSearchParams) -> Dict[str, Any]:
        """搜索商品"""
        query = db.query(Item)
        
        # 关键词搜索
        if params.keyword:
            query = query.filter(
                Item.title.contains(params.keyword) | 
                Item.description.contains(params.keyword)
            )
        
        # 价格范围
        if params.min_price is not None:
            query = query.filter(Item.price >= params.min_price)
        if params.max_price is not None:
            query = query.filter(Item.price <= params.max_price)
        
        # 分类
        if params.category:
            query = query.filter(Item.category == params.category)
        
        # 状态
        if params.status:
            query = query.filter(Item.status == params.status)
        
        # 标签
        if params.tags:
            for tag in params.tags:
                query = query.filter(Item.tags.contains([tag]))
        
        # 计算总数
        total = query.count()
        
        # 排序
        sort_field = getattr(Item, params.sort_by)
        if params.sort_order == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
        
        # 分页
        items = query.offset((params.page - 1) * params.page_size).limit(params.page_size).all()
        
        # 转换为响应格式
        item_responses = []
        for item in items:
            item_response = ItemResponse.model_validate(item)
            if item.owner:
                item_response.owner_username = item.owner.username
            item_responses.append(item_response)
        
        return {
            "total": total,
            "items": item_responses,
            "page": params.page,
            "page_size": params.page_size,
            "total_pages": (total + params.page_size - 1) // params.page_size
        }
    
    @staticmethod
    def create_review(db: Session, item_id: int, user_id: int, review_in: Any):
        """创建商品评论"""
        # TODO: 实现评论功能
        pass
    
    @staticmethod
    def toggle_favorite(db: Session, item_id: int, user_id: int) -> bool:
        """切换收藏状态"""
        # TODO: 实现收藏功能
        return True