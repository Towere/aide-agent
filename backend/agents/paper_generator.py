from typing import Dict, Any
from agents.base import BaseAgent
from utils.llm_client import get_llm_client
import json
import logging

logger = logging.getLogger(__name__)

class PaperGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("PaperGeneratorAgent")

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self._log_start()
        try:
            code_analysis = input_data["code_analysis"]
            experiment_analysis = input_data["experiment_analysis"]

            paper = self._generate_full_paper(code_analysis, experiment_analysis)

            result = {
                "success": True,
                "paper_content": paper
            }

            self._log_complete()
            return result

        except Exception as e:
            self._log_error(e)
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_full_paper(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
        sections = []

        sections.append(self._generate_abstract(code_analysis, experiment_analysis))
        sections.append(self._generate_introduction(code_analysis))
        sections.append(self._generate_related_work(code_analysis))
        sections.append(self._generate_methodology(code_analysis))
        sections.append(self._generate_experiments(code_analysis, experiment_analysis))
        sections.append(self._generate_conclusion(code_analysis, experiment_analysis))
        sections.append(self._generate_references())

        return "\n\n".join(sections)

    def _generate_section(self, prompt: str, system_prompt: str = None) -> str:
        try:
            if system_prompt is None:
                system_prompt = "你是一个专业的学术论文写作助手，擅长用清晰、专业的语言撰写科研论文。"
            return get_llm_client().chat_with_system_prompt(
                prompt,
                system_prompt,
                temperature=0.7,
                max_tokens=2000
            )
        except Exception as e:
            logger.error(f"生成章节失败: {e}")
            return "[内容生成失败]"

    def _generate_abstract(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
        prompt = f"""请为以下项目撰写150-200字的论文摘要:

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}
实验分析: {json.dumps(experiment_analysis, ensure_ascii=False)}

请用英文撰写，包含研究背景、方法、主要结果和结论。

输出格式:
# Abstract

[摘要内容]
"""
        return self._generate_section(prompt)

    def _generate_introduction(self, code_analysis: Dict) -> str:
        prompt = f"""请撰写论文的引言部分:

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}

请包含:
1. 研究背景与问题陈述
2. 研究动机
3. 本文贡献
4. 论文结构概述

输出格式:
# 1. Introduction

[引言内容]
"""
        return self._generate_section(prompt)

    def _generate_related_work(self, code_analysis: Dict) -> str:
        prompt = f"""请撰写论文的相关工作部分:

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}

请讨论相关的研究工作，与本文方法进行对比。

输出格式:
# 2. Related Work

[相关工作内容]
"""
        return self._generate_section(prompt)

    def _generate_methodology(self, code_analysis: Dict) -> str:
        prompt = f"""请撰写论文的方法部分:

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}

请详细描述:
1. 系统架构
2. 关键算法
3. 实现细节

输出格式:
# 3. Methodology

[方法内容]
"""
        return self._generate_section(prompt)

    def _generate_experiments(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
        prompt = f"""请撰写论文的实验部分:

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}
实验分析: {json.dumps(experiment_analysis, ensure_ascii=False)}

请包含:
1. 实验设置
2. 评估指标
3. 实验结果
4. 结果分析

输出格式:
# 4. Experiments

[实验内容]
"""
        return self._generate_section(prompt)

    def _generate_conclusion(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
        prompt = f"""请撰写论文的结论部分:

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}
实验分析: {json.dumps(experiment_analysis, ensure_ascii=False)}

请包含:
1. 工作总结
2. 主要贡献回顾
3. 未来工作方向

输出格式:
# 5. Conclusion

[结论内容]
"""
        return self._generate_section(prompt)

    def _generate_references(self) -> str:
        return """# 6. References

[1] Placeholder reference.
[2] Placeholder reference.
[3] Placeholder reference.
"""
