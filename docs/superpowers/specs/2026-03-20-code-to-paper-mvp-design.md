# 代码转论文智能体 MVP 设计文档

**日期**: 2026-03-20
**版本**: 1.0
**状态**: 设计中

## 1. 项目概述

### 1.1 目标
构建一个输入GitHub项目仓库，自动生成科研论文初稿的AI智能体，辅助科研人员快速生成论文草稿。

### 1.2 范围
- **MVP范围**: 优先支持计算机类项目，跑通最小闭环
- **非MVP范围**: 用户系统、在线编辑、多版本对比、LaTeX输出、非计算机类项目

## 2. 整体架构

### 2.1 系统架构图

```
┌─────────────────┐
│   Frontend      │  Vue3 + Element Plus
│  (Web UI)       │
└────────┬────────┘
         │
┌────────▼────────┐
│  FastAPI Backend│  API Gateway + Task Queue
│                 │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Redis   │  Task Queue + Cache
    └────┬────┘
         │
┌────────▼─────────────────────────────┐
│          Agent Pipeline               │
│  ┌──────────┐    ┌──────────┐    ┌─┴────────┐
│  │Code Parse│───▶│Experiment│───▶│Paper Gen │
│  │  Agent   │    │  Analyze │    │  Agent   │
│  └──────────┘    │  Agent   │    └──────────┘
│                   └──────────┘
└──────────────────────────────────────┘
         │
┌────────▼────────┐
│  MySQL Database │  Task Status + Results
└─────────────────┘
```

### 2.2 核心组件

| 组件 | 技术栈 | 职责 |
|------|--------|------|
| Frontend | Vue3 + Element Plus | 用户界面：上传代码、查看进度、下载论文 |
| Backend | FastAPI | API网关、任务管理、状态查询 |
| Redis | Redis | 任务队列、进度缓存 |
| Agent Pipeline | Python + 豆包API | 三智能体串行处理 |
| Database | MySQL | 持久化任务信息和结果 |

## 3. 目录结构

### 3.1 后端目录结构

```
backend/
├── main.py                 # FastAPI入口
├── api/
│   ├── __init__.py
│   ├── routes.py           # API路由定义
│   └── schemas.py          # Pydantic模型
├── agents/
│   ├── __init__.py
│   ├── base.py             # Agent基类
│   ├── code_parser.py      # 代码解析Agent
│   ├── experiment_analyzer.py # 实验分析Agent
│   └── paper_generator.py  # 论文生成Agent
├── adapters/
│   ├── __init__.py
│   ├── repo_agent.py       # RepoAgent适配层
│   └── rd_agent.py         # RD-Agent适配层
├── core/
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库连接
│   └── redis_client.py     # Redis连接
├── services/
│   ├── __init__.py
│   ├── task_service.py     # 任务管理服务
│   ├── code_fetcher.py     # 代码获取（git clone/zip解压）
│   └── worker.py           # 异步任务Worker
├── models/
│   ├── __init__.py
│   └── task.py             # 数据库模型
└── utils/
    ├── __init__.py
    ├── file_utils.py       # 文件处理
    └── llm_client.py       # 豆包API客户端
```

### 3.2 前端目录结构

```
frontend/
├── public/
├── src/
│   ├── api/
│   │   └── index.ts        # API请求封装
│   ├── components/
│   │   ├── TaskForm.vue    # 任务创建表单
│   │   └── TaskStatus.vue  # 任务状态展示
│   ├── views/
│   │   └── Home.vue        # 主页面
│   ├── App.vue
│   └── main.ts
├── package.json
└── vite.config.ts
```

## 4. API设计

