from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.item_service import ItemService
from app.core.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def cleanup_inactive_items():
    """清理不活跃的商品（示例任务）"""
    db = SessionLocal()
    try:
        items = ItemService.get_items(db)
        inactive_count = 0
        for item in items:
            if not item.is_active:
                # 可以在这里添加清理逻辑
                logger.info(f"清理不活跃商品: {item.id} - {item.title}")
                inactive_count += 1
        
        logger.info(f"清理完成，共发现 {inactive_count} 个不活跃商品")
        return f"Cleaned up {inactive_count} inactive items"
    finally:
        db.close()

@celery_app.task
def sync_item_to_external_system(item_id: int):
    """同步商品到外部系统（示例任务）"""
    db = SessionLocal()
    try:
        item = ItemService.get_item(db, item_id)
        if item:
            # 模拟同步到外部系统
            logger.info(f"同步商品 {item_id} 到外部系统")
            # 这里添加实际的同步逻辑
            return f"Item {item_id} synced successfully"
        else:
            logger.error(f"商品 {item_id} 不存在")
            return f"Item {item_id} not found"
    finally:
        db.close()

@celery_app.task
def generate_item_report():
    """生成商品报告（示例定时任务）"""
    db = SessionLocal()
    try:
        items = ItemService.get_items(db)
        total_items = len(items)
        active_items = sum(1 for item in items if item.is_active)
        
        report = {
            "total_items": total_items,
            "active_items": active_items,
            "inactive_items": total_items - active_items,
            "generated_at": str(datetime.now())
        }
        
        # 存储报告到Redis
        redis_client.set("item_report", report, 3600)
        
        logger.info(f"商品报告生成完成: {report}")
        return report
    finally:
        db.close()

from datetime import datetime