# 代码转论文智能体 (Code to Paper Agent)

输入GitHub项目仓库或ZIP代码文件，自动生成科研论文初稿的AI智能体系统。

## 功能特性

- 🤖 **多智能体流水线**: 代码解析 → 实验分析 → 论文生成，三阶段智能协作
- 📦 **多种输入方式**: 支持Git仓库URL和ZIP文件上传
- 📝 **多语言输出**: 支持英文、中文、双语三种论文语言
- 🎨 **自定义模板**: 支持上传自定义论文模板配置
- 📊 **系统架构图**: 自动生成项目架构可视化图表
- 📄 **多格式导出**: 支持Markdown和Word (DOCX) 两种格式
- ⚡ **异步处理**: 基于Celery + Redis的异步任务队列，实时进度跟踪
- 📋 **任务历史**: 保存历史任务，方便查看和复用

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| **后端框架** | FastAPI 0.104+ |
| **前端框架** | Vue 3.3 + Element Plus |
| **数据库** | SQLite (默认) / MySQL |
| **缓存/队列** | Redis 5.0+ |
| **异步任务** | Celery 5.3+ |
| **AI模型** | 字节跳动豆包大模型 API |
| **文档生成** | python-docx |

## 项目结构

```
aide-agent/
├── backend/                 # 后端服务
│   ├── agents/             # 多智能体模块
│   │   ├── code_parser.py        # 代码解析Agent
│   │   ├── experiment_analyzer.py # 实验分析Agent
│   │   ├── paper_generator.py     # 论文生成Agent
│   │   ├── structure_generator.py # 结构生成Agent
│   │   ├── content_optimizer.py   # 内容优化Agent
│   │   ├── diagram_generator.py   # 图表生成Agent
│   │   └── diagram_integrator.py  # 图表集成Agent
│   ├── api/                # API接口
│   │   ├── routes.py             # API路由
│   │   └── schemas.py            # 数据模型
│   ├── core/               # 核心配置
│   │   ├── config.py             # 配置管理
│   │   ├── database.py           # 数据库连接
│   │   ├── redis_client.py       # Redis连接
│   │   └── celery.py             # Celery配置
│   ├── services/           # 业务服务
│   │   ├── task_service.py       # 任务管理
│   │   ├── code_fetcher.py       # 代码获取
│   │   └── worker.py             # 任务执行
│   ├── formatters/         # 格式化模块
│   │   ├── docx_formatter.py     # Word文档生成
│   │   └── template_manager.py   # 模板管理
│   ├── utils/              # 工具函数
│   │   ├── file_utils.py         # 文件处理
│   │   └── llm_client.py         # LLM客户端
│   └── main.py             # 服务入口
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── views/Home.vue        # 主页面
│   │   ├── api/index.ts          # API封装
│   │   └── components/           # 组件
│   └── package.json
│
└── docs/                   # 项目文档
    ├── architecture.md     # 架构说明
    ├── deployment.md       # 部署指南
    └── api.md              # API文档
```

## 快速开始

### 前置要求

- Python 3.9+
- Node.js 16+
- Redis 5.0+

### 1. 克隆项目

```bash
git clone <repository-url>
cd aide-agent
```

### 2. 配置环境变量

复制环境变量模板并配置：

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，填写你的配置
```

必要配置项：
```env
# 服务配置
SERVER_HOST=localhost
SERVER_PORT=7348

# Redis（必须配置）
REDIS_HOST=localhost
REDIS_PORT=6379

# 豆包API（必须配置）
ARK_API_KEY=your_api_key
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBA_MODEL=your_model_id
```

### 3. 启动后端服务

**方式一：使用启动脚本（Windows）**

```bash
# 在项目根目录
start_backend.bat
```

**方式二：手动启动**

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动 FastAPI 服务器
python main.py

# 在另一个终端启动 Celery Worker
python start_worker.py
```

### 4. 启动前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 5. 访问应用

- 前端界面: http://localhost:7349
- 后端API: http://localhost:7348
- API文档: http://localhost:7348/docs

## 使用说明

### 创建论文任务

1. 打开前端界面
2. 选择输入方式：
   - **Git URL**: 输入GitHub仓库地址
   - **ZIP上传**: 上传代码压缩包
3. 选择论文语言：英文、中文或双语
4. （可选）上传自定义 `paper_template.json` 模板
5. 点击"生成论文"

### 任务状态说明

| 状态 | 说明 |
|------|------|
| `pending` | 任务已创建，等待处理 |
| `parsing_code` | 正在解析代码仓库 |
| `analyzing_experiment` | 正在分析实验配置 |
| `generating_structure` | 正在生成论文结构 |
| `generating_paper` | 正在生成论文内容 |
| `optimizing_content` | 正在优化论文内容 |
| `generating_diagrams` | 正在生成架构图表 |
| `integrating_diagrams` | 正在集成图表 |
| `formatting_paper` | 正在格式化论文 |
| `completed` | 任务完成 |
| `failed` | 任务失败 |

### 下载论文

任务完成后，可以下载：
- **Markdown格式**: 便于编辑和版本控制
- **Word格式**: 便于排版和提交

## 文档索引

- [架构说明](docs/architecture.md) - 系统架构、模块设计、Agent流水线详解
- [部署指南](docs/deployment.md) - 详细的环境配置和部署步骤
- [API文档](docs/api.md) - RESTful API接口说明
- [CLAUDE.md](CLAUDE.md) - 项目开发规范

## 开发规范

本项目遵循 [CLAUDE.md](CLAUDE.md) 开发规范，主要原则：

- 优先支持计算机类项目，先跑通最小闭环
- 禁止在MVP阶段开发超出需求的功能
- 统一接口返回格式、异常处理逻辑
- 复用现有工具类，禁止重复编写通用代码

## 许可证

Copyright © 2026

## 贡献

欢迎提交 Issue 和 Pull Request！
