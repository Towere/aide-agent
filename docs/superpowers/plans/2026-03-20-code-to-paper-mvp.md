# 代码转论文智能体 MVP 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个输入GitHub项目仓库，自动生成科研论文初稿的完整MVP系统

**Architecture:** 三智能体流水线架构，FastAPI后端 + Vue3前端，异步任务处理

**Tech Stack:** Python 3.9+, FastAPI, Vue3, Element Plus, MySQL, Redis, 豆包API

---

## 阶段一：项目脚手架与基础配置

### Task 1: 创建项目目录结构

**Files:**
- Create: `backend/`
- Create: `frontend/`
- Create: `backend/api/`
- Create: `backend/agents/`
- Create: `backend/adapters/`
- Create: `backend/core/`
- Create: `backend/services/`
- Create: `backend/models/`
- Create: `backend/utils/`

- [ ] **Step 1: 创建后端目录结构**
  ```bash
  mkdir -p backend/{api,agents,adapters,core,services,models,utils}
  mkdir -p frontend/src/{api,components,views}
  ```

- [ ] **Step 2: 创建后端 __init__.py 文件**
  ```bash
  touch backend/__init__.py
  touch backend/api/__init__.py
  touch backend/agents/__init__.py
  touch backend/adapters/__init__.py
  touch backend/core/__init__.py
  touch backend/services/__init__.py
  touch backend/models/__init__.py
  touch backend/utils/__init__.py
  ```

---

