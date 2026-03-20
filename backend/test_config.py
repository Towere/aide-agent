import sys
from pathlib import Path
import os

backend_dir = Path(__file__).parent
project_root = backend_dir.parent

print("=== 检查 .env 文件 ===")
env_file_project = project_root / ".env"
env_file_backend = backend_dir / ".env"

print(f"项目根目录 .env: {env_file_project} 存在: {env_file_project.exists()}")
print(f"backend 目录 .env: {env_file_backend} 存在: {env_file_backend.exists()}")
print()

if env_file_project.exists():
    print("=== 项目根目录 .env 内容 ===")
    with open(env_file_project, 'r', encoding='utf-8') as f:
        print(f.read())
    print()

if env_file_backend.exists():
    print("=== backend 目录 .env 内容 ===")
    with open(env_file_backend, 'r', encoding='utf-8') as f:
        print(f.read())
    print()

print("=== 环境变量检查 ===")
print(f"DOUBA_MODEL (环境变量): {os.environ.get('DOUBA_MODEL', '未设置')}")
print(f"ARK_API_KEY (环境变量): {os.environ.get('ARK_API_KEY', '未设置')[:20] if os.environ.get('ARK_API_KEY') else '未设置'}...")
print()

print("=== 使用 pydantic_settings 读取 ===")
sys.path.insert(0, str(backend_dir))
from core.config import settings
print(f"settings.doubao_model: {settings.doubao_model}")
print(f"settings.ark_api_key: {settings.ark_api_key[:20] if settings.ark_api_key else '未设置'}...")
