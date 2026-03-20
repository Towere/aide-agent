from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
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
from services.worker import TaskWorker
from utils import file_utils
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
