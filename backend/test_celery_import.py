#!/usr/bin/env python
"""
测试 Celery 导入和配置
"""
import sys
import os
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

print("测试 Celery 导入...")

try:
    from core.celery import app
    print("[OK] Celery 应用导入成功")
    print(f"  Broker URL: {app.conf.broker_url}")
    print(f"  Backend URL: {app.conf.result_backend}")
except Exception as e:
    print(f"[ERROR] Celery 应用导入失败: {e}")
    sys.exit(1)

try:
    import tasks
    process_task = tasks.process_task
    print("[OK] Celery 任务导入成功")
    print(f"  任务名称: {process_task.name}")
except Exception as e:
    print(f"[ERROR] Celery 任务导入失败: {e}")
    sys.exit(1)

try:
    from services.worker import TaskWorker
    print("[OK] TaskWorker 导入成功")
except Exception as e:
    print(f"[ERROR] TaskWorker 导入失败: {e}")
    sys.exit(1)

print("\n所有导入测试通过！")
print("\n配置摘要:")
print(f"- Redis URL: {app.conf.broker_url}")
print(f"- 任务队列: {app.conf.task_routes}")
print(f"- 任务超时: {app.conf.task_time_limit} 秒")