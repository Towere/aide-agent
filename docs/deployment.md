# 部署指南

## 目录
- [环境要求](#环境要求)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Windows部署](#windows部署)
- [常见问题](#常见问题)

## 环境要求

### 软件依赖

| 软件 | 版本要求 | 用途 |
|------|---------|------|
| Python | 3.9+ | 后端运行环境 |
| Node.js | 16+ | 前端构建环境 |
| Redis | 5.0+ | 缓存和消息队列 |
| MySQL | 8.0+ (可选) | 生产数据库 |
| Git | 最新版 | 代码仓库克隆 |

### 硬件要求

| 配置 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 10GB | 50GB+ |

## 开发环境部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd aide-agent
```

### 2. 后端部署

#### 2.1 创建虚拟环境 (推荐)

```bash
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 2.2 安装Python依赖

```bash
pip install -r requirements.txt
```

依赖列表：
```
fastapi>=0.104.1
uvicorn>=0.24.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
redis>=5.0.1
celery>=5.3.4
python-dotenv>=1.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
gitpython>=3.1.40
python-multipart>=0.0.6
openai>=1.3.7
python-docx>=1.1.0
markdown>=3.5.1
graphviz>=0.20.1
```

#### 2.3 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 服务配置
SERVER_HOST=localhost
SERVER_PORT=7348
DEBUG=True

# 数据库配置 (默认SQLite，无需修改)
DB_TYPE=sqlite
DB_NAME=code_to_paper.db

# 使用MySQL (可选)
# DB_TYPE=mysql
# DB_HOST=localhost
# DB_PORT=3306
# DB_USER=root
# DB_PASSWORD=your_password
# DB_NAME=code_to_paper

# Redis配置 (必须配置)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# 豆包API配置 (必须配置)
ARK_API_KEY=your_api_key_here
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBA_MODEL=your_model_id_here

# 文件存储
UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs
```

#### 2.4 安装并启动Redis

**Windows (使用WSL或Docker):**
```bash
# 方式一：Docker
docker run -d -p 6379:6379 redis:alpine

# 方式二：WSL Ubuntu
wsl
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# CentOS/RHEL
sudo yum install redis
sudo systemctl start redis
```

**Mac:**
```bash
brew install redis
brew services start redis
```

验证Redis连接：
```bash
redis-cli ping
# 返回 PONG 表示正常
```

#### 2.5 启动后端服务

**终端1 - 启动FastAPI:**
```bash
cd backend
python main.py
```

**终端2 - 启动Celery Worker:**
```bash
cd backend
python start_worker.py
```

或使用Celery命令：
```bash
celery -A backend.core.celery.app worker --loglevel=info -Q tasks,default
```

验证后端：
- 访问 http://localhost:7348
- 访问 http://localhost:7348/docs (API文档)

### 3. 前端部署

#### 3.1 安装Node.js依赖

```bash
cd frontend
npm install
```

依赖列表：
```json
{
  "vue": "^3.3.8",
  "element-plus": "^2.4.4",
  "@element-plus/icons-vue": "^2.1.0",
  "axios": "^1.6.2",
  "vite": "^5.0.4",
  "@vitejs/plugin-vue": "^4.5.0"
}
```

#### 3.2 配置API地址

编辑 `vite.config.ts` (默认已配置好):

```typescript
export default defineConfig({
  server: {
    port: 7349,
    proxy: {
      '/api': {
        target: 'http://localhost:7348',
        changeOrigin: true
      }
    }
  }
})
```

#### 3.3 启动开发服务器

```bash
npm run dev
```

访问前端：http://localhost:7349

## 生产环境部署

### 1. 服务器准备

#### 1.1 系统更新

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

#### 1.2 安装基础工具

```bash
# Ubuntu/Debian
sudo apt install -y git curl wget nginx supervisor

# CentOS/RHEL
sudo yum install -y git curl wget nginx supervisor
```

### 2. 后端部署

#### 2.1 使用Gunicorn + Uvicorn Workers

安装Gunicorn：
```bash
pip install gunicorn
```

创建启动脚本 `backend/start_prod.sh`:

```bash
#!/bin/bash
cd /path/to/aide-agent/backend
source venv/bin/activate

# 启动Gunicorn
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:7348 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

#### 2.2 使用Supervisor管理进程

创建 `/etc/supervisor/conf.d/code-to-paper.conf`:

```ini
[program:code-to-paper-api]
directory=/path/to/aide-agent/backend
command=/path/to/aide-agent/backend/venv/bin/gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:7348
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/code-to-paper/api.log
stderr_logfile=/var/log/code-to-paper/api_err.log
environment=PYTHONUNBUFFERED="1"

[program:code-to-paper-worker]
directory=/path/to/aide-agent/backend
command=/path/to/aide-agent/backend/venv/bin/celery -A backend.core.celery.app worker --loglevel=info -Q tasks,default --concurrency=2
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/code-to-paper/worker.log
stderr_logfile=/var/log/code-to-paper/worker_err.log
environment=PYTHONUNBUFFERED="1"
```

启动服务：
```bash
sudo mkdir -p /var/log/code-to-paper
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start code-to-paper-api
sudo supervisorctl start code-to-paper-worker
```

### 3. 前端部署

#### 3.1 构建生产版本

```bash
cd frontend
npm run build
```

构建产物在 `dist/` 目录。

#### 3.2 Nginx配置

创建 `/etc/nginx/sites-available/code-to-paper`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/aide-agent/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # API代理
    location /api {
        proxy_pass http://127.0.0.1:7348;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 文件上传大小限制
    client_max_body_size 100M;

    # 日志
    access_log /var/log/nginx/code-to-paper-access.log;
    error_log /var/log/nginx/code-to-paper-error.log;
}
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/code-to-paper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. MySQL配置 (可选)

#### 4.1 安装MySQL

```bash
# Ubuntu/Debian
sudo apt install mysql-server

# CentOS/RHEL
sudo yum install mysql-server
```

#### 4.2 创建数据库

```sql
CREATE DATABASE code_to_paper CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'code_to_paper'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON code_to_paper.* TO 'code_to_paper'@'localhost';
FLUSH PRIVILEGES;
```

#### 4.3 更新.env配置

```env
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=code_to_paper
DB_PASSWORD=your_password
DB_NAME=code_to_paper
```

### 5. 使用Docker部署 (推荐)

#### 5.1 创建docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:alpine
    container_name: code-to-paper-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  mysql:
    image: mysql:8.0
    container_name: code-to-paper-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: code_to_paper
      MYSQL_USER: code_to_paper
      MYSQL_PASSWORD: db_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  api:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: code-to-paper-api
    restart: unless-stopped
    depends_on:
      - redis
      - mysql
    environment:
      - DB_TYPE=mysql
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_USER=code_to_paper
      - DB_PASSWORD=db_password
      - DB_NAME=code_to_paper
      - REDIS_HOST=redis
      - ARK_API_KEY=${ARK_API_KEY}
      - ARK_BASE_URL=${ARK_BASE_URL}
      - DOUBA_MODEL=${DOUBA_MODEL}
    ports:
      - "7348:7348"
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/outputs:/app/outputs

  worker:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: code-to-paper-worker
    restart: unless-stopped
    depends_on:
      - redis
      - mysql
    environment:
      - DB_TYPE=mysql
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_USER=code_to_paper
      - DB_PASSWORD=db_password
      - DB_NAME=code_to_paper
      - REDIS_HOST=redis
      - ARK_API_KEY=${ARK_API_KEY}
      - ARK_BASE_URL=${ARK_BASE_URL}
      - DOUBA_MODEL=${DOUBA_MODEL}
    command: celery -A backend.core.celery.app worker --loglevel=info -Q tasks,default
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/outputs:/app/outputs

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: code-to-paper-frontend
    restart: unless-stopped
    depends_on:
      - api
    ports:
      - "80:80"

volumes:
  redis_data:
  mysql_data:
```

#### 5.2 创建Dockerfile.backend

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY backend/ .

# 创建必要目录
RUN mkdir -p uploads outputs logs

# 暴露端口
EXPOSE 7348

# 启动命令
CMD ["python", "main.py"]
```

#### 5.3 创建Dockerfile.frontend

```dockerfile
# 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# 生产阶段
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 5.4 启动服务

```bash
# 创建.env文件
cp .env.example .env
# 编辑.env，填写API密钥等配置

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## Windows部署

### 方式一：使用批处理脚本

项目根目录已提供 `start_backend.bat`：

```batch
@echo off
echo Starting Code to Paper Backend...

cd backend

echo Starting FastAPI Server...
start "FastAPI" cmd /k "python main.py"

timeout /t 3 /nobreak >nul

echo Starting Celery Worker...
start "Celery Worker" cmd /k "python start_worker.py"

echo Backend services started!
echo - FastAPI: http://localhost:7348
echo - API Docs: http://localhost:7348/docs
pause
```

使用方法：
1. 双击 `start_backend.bat`
2. 在另一个终端启动前端：`cd frontend && npm run dev`

### 方式二：使用WSL2 (推荐)

1. 安装WSL2：https://docs.microsoft.com/zh-cn/windows/wsl/install
2. 在WSL2中按照Linux部署步骤操作

## 常见问题

### 1. Redis连接失败

**症状**: `Redis 连接失败: Connection refused`

**解决方案**:
```bash
# 检查Redis是否运行
redis-cli ping

# Linux
sudo systemctl status redis
sudo systemctl start redis

# Windows Docker
docker ps
docker start redis-container
```

### 2. 豆包API调用失败

**症状**: `API调用失败: AuthenticationError`

**解决方案**:
- 检查 `.env` 中的 `ARK_API_KEY` 是否正确
- 确认 `DOUBA_MODEL` 模型ID是否正确
- 检查账户余额是否充足

### 3. 前端无法连接后端

**症状**: 前端显示"网络错误"

**解决方案**:
- 确认后端服务正在运行：访问 http://localhost:7348
- 检查 `vite.config.ts` 中的代理配置
- 检查浏览器控制台的具体错误信息

### 4. 文件上传大小限制

**症状**: 上传大文件时报错

**解决方案**:
```python
# FastAPI配置
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    # ...
)

# 或在Nginx中配置
client_max_body_size 100M;
```

### 5. Celery任务不执行

**症状**: 任务一直处于pending状态

**解决方案**:
- 确认Celery Worker正在运行
- 检查Redis连接是否正常
- 查看Worker日志：`celery -A backend.core.celery.app worker --loglevel=debug`

### 6. 数据库迁移

首次启动会自动创建表结构。如需重置：

```bash
# 删除SQLite数据库
rm backend/code_to_paper.db

# 重启后端，会自动重新创建
```

### 7. 端口被占用

**症状**: `Address already in use`

**解决方案**:
```bash
# Windows
netstat -ano | findstr :7348
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:7348 | xargs kill -9
```

## 监控和维护

### 日志查看

```bash
# Supervisor日志
sudo tail -f /var/log/code-to-paper/api.log
sudo tail -f /var/log/code-to-paper/worker.log

# Nginx日志
sudo tail -f /var/log/nginx/code-to-paper-access.log

# Docker日志
docker-compose logs -f api
docker-compose logs -f worker
```

### 备份策略

```bash
# 备份数据库 (MySQL)
mysqldump -u code_to_paper -p code_to_paper > backup_$(date +%Y%m%d).sql

# 备份上传和输出目录
tar -czf backup_files_$(date +%Y%m%d).tar.gz backend/uploads backend/outputs
```

### 性能优化

- 根据服务器配置调整Celery Worker数量 (`--concurrency`)
- 使用MySQL代替SQLite提升性能
- 配置Redis持久化
- 启用Nginx gzip压缩