### Task 2: 创建后端依赖配置

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`

- [ ] **Step 1: 创建 requirements.txt**
  ```txt
  fastapi==0.104.1
  uvicorn[standard]==0.24.0
  sqlalchemy==2.0.23
  pymysql==1.1.0
  cryptography==41.0.7
  redis==5.0.1
  celery==5.3.4
  python-dotenv==1.0.0
  pydantic==2.5.2
  pydantic-settings==2.1.0
  python-multipart==0.0.6
  gitpython==3.1.40
  openai==1.3.7
  ```

- [ ] **Step 2: 创建 .env.example**
  ```env
  # 服务配置
  SERVER_HOST=localhost
  SERVER_PORT=7348
  DEBUG=True

  # MySQL
  DB_HOST=localhost
  DB_PORT=3306
  DB_USER=root
  DB_PASSWORD=123456
  DB_NAME=code_to_paper

  # Redis
  REDIS_HOST=localhost
  REDIS_PORT=6379
  REDIS_PASSWORD=
  REDIS_DB=0

  # 豆包API
  ARK_API_KEY=your_api_key
  ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
  DOUBA_MODEL=ep-20260315170036-qb56q

  # 文件存储
  UPLOAD_DIR=./uploads
  ```

---

### Task 3: 核心配置模块

**Files:**
- Create: `backend/core/config.py`

- [ ] **Step 1: 编写配置管理代码**
  ```python
  from pydantic_settings import BaseSettings
  from typing import List
  import os

  class Settings(BaseSettings):
      # Server
      server_host: str = "localhost"
      server_port: int = 7348
      debug: bool = True

      # Database
      db_host: str = "localhost"
      db_port: int = 3306
      db_user: str = "root"
      db_password: str = ""
      db_name: str = "code_to_paper"

      # Redis
      redis_host: str = "localhost"
      redis_port: int = 6379
      redis_password: str = ""
      redis_db: int = 0

      # LLM
      ark_api_key: str = ""
      ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
      doubao_model: str = ""

      # File storage
      upload_dir: str = "./uploads"
      output_dir: str = "./outputs"

      @property
      def database_url(self) -> str:
          return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

      @property
      def redis_url(self) -> str:
          if self.redis_password:
              return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
          return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

      model_config = {
          "env_file": ".env",
          "case_sensitive": False,
      }

  settings = Settings()

  # Create directories
  os.makedirs(settings.upload_dir, exist_ok=True)
  os.makedirs(settings.output_dir, exist_ok=True)
  ```

---

### Task 4: 数据库连接模块

**Files:**
- Create: `backend/core/database.py`

- [ ] **Step 1: 编写数据库连接代码**
  ```python
  from sqlalchemy import create_engine
  from sqlalchemy.ext.declarative import declarative_base
  from sqlalchemy.orm import sessionmaker
  from .config import settings

  engine = create_engine(
      settings.database_url,
      pool_pre_ping=True,
      pool_recycle=3600,
      echo=settings.debug
  )

  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

  Base = declarative_base()

  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```

---

### Task 5: Redis连接模块

**Files:**
- Create: `backend/core/redis_client.py`

- [ ] **Step 1: 编写Redis连接代码**
  ```python
  import redis
  from .config import settings

  redis_client = redis.from_url(
      settings.redis_url,
      decode_responses=True,
      socket_connect_timeout=5,
      socket_keepalive=True
  )

  def get_redis():
      return redis_client
  ```

---

## 阶段二：数据模型与API基础

### Task 6: 数据库模型 - Task

**Files:**
- Create: `backend/models/task.py`

- [ ] **Step 1: 编写Task模型**
  ```python
  from sqlalchemy import Column, String, Text, Integer, DateTime, Enum as SQLEnum, JSON
  from sqlalchemy.dialects.mysql import CHAR
  from datetime import datetime
  import enum
  import uuid
  from backend.core.database import Base

  class TaskStatus(str, enum.Enum):
      PENDING = "pending"
      PARSING_CODE = "parsing_code"
      ANALYZING_EXPERIMENT = "analyzing_experiment"
      GENERATING_PAPER = "generating_paper"
      COMPLETED = "completed"
      FAILED = "failed"

  class InputType(str, enum.Enum):
      GIT_URL = "git_url"
      ZIP_UPLOAD = "zip_upload"

  class Task(Base):
      __tablename__ = "tasks"

      id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
      status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
      input_type = Column(SQLEnum(InputType), nullable=False)
      input_source = Column(String(500), nullable=False)
      repo_path = Column(String(500), nullable=True)

      progress = Column(Integer, default=0)

      code_analysis = Column(JSON, nullable=True)
      experiment_analysis = Column(JSON, nullable=True)
      paper_content = Column(Text, nullable=True)

      error_message = Column(Text, nullable=True)

      created_at = Column(DateTime, default=datetime.utcnow, index=True)
      updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

      def to_dict(self):
          return {
              "id": self.id,
              "status": self.status.value if self.status else None,
              "input_type": self.input_type.value if self.input_type else None,
              "input_source": self.input_source,
              "progress": self.progress,
              "paper_content": self.paper_content,
              "error_message": self.error_message,
              "created_at": self.created_at.isoformat() if self.created_at else None,
              "updated_at": self.updated_at.isoformat() if self.updated_at else None,
          }
  ```

---

### Task 7: API Schema定义

**Files:**
- Create: `backend/api/schemas.py`

- [ ] **Step 1: 编写Pydantic模型**
  ```python
  from pydantic import BaseModel, Field
  from typing import Optional
  from datetime import datetime
  from enum import Enum

  class TaskStatus(str, Enum):
      PENDING = "pending"
      PARSING_CODE = "parsing_code"
      ANALYZING_EXPERIMENT = "analyzing_experiment"
      GENERATING_PAPER = "generating_paper"
      COMPLETED = "completed"
      FAILED = "failed"

  class InputType(str, Enum):
      GIT_URL = "git_url"
      ZIP_UPLOAD = "zip_upload"

  class TaskCreateRequest(BaseModel):
      input_type: InputType
      input_source: Optional[str] = None

  class TaskResponse(BaseModel):
      id: str
      status: TaskStatus
      progress: int
      created_at: datetime
      updated_at: datetime
      paper_content: Optional[str] = None
      error_message: Optional[str] = None

  class MessageResponse(BaseModel):
      message: str
  ```

---

### Task 8: LLM客户端工具

**Files:**
- Create: `backend/utils/llm_client.py`

- [ ] **Step 1: 编写豆包API客户端**
  ```python
  from openai import OpenAI
  from typing import List, Dict, Any, Optional
  from backend.core.config import settings
  import json

  class LLMClient:
      def __init__(self):
          self.client = OpenAI(
              api_key=settings.ark_api_key,
              base_url=settings.ark_base_url
          )
          self.model = settings.doubao_model

      def chat(
          self,
          messages: List[Dict[str, str]],
          temperature: float = 0.7,
          max_tokens: int = 4000,
          **kwargs
      ) -> str:
          try:
              response = self.client.chat.completions.create(
                  model=self.model,
                  messages=messages,
                  temperature=temperature,
                  max_tokens=max_tokens,
                  **kwargs
              )
              return response.choices[0].message.content
          except Exception as e:
              raise Exception(f"LLM调用失败: {str(e)}")

      def chat_with_system_prompt(
          self,
          user_prompt: str,
          system_prompt: str = "你是一个有用的助手。",
          temperature: float = 0.7,
          max_tokens: int = 4000
      ) -> str:
          messages = [
              {"role": "system", "content": system_prompt},
              {"role": "user", "content": user_prompt}
          ]
          return self.chat(messages, temperature, max_tokens)

      def extract_json(self, text: str) -> Optional[Dict[str, Any]]:
          try:
              text = text.strip()
              if text.startswith("```json"):
                  text = text[7:]
              if text.endswith("```"):
                  text = text[:-3]
              return json.loads(text.strip())
          except Exception:
              return None

  llm_client = LLMClient()
  ```

---

### Task 9: 文件处理工具

**Files:**
- Create: `backend/utils/file_utils.py`

- [ ] **Step 1: 编写文件处理工具**
  ```python
  import os
  import zipfile
  import shutil
  from typing import Optional
  from backend.core.config import settings
  import uuid

  def get_unique_upload_dir() -> str:
      task_id = str(uuid.uuid4())
      dir_path = os.path.join(settings.upload_dir, task_id)
      os.makedirs(dir_path, exist_ok=True)
      return dir_path, task_id

  def save_uploaded_file(file_bytes: bytes, filename: str, target_dir: str) -> str:
      file_path = os.path.join(target_dir, filename)
      with open(file_path, "wb") as f:
          f.write(file_bytes)
      return file_path

  def extract_zip(zip_path: str, extract_to: str) -> str:
      repo_name = os.path.splitext(os.path.basename(zip_path))[0]
      repo_dir = os.path.join(extract_to, repo_name)
      os.makedirs(repo_dir, exist_ok=True)

      with zipfile.ZipFile(zip_path, 'r') as zip_ref:
          zip_ref.extractall(repo_dir)

      return repo_dir

  def cleanup_directory(dir_path: str):
      if os.path.exists(dir_path):
          shutil.rmtree(dir_path, ignore_errors=True)

  def read_file_safe(file_path: str, max_size: int = 10 * 1024 * 1024) -> Optional[str]:
      try:
          if os.path.getsize(file_path) > max_size:
              return None
          with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
              return f.read()
      except Exception:
          return None

  def find_readme(repo_dir: str) -> Optional[str]:
      readme_names = ['README.md', 'README', 'readme.md', 'Readme.md']
      for name in readme_names:
          path = os.path.join(repo_dir, name)
          if os.path.exists(path):
              return path
      return None
  ```

---

## 阶段三：代码获取服务

### Task 10: Git克隆服务

**Files:**
- Create: `backend/services/code_fetcher.py`

- [ ] **Step 1: 编写代码获取服务**
  ```python
  import os
  import git
  from typing import Optional, Tuple
  from backend.core.config import settings
  from backend.utils import file_utils
  import shutil

  class CodeFetcher:
      @staticmethod
      def clone_git_repo(git_url: str, target_dir: str) -> Tuple[str, str]:
          repo_name = git_url.split("/")[-1].replace(".git", "")
          repo_dir = os.path.join(target_dir, repo_name)

          if os.path.exists(repo_dir):
              shutil.rmtree(repo_dir)

          try:
              git.Repo.clone_from(git_url, repo_dir, depth=1)
              return repo_dir, repo_name
          except Exception as e:
              raise Exception(f"Git clone失败: {str(e)}")

      @staticmethod
      def process_zip_upload(zip_path: str, target_dir: str) -> Tuple[str, str]:
          repo_dir = file_utils.extract_zip(zip_path, target_dir)
          repo_name = os.path.basename(repo_dir)
          return repo_dir, repo_name

      @staticmethod
      def scan_repo_structure(repo_dir: str) -> dict:
          structure = {
              "files": [],
              "directories": [],
              "readme": None,
              "requirements": None,
              "setup_py": None,
              "pyproject_toml": None
          }

          readme_path = file_utils.find_readme(repo_dir)
          if readme_path:
              structure["readme"] = file_utils.read_file_safe(readme_path)

          for root, dirs, files in os.walk(repo_dir):
              rel_root = os.path.relpath(root, repo_dir)
              if rel_root == ".":
                  rel_root = ""

              for d in dirs:
                  if d.startswith('.') or d in ['__pycache__', 'node_modules', 'venv', '.git']:
                      dirs.remove(d)
                      continue
                  structure["directories"].append(os.path.join(rel_root, d) if rel_root else d)

              for f in files:
                  if f.startswith('.'):
                      continue
                  file_path = os.path.join(rel_root, f) if rel_root else f
                  structure["files"].append(file_path)

                  if f == "requirements.txt":
                      structure["requirements"] = file_utils.read_file_safe(os.path.join(root, f))
                  elif f == "setup.py":
                      structure["setup_py"] = file_utils.read_file_safe(os.path.join(root, f))
                  elif f == "pyproject.toml":
                      structure["pyproject_toml"] = file_utils.read_file_safe(os.path.join(root, f))

          return structure
  ```

---

## 阶段四：Agent基础与适配层

### Task 11: Agent基类

**Files:**
- Create: `backend/agents/base.py`

- [ ] **Step 1: 编写Agent基类**
  ```python
  from abc import ABC, abstractmethod
  from typing import Any, Dict, Optional
  import logging

  logger = logging.getLogger(__name__)

  class BaseAgent(ABC):
      def __init__(self, name: str):
          self.name = name

      @abstractmethod
      def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
          pass

      def _log_start(self):
          logger.info(f"[{self.name}] 开始执行...")

      def _log_complete(self):
          logger.info(f"[{self.name}] 执行完成")

      def _log_error(self, error: Exception):
          logger.error(f"[{self.name}] 执行失败: {str(error)}")
  ```

---

### Task 12: RepoAgent适配层

**Files:**
- Create: `backend/adapters/repo_agent.py`

- [ ] **Step 1: 编写RepoAgent适配层（简化实现）**
  ```python
  import os
  from typing import Dict, Any, List
  from backend.utils.llm_client import llm_client
  import json
  import logging

  logger = logging.getLogger(__name__)

  class RepoAgentAdapter:
      def __init__(self, repo_dir: str):
          self.repo_dir = repo_dir

      def analyze(self, repo_structure: Dict[str, Any]) -> Dict[str, Any]:
          logger.info("开始代码解析...")

          files_sample = self._collect_code_files(repo_structure)

          system_prompt = """你是一个专业的代码分析专家。请分析给定的代码仓库，输出JSON格式的分析结果。

  请输出以下格式的JSON:
  {
      "project_overview": {
          "name": "项目名称",
          "description": "项目功能描述",
          "tech_stack": ["Python", "PyTorch", "..."]
      },
      "structure": {
          "main_modules": ["模块1", "模块2"],
          "key_files": ["文件1", "文件2"]
      },
      "algorithms": [
          {
              "name": "算法名称",
              "description": "算法描述",
              "file": "所在文件"
          }
      ],
      "dependencies": ["依赖1", "依赖2"],
      "experiments": {
          "has_experiments": true/false,
          "experiment_files": ["文件列表"],
          "metrics": ["指标1", "指标2"]
      }
  }"""

          user_prompt = f"""请分析以下代码仓库:

  仓库结构:
  {json.dumps(repo_structure, ensure_ascii=False, indent=2)}

  代码文件内容示例:
  {files_sample[:8000]}

  请输出JSON格式的分析结果。"""

          try:
              response = llm_client.chat_with_system_prompt(
                  user_prompt,
                  system_prompt,
                  temperature=0.3,
                  max_tokens=4000
              )

              result = llm_client.extract_json(response)
              if result:
                  return result
              else:
                  return self._fallback_analysis(repo_structure)
          except Exception as e:
              logger.error(f"代码解析失败: {e}")
              return self._fallback_analysis(repo_structure)

      def _collect_code_files(self, repo_structure: Dict[str, Any]) -> str:
          from backend.utils import file_utils
          sample = []

          for f in repo_structure.get("files", [])[:20]:
              if f.endswith('.py') or f.endswith('.md'):
                  filepath = os.path.join(self.repo_dir, f)
                  content = file_utils.read_file_safe(filepath, max_size=5000)
                  if content:
                      sample.append(f"--- {f} ---\n{content}\n")

          return "\n".join(sample)

      def _fallback_analysis(self, repo_structure: Dict[str, Any]) -> Dict[str, Any]:
          return {
              "project_overview": {
                  "name": "Unknown Project",
                  "description": "Project description unavailable",
                  "tech_stack": ["Python"]
              },
              "structure": {
                  "main_modules": [],
                  "key_files": repo_structure.get("files", [])[:10]
              },
              "algorithms": [],
              "dependencies": [],
              "experiments": {
                  "has_experiments": False,
                  "experiment_files": [],
                  "metrics": []
              }
          }
  ```

---

### Task 13: RD-Agent适配层

**Files:**
- Create: `backend/adapters/rd_agent.py`

- [ ] **Step 1: 编写RD-Agent适配层（简化实现）**
  ```python
  import os
  from typing import Dict, Any
  from backend.utils.llm_client import llm_client
  import json
  import logging

  logger = logging.getLogger(__name__)

  class RDAgentAdapter:
      def __init__(self, repo_dir: str):
          self.repo_dir = repo_dir

      def analyze(self, code_analysis: Dict[str, Any]) -> Dict[str, Any]:
          logger.info("开始实验分析...")

          system_prompt = """你是一个专业的实验分析专家。请基于代码分析结果，输出JSON格式的实验分析。

  请输出以下格式的JSON:
  {
      "experiment_setup": {
          "framework": "PyTorch/TensorFlow/...",
          "hardware": "GPU/CPU",
          "dataset": "数据集描述"
      },
      "metrics": [
          {
              "name": "准确率/Accuracy",
              "description": "指标描述"
          }
      ],
      "results": {
          "main_result": "主要结果描述",
          "baseline_comparison": "与基线对比"
      },
      "conclusion": "实验结论"
  }"""

          user_prompt = f"""请基于以下代码分析进行实验分析:

  {json.dumps(code_analysis, ensure_ascii=False, indent=2)}

  请输出JSON格式的实验分析结果。"""

          try:
              response = llm_client.chat_with_system_prompt(
                  user_prompt,
                  system_prompt,
                  temperature=0.3,
                  max_tokens=3000
              )

              result = llm_client.extract_json(response)
              if result:
                  return result
              else:
                  return self._fallback_analysis()
          except Exception as e:
              logger.error(f"实验分析失败: {e}")
              return self._fallback_analysis()

      def _fallback_analysis(self) -> Dict[str, Any]:
          return {
              "experiment_setup": {
                  "framework": "Unknown",
                  "hardware": "Unknown",
                  "dataset": "Unknown"
              },
              "metrics": [],
              "results": {
                  "main_result": "实验结果待补充",
                  "baseline_comparison": "基线对比待补充"
              },
              "conclusion": "实验结论待补充"
          }
  ```

---

## 阶段五：三个Agent实现

### Task 14: Code Parser Agent

**Files:**
- Create: `backend/agents/code_parser.py`

- [ ] **Step 1: 编写代码解析Agent**
  ```python
  from typing import Dict, Any
  from backend.agents.base import BaseAgent
  from backend.adapters.repo_agent import RepoAgentAdapter
  from backend.services.code_fetcher import CodeFetcher
  import logging

  logger = logging.getLogger(__name__)

  class CodeParserAgent(BaseAgent):
      def __init__(self):
          super().__init__("CodeParserAgent")

      def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
          self._log_start()
          try:
              repo_dir = input_data["repo_dir"]

              code_fetcher = CodeFetcher()
              repo_structure = code_fetcher.scan_repo_structure(repo_dir)

              repo_agent = RepoAgentAdapter(repo_dir)
              analysis = repo_agent.analyze(repo_structure)

              result = {
                  "success": True,
                  "repo_structure": repo_structure,
                  "code_analysis": analysis
              }

              self._log_complete()
              return result

          except Exception as e:
              self._log_error(e)
              return {
                  "success": False,
                  "error": str(e)
              }
  ```

---

### Task 15: Experiment Analyzer Agent

**Files:**
- Create: `backend/agents/experiment_analyzer.py`

- [ ] **Step 1: 编写实验分析Agent**
  ```python
  from typing import Dict, Any
  from backend.agents.base import BaseAgent
  from backend.adapters.rd_agent import RDAgentAdapter
  import logging

  logger = logging.getLogger(__name__)

  class ExperimentAnalyzerAgent(BaseAgent):
      def __init__(self):
          super().__init__("ExperimentAnalyzerAgent")

      def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
          self._log_start()
          try:
              repo_dir = input_data["repo_dir"]
              code_analysis = input_data["code_analysis"]

              rd_agent = RDAgentAdapter(repo_dir)
              analysis = rd_agent.analyze(code_analysis)

              result = {
                  "success": True,
                  "experiment_analysis": analysis
              }

              self._log_complete()
              return result

          except Exception as e:
              self._log_error(e)
              return {
                  "success": False,
                  "error": str(e)
              }
  ```

---

### Task 16: Paper Generator Agent

**Files:**
- Create: `backend/agents/paper_generator.py`

- [ ] **Step 1: 编写论文生成Agent**
  ```python
  from typing import Dict, Any
  from backend.agents.base import BaseAgent
  from backend.utils.llm_client import llm_client
  import json
  import logging

  logger = logging.getLogger(__name__)

  class PaperGeneratorAgent(BaseAgent):
      def __init__(self):
          super().__init__("PaperGeneratorAgent")

      def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
          self._log_start()
          try:
              code_analysis = input_data["code_analysis"]
              experiment_analysis = input_data["experiment_analysis"]

              paper = self._generate_full_paper(code_analysis, experiment_analysis)

              result = {
                  "success": True,
                  "paper_content": paper
              }

              self._log_complete()
              return result

          except Exception as e:
              self._log_error(e)
              return {
                  "success": False,
                  "error": str(e)
              }

      def _generate_full_paper(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
          sections = []

          sections.append(self._generate_abstract(code_analysis, experiment_analysis))
          sections.append(self._generate_introduction(code_analysis))
          sections.append(self._generate_related_work(code_analysis))
          sections.append(self._generate_methodology(code_analysis))
          sections.append(self._generate_experiments(code_analysis, experiment_analysis))
          sections.append(self._generate_conclusion(code_analysis, experiment_analysis))
          sections.append(self._generate_references())

          return "\n\n".join(sections)

      def _generate_section(self, prompt: str, system_prompt: str = None) -> str:
          try:
              if system_prompt is None:
                  system_prompt = "你是一个专业的学术论文写作助手，擅长用清晰、专业的语言撰写科研论文。"
              return llm_client.chat_with_system_prompt(
                  prompt,
                  system_prompt,
                  temperature=0.7,
                  max_tokens=2000
              )
          except Exception as e:
              logger.error(f"生成章节失败: {e}")
              return "[内容生成失败]"

      def _generate_abstract(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
          prompt = f"""请为以下项目撰写150-200字的论文摘要:

  项目分析: {json.dumps(code_analysis, ensure_ascii=False)}
  实验分析: {json.dumps(experiment_analysis, ensure_ascii=False)}

  请用英文撰写，包含研究背景、方法、主要结果和结论。

  输出格式:
  # Abstract

  [摘要内容]
  """
          return self._generate_section(prompt)

      def _generate_introduction(self, code_analysis: Dict) -> str:
          prompt = f"""请撰写论文的引言部分:

  项目分析: {json.dumps(code_analysis, ensure_ascii=False)}

  请包含:
  1. 研究背景与问题陈述
  2. 研究动机
  3. 本文贡献
  4. 论文结构概述

  输出格式:
  # 1. Introduction

  [引言内容]
  """
          return self._generate_section(prompt)

      def _generate_related_work(self, code_analysis: Dict) -> str:
          prompt = f"""请撰写论文的相关工作部分:

  项目分析: {json.dumps(code_analysis, ensure_ascii=False)}

  请讨论相关的研究工作，与本文方法进行对比。

  输出格式:
  # 2. Related Work

  [相关工作内容]
  """
          return self._generate_section(prompt)

      def _generate_methodology(self, code_analysis: Dict) -> str:
          prompt = f"""请撰写论文的方法部分:

  项目分析: {json.dumps(code_analysis, ensure_ascii=False)}

  请详细描述:
  1. 系统架构
  2. 关键算法
  3. 实现细节

  输出格式:
  # 3. Methodology

  [方法内容]
  """
          return self._generate_section(prompt)

      def _generate_experiments(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
          prompt = f"""请撰写论文的实验部分:

  项目分析: {json.dumps(code_analysis, ensure_ascii=False)}
  实验分析: {json.dumps(experiment_analysis, ensure_ascii=False)}

  请包含:
  1. 实验设置
  2. 评估指标
  3. 实验结果
  4. 结果分析

  输出格式:
  # 4. Experiments

  [实验内容]
  """
          return self._generate_section(prompt)

      def _generate_conclusion(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
          prompt = f"""请撰写论文的结论部分:

  项目分析: {json.dumps(code_analysis, ensure_ascii=False)}
  实验分析: {json.dumps(experiment_analysis, ensure_ascii=False)}

  请包含:
  1. 工作总结
  2. 主要贡献回顾
  3. 未来工作方向

  输出格式:
  # 5. Conclusion

  [结论内容]
  """
          return self._generate_section(prompt)

      def _generate_references(self) -> str:
          return """# 6. References

  [1] Placeholder reference.
  [2] Placeholder reference.
  [3] Placeholder reference.
  """
  ```

---

## 阶段六：任务服务与Worker

### Task 17: 任务服务

**Files:**
- Create: `backend/services/task_service.py`

- [ ] **Step 1: 编写任务管理服务**
  ```python
  from sqlalchemy.orm import Session
  from typing import Optional, Dict, Any
  from backend.models.task import Task, TaskStatus, InputType
  from datetime import datetime
  import logging

  logger = logging.getLogger(__name__)

  class TaskService:
      @staticmethod
      def create_task(
          db: Session,
          input_type: InputType,
          input_source: str,
          repo_path: Optional[str] = None
      ) -> Task:
          task = Task(
              input_type=input_type,
              input_source=input_source,
              repo_path=repo_path,
              status=TaskStatus.PENDING,
              progress=0
          )
          db.add(task)
          db.commit()
          db.refresh(task)
          logger.info(f"创建任务: {task.id}")
          return task

      @staticmethod
      def get_task(db: Session, task_id: str) -> Optional[Task]:
          return db.query(Task).filter(Task.id == task_id).first()

      @staticmethod
      def update_task_status(
          db: Session,
          task_id: str,
          status: TaskStatus,
          progress: Optional[int] = None
      ) -> bool:
          task = TaskService.get_task(db, task_id)
          if not task:
              return False
          task.status = status
          if progress is not None:
              task.progress = progress
          task.updated_at = datetime.utcnow()
          db.commit()
          logger.info(f"任务 {task_id} 状态更新为 {status.value}")
          return True

      @staticmethod
      def update_task_result(
          db: Session,
          task_id: str,
          code_analysis: Optional[Dict] = None,
          experiment_analysis: Optional[Dict] = None,
          paper_content: Optional[str] = None
      ) -> bool:
          task = TaskService.get_task(db, task_id)
          if not task:
              return False
          if code_analysis is not None:
              task.code_analysis = code_analysis
          if experiment_analysis is not None:
              task.experiment_analysis = experiment_analysis
          if paper_content is not None:
              task.paper_content = paper_content
          task.updated_at = datetime.utcnow()
          db.commit()
          return True

      @staticmethod
      def set_task_failed(db: Session, task_id: str, error_message: str) -> bool:
          task = TaskService.get_task(db, task_id)
          if not task:
              return False
          task.status = TaskStatus.FAILED
          task.error_message = error_message
          task.updated_at = datetime.utcnow()
          db.commit()
          logger.error(f"任务 {task_id} 失败: {error_message}")
          return True
  ```

---

### Task 18: 异步任务Worker

**Files:**
- Create: `backend/services/worker.py`

- [ ] **Step 1: 编写任务Worker**
  ```python
  import logging
  from backend.core.database import SessionLocal
  from backend.models.task import TaskStatus
  from backend.services.task_service import TaskService
  from backend.agents.code_parser import CodeParserAgent
  from backend.agents.experiment_analyzer import ExperimentAnalyzerAgent
  from backend.agents.paper_generator import PaperGeneratorAgent
  from backend.utils import file_utils

  logger = logging.getLogger(__name__)

  class TaskWorker:
      def __init__(self, task_id: str, repo_dir: str):
          self.task_id = task_id
          self.repo_dir = repo_dir
          self.db = SessionLocal()

      def run(self):
          try:
              logger.info(f"开始处理任务 {self.task_id}")

              TaskService.update_task_status(
                  self.db, self.task_id, TaskStatus.PARSING_CODE, progress=10
              )

              code_parser = CodeParserAgent()
              code_result = code_parser.run({
                  "repo_dir": self.repo_dir
              })

              if not code_result["success"]:
                  TaskService.set_task_failed(self.db, self.task_id, code_result["error"])
                  return

              code_analysis = code_result["code_analysis"]
              TaskService.update_task_result(
                  self.db, self.task_id, code_analysis=code_analysis
              )
              TaskService.update_task_status(
                  self.db, self.task_id, TaskStatus.ANALYZING_EXPERIMENT, progress=40
              )

              exp_analyzer = ExperimentAnalyzerAgent()
              exp_result = exp_analyzer.run({
                  "repo_dir": self.repo_dir,
                  "code_analysis": code_analysis
              })

              if not exp_result["success"]:
                  TaskService.set_task_failed(self.db, self.task_id, exp_result["error"])
                  return

              experiment_analysis = exp_result["experiment_analysis"]
              TaskService.update_task_result(
                  self.db, self.task_id, experiment_analysis=experiment_analysis
              )
              TaskService.update_task_status(
                  self.db, self.task_id, TaskStatus.GENERATING_PAPER, progress=70
              )

              paper_gen = PaperGeneratorAgent()
              paper_result = paper_gen.run({
                  "code_analysis": code_analysis,
                  "experiment_analysis": experiment_analysis
              })

              if not paper_result["success"]:
                  TaskService.set_task_failed(self.db, self.task_id, paper_result["error"])
                  return

              TaskService.update_task_result(
                  self.db, self.task_id, paper_content=paper_result["paper_content"]
              )
              TaskService.update_task_status(
                  self.db, self.task_id, TaskStatus.COMPLETED, progress=100
              )

              logger.info(f"任务 {self.task_id} 完成")

          except Exception as e:
              logger.exception(f"任务 {self.task_id} 异常")
              TaskService.set_task_failed(self.db, self.task_id, str(e))
          finally:
              try:
                  file_utils.cleanup_directory(self.repo_dir)
              except:
                  pass
              self.db.close()
  ```

---

## 阶段七：API路由与主入口

### Task 19: API路由

**Files:**
- Create: `backend/api/routes.py`

- [ ] **Step 1: 编写API路由**
  ```python
  from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
  from fastapi.responses import StreamingResponse
  from sqlalchemy.orm import Session
  from typing import Optional
  import uuid
  import os
  import io

  from backend.core.database import get_db
  from backend.core.config import settings
  from backend.api.schemas import (
      TaskCreateRequest,
      TaskResponse,
      MessageResponse,
      InputType,
      TaskStatus
  )
  from backend.services.task_service import TaskService
  from backend.services.code_fetcher import CodeFetcher
  from backend.services.worker import TaskWorker
  from backend.utils import file_utils
  import logging

  router = APIRouter(prefix="/api", tags=["tasks"])
  logger = logging.getLogger(__name__)

  def process_task_async(task_id: str, repo_dir: str):
      worker = TaskWorker(task_id, repo_dir)
      worker.run()

  @router.post("/tasks", response_model=TaskResponse)
  async def create_task(
      background_tasks: BackgroundTasks,
      input_type: str = Form(...),
      input_source: Optional[str] = Form(None),
      file: Optional[UploadFile] = File(None),
      db: Session = Depends(get_db)
  ):
      try:
          input_type_enum = InputType(input_type)

          work_dir, dir_id = file_utils.get_unique_upload_dir()
          repo_dir = None

          if input_type_enum == InputType.GIT_URL:
              if not input_source:
                  raise HTTPException(status_code=400, detail="Git URL required")
              repo_dir, repo_name = CodeFetcher.clone_git_repo(input_source, work_dir)
          elif input_type_enum == InputType.ZIP_UPLOAD:
              if not file:
                  raise HTTPException(status_code=400, detail="Zip file required")
              zip_path = file_utils.save_uploaded_file(
                  await file.read(),
                  file.filename or "upload.zip",
                  work_dir
              )
              repo_dir, repo_name = CodeFetcher.process_zip_upload(zip_path, work_dir)

          task = TaskService.create_task(
              db,
              input_type_enum,
              input_source or (file.filename if file else "upload.zip"),
              repo_path=repo_dir
          )

          background_tasks.add_task(process_task_async, task.id, repo_dir)

          return TaskResponse(
              id=task.id,
              status=TaskStatus(task.status.value),
              progress=task.progress,
              created_at=task.created_at,
              updated_at=task.updated_at
          )

      except ValueError as e:
          raise HTTPException(status_code=400, detail=str(e))
      except Exception as e:
          logger.exception("创建任务失败")
          raise HTTPException(status_code=500, detail=str(e))

  @router.get("/tasks/{task_id}", response_model=TaskResponse)
  async def get_task(task_id: str, db: Session = Depends(get_db)):
      task = TaskService.get_task(db, task_id)
      if not task:
          raise HTTPException(status_code=404, detail="Task not found")

      return TaskResponse(
          id=task.id,
          status=TaskStatus(task.status.value),
          progress=task.progress,
          created_at=task.created_at,
          updated_at=task.updated_at,
          paper_content=task.paper_content,
          error_message=task.error_message
      )

  @router.get("/tasks/{task_id}/download")
  async def download_paper(task_id: str, db: Session = Depends(get_db)):
      task = TaskService.get_task(db, task_id)
      if not task:
          raise HTTPException(status_code=404, detail="Task not found")
      if not task.paper_content:
          raise HTTPException(status_code=400, detail="Paper not available")

      filename = f"paper_{task.id}.md"
      return StreamingResponse(
          io.StringIO(task.paper_content),
          media_type="text/markdown",
          headers={"Content-Disposition": f'attachment; filename="{filename}"'}
      )
  ```

---

### Task 20: FastAPI主入口

**Files:**
- Create: `backend/main.py`

- [ ] **Step 1: 编写main.py**
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  import logging
  from backend.core.config import settings
  from backend.core.database import engine, Base
  from backend.api.routes import router

  logging.basicConfig(
      level=logging.INFO if not settings.debug else logging.DEBUG,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  )
  logger = logging.getLogger(__name__)

  Base.metadata.create_all(bind=engine)

  app = FastAPI(
      title="Code to Paper API",
      description="将代码仓库转换为科研论文的AI智能体",
      version="1.0.0"
  )

  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  app.include_router(router)

  @app.get("/")
  async def root():
      return {
          "message": "Code to Paper API",
          "version": "1.0.0",
          "status": "running"
      }

  @app.get("/health")
  async def health_check():
      return {"status": "healthy"}

  if __name__ == "__main__":
      import uvicorn
      uvicorn.run(
          "main:app",
          host=settings.server_host,
          port=settings.server_port,
          reload=settings.debug
      )
  ```

---

## 阶段八：前端实现

### Task 21: 前端项目配置

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`

- [ ] **Step 1: 创建 package.json**
  ```json
  {
    "name": "code-to-paper-frontend",
    "version": "1.0.0",
    "type": "module",
    "scripts": {
      "dev": "vite",
      "build": "vite build",
      "preview": "vite preview"
    },
    "dependencies": {
      "vue": "^3.3.8",
      "element-plus": "^2.4.4",
      "axios": "^1.6.2",
      "@element-plus/icons-vue": "^2.1.0"
    },
    "devDependencies": {
      "@vitejs/plugin-vue": "^4.5.0",
      "vite": "^5.0.4"
    }
  }
  ```

- [ ] **Step 2: 创建 vite.config.ts**
  ```typescript
  import { defineConfig } from 'vite'
  import vue from '@vitejs/plugin-vue'

  export default defineConfig({
    plugins: [vue()],
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

---

### Task 22: 前端API封装

**Files:**
- Create: `frontend/src/api/index.ts`

- [ ] **Step 1: 编写API封装**
  ```typescript
  import axios from 'axios'

  const api = axios.create({
    baseURL: '/api',
    timeout: 30000
  })

  export interface Task {
    id: string
    status: 'pending' | 'parsing_code' | 'analyzing_experiment' | 'generating_paper' | 'completed' | 'failed'
    progress: number
    created_at: string
    updated_at: string
    paper_content?: string
    error_message?: string
  }

  export const taskApi = {
    async createByGit(url: string): Promise<Task> {
      const formData = new FormData()
      formData.append('input_type', 'git_url')
      formData.append('input_source', url)
      const { data } = await api.post('/tasks', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return data
    },

    async createByZip(file: File): Promise<Task> {
      const formData = new FormData()
      formData.append('input_type', 'zip_upload')
      formData.append('file', file)
      const { data } = await api.post('/tasks', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return data
    },

    async get(taskId: string): Promise<Task> {
      const { data } = await api.get(`/tasks/${taskId}`)
      return data
    },

    download(taskId: string) {
      window.open(`/api/tasks/${taskId}/download`, '_blank')
    }
  }
  ```

---

### Task 23: 前端主组件

**Files:**
- Create: `frontend/src/App.vue`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/views/Home.vue`

- [ ] **Step 1: 创建 App.vue**
  ```vue
  <template>
    <el-container class="app-container">
      <el-header>
        <h1>📄 代码转论文智能体</h1>
      </el-header>
      <el-main>
        <Home />
      </el-main>
    </el-container>
  </template>

  <script setup lang="ts">
  import Home from './views/Home.vue'
  </script>

  <style>
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  .app-container {
    min-height: 100vh;
    background: #f5f7fa;
  }

  .app-container .el-header {
    background: #409eff;
    color: white;
    display: flex;
    align-items: center;
    padding: 0 40px;
  }

  .app-container .el-header h1 {
    font-size: 24px;
  }

  .app-container .el-main {
    max-width: 1000px;
    margin: 40px auto;
  }
  </style>
  ```

- [ ] **Step 2: 创建 main.ts**
  ```typescript
  import { createApp } from 'vue'
  import ElementPlus from 'element-plus'
  import 'element-plus/dist/index.css'
  import * as ElementPlusIconsVue from '@element-plus/icons-vue'
  import App from './App.vue'

  const app = createApp(App)

  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  app.use(ElementPlus)
  app.mount('#app')
  ```

- [ ] **Step 3: 创建 Home.vue**
  ```vue
  <template>
    <el-card>
      <template #header>
        <span>创建论文生成任务</span>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="Git仓库" name="git">
          <el-form label-width="100px">
            <el-form-item label="仓库URL">
              <el-input v-model="gitUrl" placeholder="https://github.com/user/repo.git" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitGit" :loading="loading">
                开始生成
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="上传ZIP" name="zip">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept=".zip"
          >
            <el-button type="primary">选择ZIP文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                请上传包含代码的ZIP压缩文件
              </div>
            </template>
          </el-upload>
          <el-button
            type="primary"
            style="margin-top: 20px"
            :disabled="!selectedFile"
            :loading="loading"
            @click="submitZip"
          >
            开始生成
          </el-button>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card v-if="currentTask" style="margin-top: 20px">
      <template #header>
        <span>任务状态</span>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务ID">{{ currentTask.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType">{{ statusText }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="进度" :span="2">
          <el-progress :percentage="currentTask.progress" :status="progressStatus" />
        </el-descriptions-item>
      </el-descriptions>

      <el-alert
        v-if="currentTask.error_message"
        type="error"
        :title="currentTask.error_message"
        style="margin-top: 20px"
        show-icon
      />

      <div v-if="currentTask.paper_content" style="margin-top: 20px">
        <el-button type="success" @click="downloadPaper">
          <el-icon><Download /></el-icon>
          下载论文
        </el-button>
      </div>
    </el-card>
  </template>

  <script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted } from 'vue'
  import { ElMessage } from 'element-plus'
  import { Download } from '@element-plus/icons-vue'
  import { taskApi, type Task } from '../api'

  const activeTab = ref('git')
  const gitUrl = ref('')
  const selectedFile = ref<File | null>(null)
  const loading = ref(false)
  const currentTask = ref<Task | null>(null)
  let pollTimer: number | null = null

  const statusType = computed(() => {
    const s = currentTask.value?.status
    if (s === 'completed') return 'success'
    if (s === 'failed') return 'danger'
    return 'info'
  })

  const statusText = computed(() => {
    const map: Record<string, string> = {
      pending: '等待中',
      parsing_code: '解析代码中',
      analyzing_experiment: '分析实验中',
      generating_paper: '生成论文中',
      completed: '已完成',
      failed: '失败'
    }
    return map[currentTask.value?.status || ''] || currentTask.value?.status
  })

  const progressStatus = computed(() => {
    const s = currentTask.value?.status
    if (s === 'completed') return 'success'
    if (s === 'failed') return 'exception'
    return undefined
  })

  const handleFileChange = (file: any) => {
    selectedFile.value = file.raw
  }

  const submitGit = async () => {
    if (!gitUrl.value) {
      ElMessage.warning('请输入Git仓库URL')
      return
    }
    loading.value = true
    try {
      currentTask.value = await taskApi.createByGit(gitUrl.value)
      ElMessage.success('任务创建成功')
      startPolling()
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '创建失败')
    } finally {
      loading.value = false
    }
  }

  const submitZip = async () => {
    if (!selectedFile.value) {
      ElMessage.warning('请选择ZIP文件')
      return
    }
    loading.value = true
    try {
      currentTask.value = await taskApi.createByZip(selectedFile.value)
      ElMessage.success('任务创建成功')
      startPolling()
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '创建失败')
    } finally {
      loading.value = false
    }
  }

  const startPolling = () => {
    if (pollTimer) clearInterval(pollTimer)
    pollTimer = window.setInterval(async () => {
      if (currentTask.value) {
        currentTask.value = await taskApi.get(currentTask.value.id)
        if (['completed', 'failed'].includes(currentTask.value.status)) {
          stopPolling()
        }
      }
    }, 2000)
  }

  const stopPolling = () => {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  const downloadPaper = () => {
    if (currentTask.value) {
      taskApi.download(currentTask.value.id)
    }
  }

  onUnmounted(() => {
    stopPolling()
  })
  </script>
  ```

---

### Task 24: 前端入口HTML

**Files:**
- Create: `frontend/index.html`

- [ ] **Step 1: 创建 index.html**
  ```html
  <!DOCTYPE html>
  <html lang="zh-CN">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>代码转论文智能体</title>
    </head>
    <body>
      <div id="app"></div>
      <script type="module" src="/src/main.ts"></script>
    </body>
  </html>
  ```

---

## 阶段九：运行与测试

### Task 25: 创建启动脚本

**Files:**
- Create: `backend/run.py`
- Create: `README.md`

- [ ] **Step 1: 创建 run.py（可选的启动脚本）**
  ```python
  import uvicorn
  from backend.core.config import settings

  if __name__ == "__main__":
      uvicorn.run(
          "backend.main:app",
          host=settings.server_host,
          port=settings.server_port,
          reload=settings.debug
      )
  ```

- [ ] **Step 2: 创建项目README**
  ```markdown
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
  ```

---

## 总结

这个实现计划包含了9个阶段，共25个任务，涵盖了从项目脚手架到完整MVP的所有代码。

**执行顺序建议：**
1. 阶段一-三：基础架构
2. 阶段四-六：核心业务逻辑
3. 阶段七：API层
4. 阶段八：前端
5. 阶段九：收尾

每个任务都有详细的步骤和完整代码，可以按顺序执行。
