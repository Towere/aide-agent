"""
Celery 任务定义
"""
import logging
import sys
import os
from pathlib import Path
from celery import shared_task

# 添加 backend 目录到 Python 路径，以便能够导入 services
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from services.worker import TaskWorker
except ImportError:
    # 如果上述导入失败，尝试从 backend.services 导入
    from backend.services.worker import TaskWorker

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='tasks.process_task')
def process_task(self, task_id: str, repo_dir: str):
    """
    异步处理任务 - Celery 任务版本

    Args:
        task_id: 任务ID
        repo_dir: 代码仓库目录路径
    """
    logger.info(f"Celery 任务开始处理: task_id={task_id}, repo_dir={repo_dir}")
    try:
        worker = TaskWorker(task_id, repo_dir)
        worker.run()
        logger.info(f"Celery 任务完成: task_id={task_id}")
        return {"task_id": task_id, "status": "completed"}
    except Exception as e:
        logger.exception(f"Celery 任务失败: task_id={task_id}, error={e}")
        # 任务失败会触发重试机制
        raise