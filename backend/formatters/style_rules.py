"""
格式规则库 - 定义各类论文格式样式
"""
from typing import Dict, Any

# 默认学术格式
DEFAULT_STYLE: Dict[str, Any] = {
    "font": "Times New Roman",
    "font_cjk": "宋体",
    "title_size": 18,
    "heading1_size": 16,
    "heading2_size": 14,
    "heading3_size": 13,
    "body_size": 12,
    "line_spacing": 1.5,
    "paragraph_spacing_before": 6,  # 磅
    "paragraph_spacing_after": 6,
    "margin_top": 2.54,  # 厘米
    "margin_bottom": 2.54,
    "margin_left": 3.17,
    "margin_right": 3.17,
    "title_alignment": "center",  # center, left, right
    "heading_alignment": "left",
    "body_alignment": "justified",  # justified, left
}

# 广东高校格式（预留接口，可根据具体要求扩展）
GUANGDONG_UNIVERSITY_STYLE: Dict[str, Any] = {
    "font": "Times New Roman",
    "font_cjk": "宋体",
    "title_size": 22,
    "heading1_size": 18,
    "heading2_size": 16,
    "heading3_size": 14,
    "body_size": 12,
    "line_spacing": 1.5,
    "paragraph_spacing_before": 12,
    "paragraph_spacing_after": 12,
    "margin_top": 3.0,
    "margin_bottom": 3.0,
    "margin_left": 3.0,
    "margin_right": 2.5,
    "title_alignment": "center",
    "heading_alignment": "left",
    "body_alignment": "justified",
}


def get_style(style_name: str = "default") -> Dict[str, Any]:
    """
    获取指定名称的样式配置

    Args:
        style_name: 样式名称，"default" 或 "guangdong_university"

    Returns:
        样式配置字典
    """
    styles = {
        "default": DEFAULT_STYLE,
        "guangdong_university": GUANGDONG_UNIVERSITY_STYLE,
    }
    return styles.get(style_name, DEFAULT_STYLE).copy()


def merge_style(base_style: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并样式配置，override中的配置会覆盖base_style

    Args:
        base_style: 基础样式
        override: 覆盖样式

    Returns:
        合并后的样式
    """
    result = base_style.copy()
    result.update(override)
    return result
