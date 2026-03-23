"""
论文生成协调器 - 协调各模块生成完整论文
"""
from typing import Dict, Any
from agents.base import BaseAgent
from agents.structure_generator import StructureGeneratorAgent
from agents.content_optimizer import ContentOptimizerAgent
from formatters.template_manager import get_template_manager
from formatters.docx_formatter import generate_docx
import json
import logging

logger = logging.getLogger(__name__)


class PaperGeneratorAgent(BaseAgent):
    """论文生成协调器"""

    def __init__(self):
        super().__init__("PaperGeneratorAgent")
        self.structure_agent = StructureGeneratorAgent()
        self.content_optimizer = ContentOptimizerAgent()
        self.template_manager = get_template_manager()

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行论文生成流程

        Args:
            input_data: 包含以下字段:
                - code_analysis: 代码分析结果
                - experiment_analysis: 实验分析结果
                - template: (可选) 自定义模板配置
                - language: (可选) 论文语言 - en, zh, bilingual

        Returns:
            生成结果，包含:
                - success: 是否成功
                - paper_content: Markdown格式论文
                - paper_docx: DOCX格式论文（字节）
                - paper_structure: 论文结构
        """
        self._log_start()
        try:
            code_analysis = input_data["code_analysis"]
            experiment_analysis = input_data["experiment_analysis"]
            custom_template = input_data.get("template")
            language = input_data.get("language", "en")

            # 1. 获取模板
            template = self.template_manager.merge_with_default(custom_template)

            # 2. 生成论文结构
            structure_result = self.structure_agent.run({
                "code_analysis": code_analysis,
                "experiment_analysis": experiment_analysis,
                "template": template,
                "language": language
            })
            if not structure_result.get("success"):
                return {
                    "success": False,
                    "error": structure_result.get("error", "结构生成失败")
                }
            paper_structure = structure_result["paper_structure"]

            # 3. 生成论文内容（根据语言选择）
            paper_content = self._generate_full_paper(code_analysis, experiment_analysis, language)

            # 4. 优化内容
            opt_result = self.content_optimizer.run({
                "paper_content": paper_content,
                "code_analysis": code_analysis
            })
            if opt_result.get("success"):
                paper_content = opt_result["optimized_content"]

            # 5. 生成DOCX
            paper_docx = generate_docx(
                paper_content=paper_content,
                template=template,
                code_analysis=code_analysis
            )

            result = {
                "success": True,
                "paper_content": paper_content,
                "paper_docx": paper_docx,
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

    def _generate_full_paper(self, code_analysis: Dict, experiment_analysis: Dict, language: str = "en") -> str:
        """
        生成完整论文

        Args:
            code_analysis: 代码分析结果
            experiment_analysis: 实验分析结果
            language: 论文语言 - en, zh, bilingual

        Returns:
            Markdown格式论文
        """
        if language == "zh":
            return self._generate_paper_chinese(code_analysis, experiment_analysis)
        elif language == "bilingual":
            return self._generate_paper_bilingual(code_analysis, experiment_analysis)
        else:
            return self._generate_paper_english(code_analysis, experiment_analysis)

    def _generate_paper_english(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
        """生成纯英文论文"""
        sections = []
        sections.append(self._generate_abstract(code_analysis, experiment_analysis))
        sections.append(self._generate_introduction(code_analysis))
        sections.append(self._generate_related_work(code_analysis))
        sections.append(self._generate_methodology(code_analysis))
        sections.append(self._generate_experiments(code_analysis, experiment_analysis))
        sections.append(self._generate_conclusion(code_analysis, experiment_analysis))
        sections.append(self._generate_references())
        return "\n\n".join(sections)

    def _generate_paper_chinese(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
        """生成纯中文论文"""
        sections = []
        sections.append(self._generate_abstract_cn(code_analysis, experiment_analysis))
        sections.append(self._generate_introduction_cn(code_analysis))
        sections.append(self._generate_related_work_cn(code_analysis))
        sections.append(self._generate_methodology_cn(code_analysis))
        sections.append(self._generate_experiments_cn(code_analysis, experiment_analysis))
        sections.append(self._generate_conclusion_cn(code_analysis, experiment_analysis))
        sections.append(self._generate_references_cn())
        return "\n\n".join(sections)

    def _generate_paper_bilingual(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
        """生成双语对照论文"""
        sections = []
        sections.append(self._generate_abstract(code_analysis, experiment_analysis))
        sections.append(self._generate_abstract_cn(code_analysis, experiment_analysis))
        sections.append(self._generate_introduction(code_analysis))
        sections.append(self._generate_introduction_cn(code_analysis))
        sections.append(self._generate_related_work(code_analysis))
        sections.append(self._generate_related_work_cn(code_analysis))
        sections.append(self._generate_methodology(code_analysis))
        sections.append(self._generate_methodology_cn(code_analysis))
        sections.append(self._generate_experiments(code_analysis, experiment_analysis))
        sections.append(self._generate_experiments_cn(code_analysis, experiment_analysis))
        sections.append(self._generate_conclusion(code_analysis, experiment_analysis))
        sections.append(self._generate_conclusion_cn(code_analysis, experiment_analysis))
        sections.append(self._generate_references())
        return "\n\n".join(sections)

    def _generate_section(self, prompt: str, system_prompt: str = None) -> str:
        """生成单个章节"""
        from utils.llm_client import get_llm_client

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

    # ========== 中文论文生成方法 ==========

    def _generate_abstract_cn(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
        prompt = f"""请为以下项目撰写150-200字的中文论文摘要:

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}
实验分析: {json.dumps(experiment_analysis, ensure_ascii=False)}

