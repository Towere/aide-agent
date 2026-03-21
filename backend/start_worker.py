"""
启动 Celery Worker
"""
import os
import sys
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# 设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.config')

# 导入 Celery 应用
from core.celery import app

if __name__ == '__main__':
    # 启动 Celery worker
    # 使用以下命令启动 worker:
    # python -m backend.start_worker worker --loglevel=info
    # 或者直接使用 celery 命令:
    # celery -A backend.core.celery.app worker --loglevel=info

    # 使用 Celery 应用的 worker_main 方法启动 worker
    # 在 Windows 上使用 --pool=solo 避免多进程导入问题
    argv = ['worker', '--loglevel=info', '-Q', 'tasks,default', '--pool=solo']
    app.worker_main(argv)