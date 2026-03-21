from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import io

from core.database import get_db
from core.config import settings
from api.schemas import (
    TaskCreateRequest,
    TaskResponse,
    MessageResponse,
    InputType,
    TaskStatus
)
from services.task_service import TaskService
from services.code_fetcher import CodeFetcher
# 🔴 关键修复1：导入 celery.py 中配置好的 Celery 实例，确保 API 复用同一配置
from core.celery import app as celery_app
from tasks import process_task as process_task_celery
from utils import file_utils
import logging

# 🔴 关键修复2：API 启动时验证 Redis 连接，提前暴露问题
import redis
logger = logging.getLogger(__name__)
try:
    r = redis.Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    r.ping()
    logger.info("✅ API 服务 Redis 连接验证成功")
except Exception as e:
    logger.error(f"❌ API 服务 Redis 连接失败: {str(e)}", exc_info=True)
    raise RuntimeError(f"Redis 连接失败: {str(e)}") from e

router = APIRouter(prefix="/api", tags=["tasks"])


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
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

        # 🔴 关键修复3：使用 apply_async 显式指定队列，匹配 celery.py 路由，添加重试
        process_task_celery.apply_async(
            args=[task.id, repo_dir],
            queue='tasks',  # 强制发送到 tasks 队列，确保 Worker 能消费
            retry=True,
            retry_policy={
                'max_retries': 3,
                'interval_start': 0,
                'interval_step': 0.5,
                'interval_max': 2,
            }
        )

        return TaskResponse(
            id=task.id,
            status=TaskStatus(task.status.value),
            progress=task.progress,
            created_at=task.created_at,
            updated_at=task.updated_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except redis.ConnectionError as e:
        logger.error(f"Redis 连接错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail="任务队列服务不可用，请稍后重试")
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