请用中文撰写，包含研究背景、方法、主要结果和结论。

输出格式:
# 摘要

[摘要内容]
"""
        return self._generate_section(prompt, "你是一个专业的中文学术论文写作助手。")

    def _generate_introduction_cn(self, code_analysis: Dict) -> str:
        prompt = f"""请撰写论文的引言部分:

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}

请包含:
1. 研究背景与问题陈述
2. 研究动机
3. 本文贡献
4. 论文结构概述

输出格式:
# 1. 引言

[引言内容]
"""
        return self._generate_section(prompt, "你是一个专业的中文学术论文写作助手。")

    def _generate_related_work_cn(self, code_analysis: Dict) -> str:
        prompt = f"""请撰写论文的相关工作部分:

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}

请讨论相关的研究工作，与本文方法进行对比。

输出格式:
# 2. 相关工作

[相关工作内容]
"""
        return self._generate_section(prompt, "你是一个专业的中文学术论文写作助手。")

    def _generate_methodology_cn(self, code_analysis: Dict) -> str:
        prompt = f"""请撰写论文的研究方法部分:

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}

请详细描述:
1. 系统架构
2. 关键算法
3. 实现细节

输出格式:
# 3. 研究方法

[方法内容]
"""
        return self._generate_section(prompt, "你是一个专业的中文学术论文写作助手。")

    def _generate_experiments_cn(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
        prompt = f"""请撰写论文的实验部分:

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}
实验分析: {json.dumps(experiment_analysis, ensure_ascii=False)}

请包含:
1. 实验设置
2. 评估指标
3. 实验结果
4. 结果分析

输出格式:
# 4. 实验

[实验内容]
"""
        return self._generate_section(prompt, "你是一个专业的中文学术论文写作助手。")

    def _generate_conclusion_cn(self, code_analysis: Dict, experiment_analysis: Dict) -> str:
        prompt = f"""请撰写论文的结论部分:

项目分析: {json.dumps(code_analysis, ensure_ascii=False)}
实验分析: {json.dumps(experiment_analysis, ensure_ascii=False)}

请包含:
1. 工作总结
2. 主要贡献回顾
3. 未来工作方向

输出格式:
# 5. 结论

[结论内容]
"""
        return self._generate_section(prompt, "你是一个专业的中文学术论文写作助手。")

    def _generate_references_cn(self) -> str:
        return """# 6. 参考文献

[1] 参考文献示例1.
[2] 参考文献示例2.
[3] 参考文献示例3.
"""
