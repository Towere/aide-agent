import os
from typing import Dict, Any, List
from utils.llm_client import get_llm_client
import json
import logging

logger = logging.getLogger(__name__)

class RepoAgentAdapter:
    def __init__(self, repo_dir: str):
        self.repo_dir = repo_dir

    def analyze(self, repo_structure: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("开始代码解析...")

        files_sample = self._collect_code_files(repo_structure)

        system_prompt = """你是一个专业的代码分析专家。请分析给定的代码仓库，输出JSON格式的分析结果。

请输出以下格式的JSON:
{
    "project_overview": {
        "name": "项目名称",
        "description": "项目功能描述",
        "tech_stack": ["Python", "PyTorch", "..."]
    },
    "structure": {
        "main_modules": ["模块1", "模块2"],
        "key_files": ["文件1", "文件2"]
    },
    "algorithms": [
        {
            "name": "算法名称",
            "description": "算法描述",
            "file": "所在文件"
        }
    ],
    "dependencies": ["依赖1", "依赖2"],
    "experiments": {
        "has_experiments": true/false,
        "experiment_files": ["文件列表"],
        "metrics": ["指标1", "指标2"]
    }
}"""

        user_prompt = f"""请分析以下代码仓库:

仓库结构:
{json.dumps(repo_structure, ensure_ascii=False, indent=2)}

代码文件内容示例:
{files_sample[:8000]}

请输出JSON格式的分析结果。"""

        try:
            response = get_llm_client().chat_with_system_prompt(
                user_prompt,
                system_prompt,
                temperature=0.3,
                max_tokens=4000
            )

            result = get_llm_client().extract_json(response)
            if result:
                return result
            else:
                return self._fallback_analysis(repo_structure)
        except Exception as e:
            logger.error(f"代码解析失败: {e}")
            return self._fallback_analysis(repo_structure)

    def _collect_code_files(self, repo_structure: Dict[str, Any]) -> str:
        from utils import file_utils
        sample = []

        for f in repo_structure.get("files", [])[:20]:
            if f.endswith('.py') or f.endswith('.md'):
                filepath = os.path.join(self.repo_dir, f)
                content = file_utils.read_file_safe(filepath, max_size=5000)
                if content:
                    sample.append(f"--- {f} ---\n{content}\n")

        return "\n".join(sample)

    def _fallback_analysis(self, repo_structure: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "project_overview": {
                "name": "Unknown Project",
                "description": "Project description unavailable",
                "tech_stack": ["Python"]
            },
            "structure": {
                "main_modules": [],
                "key_files": repo_structure.get("files", [])[:10]
            },
            "algorithms": [],
            "dependencies": [],
            "experiments": {
                "has_experiments": False,
                "experiment_files": [],
                "metrics": []
            }
        }
