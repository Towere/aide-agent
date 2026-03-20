import os
import git
from typing import Optional, Tuple
from core.config import settings
from utils import file_utils
import shutil

class CodeFetcher:
    @staticmethod
    def clone_git_repo(git_url: str, target_dir: str) -> Tuple[str, str]:
        repo_name = git_url.split("/")[-1].replace(".git", "")
        repo_dir = os.path.join(target_dir, repo_name)

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        try:
            git.Repo.clone_from(git_url, repo_dir, depth=1)
            return repo_dir, repo_name
        except Exception as e:
            raise Exception(f"Git clone失败: {str(e)}")

    @staticmethod
    def process_zip_upload(zip_path: str, target_dir: str) -> Tuple[str, str]:
        repo_dir = file_utils.extract_zip(zip_path, target_dir)
        repo_name = os.path.basename(repo_dir)
        return repo_dir, repo_name

    @staticmethod
    def scan_repo_structure(repo_dir: str) -> dict:
        structure = {
            "files": [],
            "directories": [],
            "readme": None,
            "requirements": None,
            "setup_py": None,
            "pyproject_toml": None
        }

        readme_path = file_utils.find_readme(repo_dir)
        if readme_path:
            structure["readme"] = file_utils.read_file_safe(readme_path)

        for root, dirs, files in os.walk(repo_dir):
            rel_root = os.path.relpath(root, repo_dir)
            if rel_root == ".":
                rel_root = ""

            for d in list(dirs):
                if d.startswith('.') or d in ['__pycache__', 'node_modules', 'venv', '.git']:
                    dirs.remove(d)
                    continue
                structure["directories"].append(os.path.join(rel_root, d) if rel_root else d)

            for f in files:
                if f.startswith('.'):
                    continue
                file_path = os.path.join(rel_root, f) if rel_root else f
                structure["files"].append(file_path)

                if f == "requirements.txt":
                    structure["requirements"] = file_utils.read_file_safe(os.path.join(root, f))
                elif f == "setup.py":
                    structure["setup_py"] = file_utils.read_file_safe(os.path.join(root, f))
                elif f == "pyproject.toml":
                    structure["pyproject_toml"] = file_utils.read_file_safe(os.path.join(root, f))

        return structure
