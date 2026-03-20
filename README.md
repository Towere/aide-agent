# 代码转论文智能体

输入GitHub项目仓库，自动生成科研论文初稿的AI智能体。

## 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python -m backend.main
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

- 后端: Python + FastAPI
- 前端: Vue3 + Element Plus
- 数据库: MySQL
- 缓存/队列: Redis
- AI: 豆包大模型API
