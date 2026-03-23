from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import io
import json

from core.database import get_db
from core.config import settings
from api.schemas import (
    TaskCreateRequest,
    TaskResponse,
    MessageResponse,
    InputType,
    TaskStatus
)
from models.task import PaperLanguage
from services.task_service import TaskService
from services.code_fetcher import CodeFetcher
from core.celery import app as celery_app
from tasks import process_task as process_task_celery
from utils import file_utils
import logging

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
    template_file: Optional[UploadFile] = File(None),
    language: str = Form("en"),
    db: Session = Depends(get_db)
):
    """
    创建论文生成任务

    Args:
        input_type: 输入类型 - git_url 或 zip_upload
        input_source: Git URL（当input_type为git_url时必填）
        file: ZIP文件（当input_type为zip_upload时必填）
        template_file: 自定义paper_template.json模板文件（可选）
        language: 论文语言 - en (英文), zh (中文), bilingual (双语)
        db: 数据库会话

    Returns:
        任务信息
    """
    try:
        input_type_enum = InputType(input_type)

        # 解析语言参数
        try:
            language_enum = PaperLanguage(language)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的语言选项: {language}，可选值: en, zh, bilingual")

        work_dir, dir_id = file_utils.get_unique_upload_dir()
        repo_dir = None
        template_config = None

        # 解析模板文件
        if template_file:
            try:
                template_content = await template_file.read()
                template_config = json.loads(template_content.decode('utf-8'))
                logger.info(f"加载自定义模板: {template_file.filename}")
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"模板JSON格式错误: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"模板文件读取失败: {str(e)}")

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
            repo_path=repo_dir,
            template_config=template_config,
            language=language_enum
        )

        process_task_celery.apply_async(
            args=[task.id, repo_dir],
            queue='tasks',
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
    """
    获取任务详情

    Args:
        task_id: 任务ID
        db: 数据库会话

    Returns:
        任务信息
    """
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
async def download_paper(
    task_id: str,
    format: str = "md",
    db: Session = Depends(get_db)
):
    """
    下载生成的论文

    Args:
        task_id: 任务ID
        format: 下载格式 - "md" (Markdown) 或 "docx" (Word)
        db: 数据库会话

    Returns:
        文件流
    """
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.paper_content:
        raise HTTPException(status_code=400, detail="Paper not available")

    if format == "docx":
        # 生成DOCX格式
        from formatters.template_manager import get_template_manager
        from formatters.docx_formatter import generate_docx

        template = get_template_manager().merge_with_default(task.template_config)
        language = task.language.value if hasattr(task.language, 'value') else str(task.language) if task.language else 'en'
        logger.info(f"生成DOCX，任务语言: {language}")
        docx_bytes = generate_docx(
            paper_content=task.paper_content,
            template=template,
            code_analysis=task.code_analysis,
            language=language
        )

        filename = f"paper_{task.id}.docx"
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    else:
        # 默认返回Markdown格式
        filename = f"paper_{task.id}.md"
        return StreamingResponse(
            io.StringIO(task.paper_content),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
