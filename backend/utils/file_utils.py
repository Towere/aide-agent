import os
import zipfile
import shutil
from typing import Optional
from core.config import settings
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
