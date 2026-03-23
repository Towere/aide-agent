"""
模板管理器 - 加载和管理 paper_template.json
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TemplateManager:
    """模板管理器"""

    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir is None:
            templates_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "paper_templates"
            )
        self.templates_dir = Path(templates_dir)
        self._default_template: Optional[Dict[str, Any]] = None

    def get_default_template(self) -> Dict[str, Any]:
        """
        获取默认模板

        Returns:
            默认模板配置
        """
        if self._default_template is None:
            default_path = self.templates_dir / "default.json"
            if not default_path.exists():
                raise FileNotFoundError(f"默认模板不存在: {default_path}")
            with open(default_path, 'r', encoding='utf-8') as f:
                self._default_template = json.load(f)
        return self._default_template.copy()

    def load_template(self, template_path: str) -> Dict[str, Any]:
        """
        从文件加载模板

        Args:
            template_path: 模板文件路径

        Returns:
            模板配置
        """
        path = Path(template_path)
        if not path.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        with open(path, 'r', encoding='utf-8') as f:
            template = json.load(f)
        return self._validate_template(template)

    def load_template_from_string(self, template_json: str) -> Dict[str, Any]:
        """
        从JSON字符串加载模板

        Args:
            template_json: JSON字符串

        Returns:
            模板配置
        """
        template = json.loads(template_json)
        return self._validate_template(template)

    def _validate_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证并补全模板配置

        Args:
            template: 待验证的模板

        Returns:
            验证并补全后的模板
        """
        default = self.get_default_template()

        # 合并顶层配置
        result = default.copy()
        result.update(template)

        # 合并 styles
        if 'styles' in template:
            result['styles'] = {**default['styles'], **template['styles']}

        # 合并 sections
        if 'sections' in template:
            result['sections'] = {**default['sections'], **template['sections']}

        return result

    def merge_with_default(self, custom_template: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        将自定义模板与默认模板合并

        Args:
            custom_template: 自定义模板，为None时返回默认模板

        Returns:
            合并后的模板
        """
        if custom_template is None:
            return self.get_default_template()
        return self._validate_template(custom_template)

    def render_template_variables(self, template: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        渲染模板中的变量

        Args:
            template: 模板配置
            variables: 变量字典

        Returns:
            渲染后的模板
        """
        import copy
        result = copy.deepcopy(template)

        # 默认变量
        default_vars = {
            'submit_date': datetime.now().strftime('%Y年%m月%d日'),
            'year': datetime.now().strftime('%Y'),
        }
        all_vars = {**default_vars, **variables}

        def render_string(s: str) -> str:
            if not isinstance(s, str):
                return s
            for key, value in all_vars.items():
                s = s.replace(f'{{{{{key}}}}}', str(value))
                s = s.replace(f'{{{{ {key} }}}}', str(value))
            return s

        def recursive_render(obj):
            if isinstance(obj, str):
                return render_string(obj)
            elif isinstance(obj, dict):
                return {k: recursive_render(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [recursive_render(item) for item in obj]
            return obj

        return recursive_render(result)


# 全局模板管理器实例
_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """
    获取全局模板管理器实例

    Returns:
        TemplateManager实例
    """
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager
