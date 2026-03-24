"""
DOCX格式化器 - 生成Word文档
"""
import io
import logging
from typing import Dict, Any, Optional
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

from formatters.style_rules import get_style, merge_style

logger = logging.getLogger(__name__)


class DocxFormatter:
    """DOCX文档生成器"""

    def __init__(self, template: Dict[str, Any], style_override: Optional[Dict[str, Any]] = None):
        """
        初始化DOCX生成器

        Args:
            template: 论文模板配置
            style_override: 样式覆盖配置
        """
        self.template = template
        self.style_name = template.get('style_name', 'default')

        # 合并样式配置
        base_style = get_style(self.style_name)
        template_style = template.get('styles', {})
        if style_override:
            template_style = merge_style(template_style, style_override)
        self.style = merge_style(base_style, template_style)

        self.doc = Document()
        self._setup_document()

    def _setup_document(self):
        """设置文档基础格式"""
        section = self.doc.sections[0]

        # 设置页边距（厘米转EMU）
        section.top_margin = Cm(self.style['margin_top'])
        section.bottom_margin = Cm(self.style['margin_bottom'])
        section.left_margin = Cm(self.style['margin_left'])
        section.right_margin = Cm(self.style['margin_right'])

    def _set_font(self, run, size: int, is_cjk: bool = False, bold: bool = False):
        """
        设置字体

        Args:
            run: docx的Run对象
            size: 字号
            is_cjk: 是否为中文字体
            bold: 是否加粗
        """
        font = run.font
        font.name = self.style['font_cjk'] if is_cjk else self.style['font']
        font.size = Pt(size)
        font.bold = bold

        # 设置中文字体（需要同时设置EastAsia字体）
        if is_cjk:
            run._element.rPr.rFonts.set(qn('w:eastAsia'), self.style['font_cjk'])

    def _add_paragraph(self, text: str, size: Optional[int] = None,
                       alignment: str = 'left',
                       is_cjk: bool = False,
                       bold: bool = False,
                       line_spacing: Optional[float] = None,
                       space_before: Optional[float] = None,
                       space_after: Optional[float] = None):
        """
        添加段落

        Args:
            text: 段落文本
            size: 字号，使用默认正文字号如果为None
            alignment: 对齐方式: left, center, right, justified
            is_cjk: 是否为中文
            bold: 是否加粗
            line_spacing: 行间距
            space_before: 段前间距（磅）
            space_after: 段后间距（磅）

        Returns:
            docx Paragraph对象
        """
        p = self.doc.add_paragraph()

        # 对齐方式
        align_map = {
            'left': WD_ALIGN_PARAGRAPH.LEFT,
            'center': WD_ALIGN_PARAGRAPH.CENTER,
            'right': WD_ALIGN_PARAGRAPH.RIGHT,
            'justified': WD_ALIGN_PARAGRAPH.JUSTIFY,
        }
        p.alignment = align_map.get(alignment, WD_ALIGN_PARAGRAPH.LEFT)

        # 行间距
        if line_spacing is None:
            line_spacing = self.style['line_spacing']
        p.paragraph_format.line_spacing = line_spacing

        # 段前/段后间距
        if space_before is not None:
            p.paragraph_format.space_before = Pt(space_before)
        else:
            p.paragraph_format.space_before = Pt(self.style['paragraph_spacing_before'])

        if space_after is not None:
            p.paragraph_format.space_after = Pt(space_after)
        else:
            p.paragraph_format.space_after = Pt(self.style['paragraph_spacing_after'])

        # 添加文本并设置字体
        if text:
            run = p.add_run(text)
            self._set_font(run, size or self.style['body_size'], is_cjk, bold)

        return p

    def add_title_page(self, title: str, subtitle: Optional[str] = None,
                       author: Optional[str] = None,
                       institution: Optional[str] = None,
                       date: Optional[str] = None):
        """
        添加标题页

        Args:
            title: 论文标题
            subtitle: 副标题
            author: 作者
            institution: 机构
            date: 日期
        """
        # 添加空行来垂直居中
        for _ in range(8):
            self._add_paragraph('', size=12)

        # 主标题
        self._add_paragraph(
            title,
            size=self.style['title_size'],
            alignment=self.style['title_alignment'],
            is_cjk=True,
            bold=True,
            space_before=0,
            space_after=12
        )

        # 副标题
        if subtitle:
            self._add_paragraph(
                subtitle,
                size=self.style['heading2_size'],
                alignment='center',
                is_cjk=True,
                bold=False,
                space_before=0,
                space_after=24
            )

        # 作者
        if author:
            self._add_paragraph(
                author,
                size=self.style['body_size'],
                alignment='center',
                is_cjk=True,
                space_before=6,
                space_after=6
            )

        # 机构
        if institution:
            self._add_paragraph(
                institution,
                size=self.style['body_size'],
                alignment='center',
                is_cjk=True,
                space_before=6,
                space_after=6
            )

        # 日期
        if date:
            self._add_paragraph(
                date,
                size=self.style['body_size'],
                alignment='center',
                is_cjk=True,
                space_before=24
            )

        # 添加分页符
        self.doc.add_page_break()

    def add_abstract(self, content: str, heading: str = "摘要",
                     keywords: Optional[str] = None,
                     keywords_heading: str = "关键词",
                     is_cjk: bool = True):
        """
        添加摘要

        Args:
            content: 摘要内容
            heading: 摘要标题
            keywords: 关键词
            keywords_heading: 关键词标题
            is_cjk: 是否为中文
        """
        # 摘要标题
        self._add_paragraph(
            heading,
            size=self.style['heading1_size'],
            alignment='center',
            is_cjk=is_cjk,
            bold=True,
            space_before=12,
            space_after=12
        )

        # 摘要内容
        for paragraph in content.split('\n'):
            if paragraph.strip():
                self._add_paragraph(
                    paragraph.strip(),
                    alignment=self.style['body_alignment'],
                    is_cjk=is_cjk,
                    space_before=6,
                    space_after=6
                )

        # 关键词
        if keywords:
            self._add_paragraph(
                f"{keywords_heading}：{keywords}",
                is_cjk=is_cjk,
                space_before=12,
                space_after=12
            )

        self._add_paragraph('')

    def add_table_of_contents(self, heading: str = "目录"):
        """
        添加目录

        Args:
            heading: 目录标题
        """
        self._add_paragraph(
            heading,
            size=self.style['heading1_size'],
            alignment='center',
            is_cjk=True,
            bold=True,
            space_before=12,
            space_after=12
        )

        # 目录占位符（Word会自动更新）
        self._add_paragraph("（请右键更新域以生成目录）", alignment='center', space_before=6)
        self.doc.add_page_break()

    def add_heading(self, text: str, level: int = 1, is_cjk: bool = True):
        """
        添加标题

        Args:
            text: 标题文本
            level: 标题级别（1-3）
            is_cjk: 是否为中文
        """
        size_map = {
            1: self.style['heading1_size'],
            2: self.style['heading2_size'],
            3: self.style['heading3_size'],
        }
        size = size_map.get(level, self.style['heading2_size'])

        self._add_paragraph(
            text,
            size=size,
            alignment=self.style['heading_alignment'],
            is_cjk=is_cjk,
            bold=True,
            space_before=12,
            space_after=6
        )

    def add_image(self, image_path: str, caption: str = ""):
        """
        添加图片到文档

        Args:
            image_path: 图片文件路径
            caption: 图片标题
        """
        import os
        if not os.path.exists(image_path):
            logger.warning(f"图片文件不存在: {image_path}")
            return

        try:
            # 添加图片
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            run = p.add_run()
            from docx.shared import Inches
            # 添加图片，最大宽度6英寸
            run.add_picture(image_path, width=Inches(6))

            # 添加图片标题
            if caption:
                caption_p = self.doc.add_paragraph()
                caption_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                caption_run = caption_p.add_run(f"图：{caption}")
                caption_run.font.size = Pt(10)
                caption_run.font.italic = True

            logger.info(f"已插入图片: {image_path}")

        except Exception as e:
            logger.warning(f"插入图片失败: {image_path}, error: {e}")

    def add_section_content(self, content: str, is_cjk: bool = True):
        """
        添加章节内容

        Args:
            content: 章节内容（Markdown格式）
            is_cjk: 是否为中文
        """
        import re
        # 简单的Markdown解析
        lines = content.split('\n')
        for line in lines:
            line = line.rstrip()
            if not line:
                self._add_paragraph('')
                continue

            # 检测图片语法: ![caption](path)
            img_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line)
            if img_match:
                caption = img_match.group(1)
                img_path = img_match.group(2)
                self.add_image(img_path, caption)
                continue

            # 检测斜体图片标题: *caption*
            if line.startswith('*') and line.endswith('*'):
                # 这是图片标题，已在add_image中处理，跳过
                continue

            # 标题处理
            if line.startswith('# '):
                self.add_heading(line[2:], level=1, is_cjk=is_cjk)
            elif line.startswith('## '):
                self.add_heading(line[3:], level=2, is_cjk=is_cjk)
            elif line.startswith('### '):
                self.add_heading(line[4:], level=3, is_cjk=is_cjk)
            else:
                self._add_paragraph(
                    line,
                    alignment=self.style['body_alignment'],
                    is_cjk=is_cjk
                )

    def add_references(self, content: str, heading: str = "References",
                       heading_cn: str = "参考文献", is_cjk: bool = False):
        """
        添加参考文献

        Args:
            content: 参考文献内容
            heading: 英文标题
            heading_cn: 中文标题
            is_cjk: 是否为中文
        """
        self.doc.add_page_break()
        self.add_heading(heading_cn, level=1, is_cjk=True)
        self.add_heading(heading, level=1, is_cjk=False)
        self.add_section_content(content, is_cjk=is_cjk)

    def add_page_break(self):
        """添加分页符"""
        self.doc.add_page_break()

    def save(self, file_path: str):
        """
        保存文档到文件

        Args:
            file_path: 文件路径
        """
        self.doc.save(file_path)

    def get_bytes(self) -> bytes:
        """
        获取文档字节流

        Returns:
            文档字节内容
        """
        buffer = io.BytesIO()
        self.doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()


def generate_docx(
    paper_content: str,
    template: Dict[str, Any],
    code_analysis: Optional[Dict[str, Any]] = None,
    style_override: Optional[Dict[str, Any]] = None,
    language: str = 'en'
) -> bytes:
    """
    生成DOCX文档

    Args:
        paper_content: Markdown格式的论文内容
        template: 论文模板
        code_analysis: 代码分析结果（用于提取项目名称等）
        style_override: 样式覆盖
        language: 论文语言 - en, zh, bilingual

    Returns:
        DOCX文档字节内容
    """
    from formatters.template_manager import get_template_manager

    formatter = DocxFormatter(template, style_override)

    # 获取对应语言的结构配置
    paper_structure_config = template.get('paper_structure', {})
    if isinstance(paper_structure_config, dict):
        # 新格式：根据语言选择
        structure = paper_structure_config.get(language, paper_structure_config.get('en', []))
    else:
        # 旧格式：直接是数组
        structure = paper_structure_config

    logger.info(f"使用语言: {language}, 论文结构: {structure}")

    # 提取模板配置
    sections = template.get('sections', {})

    # 准备变量
    project_name = "代码项目"
    if code_analysis:
        project_name = code_analysis.get('project_name', project_name)

    template_vars = {
        'project_name': project_name,
    }

    # 渲染模板变量
    template = get_template_manager().render_template_variables(template, template_vars)
    sections = template.get('sections', {})

    # 直接添加论文内容（简化处理，避免复杂结构问题）
    logger.info(f"开始添加论文内容，长度: {len(paper_content)}")
    formatter.add_section_content(paper_content, is_cjk=(language != 'en'))

    result = formatter.get_bytes()
    logger.info(f"DOCX生成完成，大小: {len(result)} bytes")
    return result