### 4.1 API端点

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/tasks` | 创建论文生成任务 |
| GET | `/api/tasks/{task_id}` | 获取任务状态和结果 |
| GET | `/api/tasks/{task_id}/download` | 下载生成的论文 |

### 4.2 请求/响应示例

**POST /api/tasks**
```json
{
  "input_type": "git_url",
  "input_source": "https://github.com/user/repo.git"
}
```
或
```json
{
  "input_type": "zip_upload",
  "file": "[binary]"
}
```

**响应:**
```json
{
  "task_id": "uuid-string",
  "status": "pending",
  "created_at": "2026-03-20T10:00:00Z"
}
```

**GET /api/tasks/{task_id}**
```json
{
  "task_id": "uuid-string",
  "status": "generating_paper",
  "progress": 65,
  "created_at": "2026-03-20T10:00:00Z",
  "updated_at": "2026-03-20T10:15:00Z",
  "paper_content": null,
  "error_message": null
}
```

## 5. 数据模型

### 5.1 Task模型

```python
id: UUID
status: Enum[pending, parsing_code, analyzing_experiment, generating_paper, completed, failed]
input_type: Enum[git_url, zip_upload]
input_source: String  # git URL或文件路径
progress: Integer  # 0-100
code_analysis: JSON  # 代码解析结果
experiment_analysis: JSON  # 实验分析结果
paper_content: Text  # 生成的论文Markdown
error_message: Text  # 错误信息
created_at: DateTime
updated_at: DateTime
```

### 5.2 任务状态流转

```
pending → parsing_code → analyzing_experiment → generating_paper → completed
                                                         ↓
                                                      failed
```

## 6. 三智能体流水线设计

### 6.1 Code Parser Agent（代码解析Agent）

- **输入**: 代码仓库路径
- **输出**: 结构化JSON
  ```json
  {
    "project_overview": {
      "name": "项目名称",
      "description": "项目描述",
      "tech_stack": ["Python", "PyTorch", "..."]
    },
    "structure": {
      "modules": [],
      "key_files": []
    },
    "algorithms": [],
    "dependencies": []
  }
  ```
- **实现**: 封装RepoAgent适配层

### 6.2 Experiment Analyzer Agent（实验分析Agent）

- **输入**: 代码解析结果 + 代码仓库
- **输出**: 结构化JSON
  ```json
  {
    "experiment_setup": {},
    "metrics": [],
    "results": {},
    "baselines": [],
    "conclusion": ""
  }
  ```
- **实现**: 查找实验脚本、配置文件、结果日志；封装RD-Agent适配层

### 6.3 Paper Generator Agent（论文生成Agent）

- **输入**: 代码解析 + 实验分析
- **输出**: 完整论文Markdown
- **论文章节**:
  1. 摘要 (Abstract)
  2. 引言 (Introduction)
  3. 相关工作 (Related Work)
  4. 方法 (Methodology)
  5. 实验 (Experiments)
  6. 结论 (Conclusion)
  7. 参考文献 (References)
- **实现**: 调用豆包API，按章节逐步生成

## 7. 错误处理

### 7.1 错误处理策略

- 每个Agent失败时记录详细错误信息到数据库
- 支持任务重试（从失败的Agent步骤继续）
- 超时处理：单个Agent执行超时设为30分钟
- 用户友好的错误提示

### 7.2 日志

- 任务全流程日志记录
- Agent执行细节日志
- 错误堆栈跟踪

## 8. 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 前端框架 | Vue3 + Element Plus |
| 数据库 | MySQL |
| 缓存/队列 | Redis |
| AI | 豆包大模型API |
| 开源模块 | RepoAgent、RD-Agent（封装适配层） |

## 9. MVP功能确认

### 包含功能
- ✅ 支持计算机类项目
- ✅ 支持git clone和zip上传两种输入方式
- ✅ 异步任务处理 + 进度查询
- ✅ 三智能体流水线
- ✅ 封装RepoAgent/RD-Agent适配层
- ✅ 输出完整Markdown格式论文
- ✅ 仅需代码输入，自动分析

### 暂不包含
- ❌ 用户登录/权限系统
- ❌ 论文在线编辑
- ❌ 多版本对比
- ❌ LaTeX输出
- ❌ 非计算机类项目支持

## 10. 开发顺序

1. 后端核心API（优先）
   - 项目脚手架
   - 数据库模型
   - API端点
   - 代码获取服务
   - 异步任务Worker

2. 三智能体实现
   - Agent基类
   - 代码解析Agent（RepoAgent适配）
   - 实验分析Agent（RD-Agent适配）
   - 论文生成Agent（豆包API）

3. 前端界面
   - 项目脚手架
   - 任务创建表单
   - 进度展示
   - 论文下载

