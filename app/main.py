from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import engine, Base
from app.core.exception_handlers import register_exception_handlers
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（用于上传的图片）
os.makedirs("uploads/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# 注册异常处理程序
register_exception_handlers(app)

# 注册路由
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    from app.core import ResponseHandler
    return ResponseHandler.success(data={
        "message": "Welcome to FastAPI Scaffold",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    })

@app.get("/health")
async def health_check():
    from app.core import ResponseHandler
    return ResponseHandler.success(data={"status": "healthy"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )