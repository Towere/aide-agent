from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from models.task import Task, TaskStatus, InputType
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
