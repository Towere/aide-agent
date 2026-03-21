# 代码转论文智能体

输入GitHub项目仓库，自动生成科研论文初稿的AI智能体。

## 快速开始

### 后端启动

1. 启动 FastAPI 服务器:

```bash
cd backend
pip install -r requirements.txt
python -m backend.main
```

2. 启动 Celery Worker (处理异步任务):

```bash
cd backend
# 方式1: 使用 Python 脚本
python start_worker.py

# 方式2: 使用 Celery 命令
celery -A backend.core.celery.app worker --loglevel=info -Q tasks,default
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

## 配置

复制 `.env.example` 为 `.env` 并填写配置:
- MySQL数据库连接
- Redis连接
- 豆包API密钥

## 技术栈

- 后端: Python + FastAPI + Celery
- 前端: Vue3 + Element Plus
- 数据库: MySQL
- 缓存/队列: Redis (作为 Celery 的消息代理)
- AI: 豆包大模型API
