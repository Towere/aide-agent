"""
图表集成器 - 将生成的图表插入到论文合适位置
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class DiagramIntegrator:
    """图表集成器"""

    def __init__(self):
        pass

    def integrate(
        self,
        paper_content: str,
        diagrams: Dict[str, Any],
        language: str = 'en'
    ) -> str:
        """
        将图表集成到论文中

        Args:
            paper_content: 原始论文内容（Markdown）
            diagrams: 生成的图表字典
            language: 论文语言

        Returns:
            集成图表后的论文内容
        """
        if not diagrams:
            logger.info("没有图表需要集成")
            return paper_content

        logger.info(f"开始集成 {len(diagrams)} 个图表到论文")

        lines = paper_content.split('\n')
        result_lines = []
        inserted_diagrams = set()

        # 在Methodology章节后插入图表
        methodology_found = False
        methodology_heading = "# 3. Methodology" if language == 'en' else "# 3. 研究方法"

        for line in lines:
            result_lines.append(line)

            # 检测Methodology章节
            if line.strip() == methodology_heading or line.strip() == "# 3. Methodology":
                methodology_found = True

            # 在Methodology章节后插入图表
            if methodology_found and line.strip() == "" and len(inserted_diagrams) < len(diagrams):
                for diag_type, diag_info in diagrams.items():
                    if diag_type not in inserted_diagrams:
                        # 插入图表占位符
                        fig_caption = diag_info.get("caption", "Figure")
                        img_path = diag_info.get("path", "")

                        result_lines.append(f"\n![{fig_caption}]({img_path})")
                        result_lines.append(f"\n*{fig_caption}*\n")

                        inserted_diagrams.add(diag_type)
                        logger.info(f"已插入图表: {diag_type}")
                        break

        final_content = '\n'.join(result_lines)
        logger.info(f"图表集成完成，共插入 {len(inserted_diagrams)} 个图表")
        return final_content

    def get_diagram_markdown(
        self,
        diagram_path: str,
        caption: str,
        diagram_type: str
    ) -> str:
        """
        生成图表的Markdown代码

        Args:
            diagram_path: 图片路径
            caption: 图表标题
            diagram_type: 图表类型

        Returns:
            Markdown代码
        """
        return f"""
![{caption}]({diagram_path})

*{caption}*
"""
