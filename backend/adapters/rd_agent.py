import os
from typing import Dict, Any
from utils.llm_client import get_llm_client
import json
import logging

logger = logging.getLogger(__name__)

class RDAgentAdapter:
    def __init__(self, repo_dir: str):
        self.repo_dir = repo_dir

    def analyze(self, code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("开始实验分析...")

        system_prompt = """你是一个专业的实验分析专家。请基于代码分析结果，输出JSON格式的实验分析。

请输出以下格式的JSON:
{
    "experiment_setup": {
        "framework": "PyTorch/TensorFlow/...",
        "hardware": "GPU/CPU",
        "dataset": "数据集描述"
    },
    "metrics": [
        {
            "name": "准确率/Accuracy",
            "description": "指标描述"
        }
    ],
    "results": {
        "main_result": "主要结果描述",
        "baseline_comparison": "与基线对比"
    },
    "conclusion": "实验结论"
}"""

        user_prompt = f"""请基于以下代码分析进行实验分析:

{json.dumps(code_analysis, ensure_ascii=False, indent=2)}

请输出JSON格式的实验分析结果。"""

        try:
            response = get_llm_client().chat_with_system_prompt(
                user_prompt,
                system_prompt,
                temperature=0.3,
                max_tokens=3000
            )

            result = get_llm_client().extract_json(response)
            if result:
                return result
            else:
                return self._fallback_analysis()
        except Exception as e:
            logger.error(f"实验分析失败: {e}")
            return self._fallback_analysis()

    def _fallback_analysis(self) -> Dict[str, Any]:
        return {
            "experiment_setup": {
                "framework": "Unknown",
                "hardware": "Unknown",
                "dataset": "Unknown"
            },
            "metrics": [],
            "results": {
                "main_result": "实验结果待补充",
                "baseline_comparison": "基线对比待补充"
            },
            "conclusion": "实验结论待补充"
        }
