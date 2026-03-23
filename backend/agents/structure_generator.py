"""
结构生成模块 - 生成完整论文结构
"""
from typing import Dict, Any
from agents.base import BaseAgent
from utils.llm_client import get_llm_client
import json
import logging

logger = logging.getLogger(__name__)


class StructureGeneratorAgent(BaseAgent):
    """结构生成智能体"""

    def __init__(self):
        super().__init__("StructureGeneratorAgent")

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行结构生成

        Args:
            input_data: 包含 'code_analysis' 和 'experiment_analysis' 的字典

        Returns:
            生成结果
        """
        self._log_start()
        try:
            code_analysis = input_data["code_analysis"]
            experiment_analysis = input_data.get("experiment_analysis", {})
            template = input_data.get("template", {})

            paper_structure = self._generate_structure(code_analysis, experiment_analysis, template)

            result = {
                "success": True,
                "paper_structure": paper_structure
            }

            self._log_complete()
            return result

        except Exception as e:
            self._log_error(e)
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_structure(self, code_analysis: Dict, experiment_analysis: Dict, template: Dict) -> Dict[str, Any]:
        """
        生成论文结构

        Args:
            code_analysis: 代码分析结果
            experiment_analysis: 实验分析结果
            template: 模板配置

        Returns:
            论文结构
        """
        sections = template.get('sections', {})
        main_body_config = sections.get('main_body', [])

        # 生成论文元数据
        project_name = code_analysis.get('project_name', '代码项目')

        # 生成中英文摘要
        abstract_cn = self._generate_abstract_cn(code_analysis, experiment_analysis)
        abstract_en = self._generate_abstract_en(code_analysis, experiment_analysis)

        # 生成关键词
        keywords_cn = self._generate_keywords_cn(code_analysis)
        keywords_en = self._generate_keywords_en(code_analysis)

        return {
            "title": project_name,
            "abstract_cn": abstract_cn,
            "keywords_cn": keywords_cn,
            "abstract_en": abstract_en,
            "keywords_en": keywords_en,
            "main_body_sections": main_body_config
        }

    def _generate_abstract_cn(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
        """生成中文摘要"""
        prompt = f"""请为以下项目生成中文摘要（150-200字）：

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}
实验分析: {json.dumps(experiment_analysis, ensure_ascii=False)}

请直接输出摘要内容，不要包含标题。"""

        try:
            return get_llm_client().chat_with_system_prompt(
                prompt,
                "你是一个专业的学术论文写作助手。",
                temperature=0.7,
                max_tokens=500
            )
        except Exception as e:
            logger.error(f"生成中文摘要失败: {e}")
            return "[摘要生成失败]"

    def _generate_abstract_en(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
        """生成英文摘要"""
        prompt = f"""Please write an English abstract (150-200 words) for this project:

Project Analysis: {json.dumps(code_analysis, ensure_ascii=False)}
Experiment Analysis: {json.dumps(experiment_analysis, ensure_ascii=False)}

Output only the abstract content, no title."""

        try:
            return get_llm_client().chat_with_system_prompt(
                prompt,
                "You are a professional academic paper writing assistant.",
                temperature=0.7,
                max_tokens=500
            )
        except Exception as e:
            logger.error(f"生成英文摘要失败: {e}")
            return "[Abstract generation failed]"

    def _generate_keywords_cn(self, code_analysis: Dict) -> str:
        """生成中文关键词"""
        return "关键词1, 关键词2, 关键词3"

    def _generate_keywords_en(self, code_analysis: Dict) -> str:
        """生成英文关键词"""
        return "Keyword1, Keyword2, Keyword3"
