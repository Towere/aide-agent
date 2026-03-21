"""
Celery 配置
使用 Redis 作为消息代理和结果后端
"""
import os
import sys
import warnings
from pathlib import Path
from celery import Celery

# 添加 backend 目录到 Python 路径，确保子进程能正确导入
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from .config import settings

# 抑制 Django 修复警告
warnings.filterwarnings('ignore', category=UserWarning, module='celery.fixups.django')

# 禁用 billiard 的 Django hack（Windows spawn 问题）
os.environ['NO_DJANGO_HACK'] = '1'

# 设置默认的 Django settings 模块（Celery 需要这个）
# 设置为空字符串避免 billiard 尝试导入 Django 项目
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '')

# 创建 Celery 应用实例
app = Celery(
    'code_to_paper',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['tasks']  # 包含任务模块
)

# 从配置中读取 Celery 设置
app.conf.update(
    # 🔴 关键修复：消除启动警告，启用启动时连接重试
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    
    # 任务序列化方式
    task_serializer='json',
    # 结果序列化方式
    result_serializer='json',
    # 接受的内容类型
    accept_content=['json'],
    # 时区设置
    timezone='Asia/Shanghai',
    # 启用 UTC
    enable_utc=True,
    # 任务执行结果过期时间（秒），默认 1 天
    result_expires=86400,
    # 每个 worker 最多执行 100 个任务后重启，防止内存泄漏
    worker_max_tasks_per_child=100,
    # 任务超时时间（秒），设置为 30 分钟
    task_time_limit=1800,
    # 任务软超时时间（秒），设置为 28 分钟
    task_soft_time_limit=1680,
    # 任务队列配置
    task_default_queue='default',
    # 任务路由
    task_routes={
        'tasks.process_task': {'queue': 'tasks'},
    },
    # 任务确认设置
    task_acks_late=True,
    # 任务拒绝时重新入队
    task_reject_on_worker_lost=True,
    # worker 预取数量
    worker_prefetch_multiplier=1,
)

if __name__ == '__main__':
    app.start()