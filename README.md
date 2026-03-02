安装和运行
克隆项目并安装依赖

bash
# 创建项目目录
mkdir fastapi-scaffold
cd fastapi-scaffold

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
配置环境变量

bash
cp .env.example .env
# 编辑.env文件，修改数据库和Redis配置
使用Docker运行（推荐）

bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down


本地运行

bash
# 启动MySQL和Redis（需要先安装）
# 然后启动FastAPI应用
uvicorn app.main:app --reload

# 在另一个终端启动Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# 如果需要定时任务，启动Celery Beat
celery -A app.core.celery_app beat --loglevel=info
API文档
启动应用后，访问：

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

测试API
注册用户

bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
登录获取Token

bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
创建商品（需要Token）

bash
curl -X POST "http://localhost:8000/api/v1/items/" \
  -H "Authorization: Bear


  表单验证特性
多种验证器：

密码强度验证（大小写字母、数字、特殊字符）

手机号验证（中国大陆）

身份证验证（18位，含校验码）

用户名格式验证

邮箱域名验证

日期和年龄验证

文件类型和大小验证

表单处理：

支持 application/x-www-form-urlencoded

支持 multipart/form-data（文件上传）

自动验证和转换

自定义错误消息

文件上传：

多文件上传支持

文件类型验证

文件大小限制

自动保存和URL生成

测试API示例
bash
# 1. 使用表单注册
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&email=test@example.com&password=Test@1234&confirm_password=Test@1234&agree_terms=true"

# 2. 使用表单登录（带remember_me）
curl -X POST "http://localhost:8000/api/v1/auth/login/form" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=Test@1234&remember_me=true"

# 3. 创建商品（带图片上传）
curl -X POST "http://localhost:8000/api/v1/items/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=测试商品" \
  -F "description=商品描述" \
  -F "price=99.99" \
  -F "category=electronics" \
  -F "tags=[\"手机\",\"数码\"]" \
  -F "images=@/path/to/image1.jpg" \
  -F "images=@/path/to/image2.jpg"

# 4. 搜索商品
curl -X POST "http://localhost:8000/api/v1/items/search" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "keyword=手机&min_price=100&max_price=1000&sort_by=price&sort_order=asc&page=1&page_size=20"
这个脚手架现在包含了完整的表单验证功能，支持：

多种数据类型的验证

文件上传和验证

表单数据自动转换

自定义验证规则

详细的错误信息

与现有JWT认证和数据库完美集成