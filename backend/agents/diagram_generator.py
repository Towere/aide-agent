"""
图表生成器 - 生成系统架构图、流程图、E-R图等
使用Graphviz生成图片，简约风格
"""
import os
import re
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from agents.base import BaseAgent

logger = logging.getLogger(__name__)


class DiagramTextOptimizer:
    """图表文本优化器 - 处理语义化转换和可读性优化"""

    # 技术栈分类映射
    TECH_CATEGORIES = {
        'frontend': ['React', 'Vue', 'Angular', 'TypeScript', 'JavaScript', 'HTML', 'CSS', 'Webpack', 'Vite', 'Element Plus', 'Tailwind'],
        'backend': ['FastAPI', 'Flask', 'Django', 'Spring', 'Express', 'Node.js', 'Python', 'Java', 'Go', 'Rust'],
        'database': ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 'Elasticsearch'],
        'ai': ['PyTorch', 'TensorFlow', 'Transformers', 'LLM', 'OpenAI', 'Anthropic', '豆包'],
        'tools': ['Docker', 'Kubernetes', 'Git', 'Celery', 'RabbitMQ', 'Redis', 'Nginx']
    }

    # 常见文件后缀到模块名的映射
    FILE_SUFFIX_MAP = {
        '_api.py': 'API 模块',
        'api.py': 'API 模块',
        '_service.py': '服务模块',
        'service.py': '服务模块',
        '_utils.py': '工具模块',
        'utils.py': '工具模块',
        '_handler.py': '处理模块',
        'handler.py': '处理模块',
        '_agent.py': '智能体模块',
        'agent.py': '智能体模块',
        '_model.py': '模型模块',
        'model.py': '模型模块',
        '_schema.py': 'Schema 模块',
        'schema.py': 'Schema 模块',
        'config.py': '配置模块',
        'main.py': '主程序入口',
        'app.py': '应用入口',
        '__init__.py': '包初始化'
    }

    # 目录名语义化映射
    DIR_NAME_MAPPING = {
        'zh': {
            'backend': '后端服务',
            'frontend': '前端界面',
            'src': '源代码',
            'api': 'API 接口',
            'apis': 'API 接口',
            'services': '服务层',
            'service': '服务层',
            'utils': '工具模块',
            'util': '工具模块',
            'helpers': '辅助模块',
            'models': '数据模型',
            'model': '数据模型',
            'schemas': '数据校验',
            'schema': '数据校验',
            'core': '核心模块',
            'config': '配置管理',
            'conf': '配置管理',
            'tests': '测试代码',
            'test': '测试代码',
            'docs': '项目文档',
            'doc': '项目文档',
            'data': '数据目录',
            'agents': '智能体模块',
            'agent': '智能体模块',
            'adapters': '适配器层',
            'adapter': '适配器层',
            'formatters': '格式化器',
            'formatter': '格式化器',
            'ui': '用户界面',
            'web': 'Web 层',
            'middleware': '中间件',
            'middlewares': '中间件',
            'controllers': '控制器',
            'controller': '控制器',
            'views': '视图层',
            'view': '视图层',
            'templates': '模板',
            'template': '模板',
            'static': '静态资源',
            'assets': '资源文件',
            'lib': '库文件',
            'libs': '库文件',
            'vendor': '第三方依赖',
            'scripts': '脚本目录',
            'script': '脚本目录',
            'build': '构建输出',
            'dist': '发布目录',
            'public': '公共资源'
        },
        'en': {
            'backend': 'Backend Service',
            'frontend': 'Frontend UI',
            'src': 'Source Code',
            'api': 'API Layer',
            'apis': 'API Layer',
            'services': 'Service Layer',
            'service': 'Service Layer',
            'utils': 'Utilities',
            'util': 'Utilities',
            'helpers': 'Helpers',
            'models': 'Data Models',
            'model': 'Data Models',
            'schemas': 'Schemas',
            'schema': 'Schemas',
            'core': 'Core Module',
            'config': 'Configuration',
            'conf': 'Configuration',
            'tests': 'Tests',
            'test': 'Tests',
            'docs': 'Documentation',
            'doc': 'Documentation',
            'data': 'Data',
            'agents': 'Agents',
            'agent': 'Agents',
            'adapters': 'Adapters',
            'adapter': 'Adapters',
            'formatters': 'Formatters',
            'formatter': 'Formatters',
            'ui': 'UI Layer',
            'web': 'Web Layer',
            'middleware': 'Middleware',
            'middlewares': 'Middleware',
            'controllers': 'Controllers',
            'controller': 'Controllers',
            'views': 'Views',
            'view': 'Views',
            'templates': 'Templates',
            'template': 'Templates',
            'static': 'Static Assets',
            'assets': 'Assets',
            'lib': 'Libraries',
            'libs': 'Libraries',
            'vendor': 'Vendor',
            'scripts': 'Scripts',
            'script': 'Scripts',
            'build': 'Build',
            'dist': 'Dist',
            'public': 'Public'
        }
    }

    # 流程图中英文映射
    FLOW_LABELS = {
        'en': {
            'start': 'Start',
            'input': 'Input',
            'parse': 'Parse',
            'process': 'Process',
            'generate': 'Generate',
            'output': 'Output',
            'end': 'End'
        },
        'zh': {
            'start': '开始',
            'input': '输入数据',
            'parse': '解析处理',
            'process': '分析处理',
            'generate': '生成结果',
            'output': '输出',
            'end': '结束'
        }
    }

    @classmethod
    def normalize_module_name(cls, name: str, language: str = 'zh') -> str:
        """
        标准化模块名称 - 将文件名/路径/目录名转换为语义化名称

        Args:
            name: 原始模块名或文件名
            language: 语言 ('zh' 或 'en')

        Returns:
            语义化后的模块名
        """
        if not name:
            return "Unknown Module" if language == 'en' else "未知模块"

        # 如果已经是语义化名称（包含空格或中文），直接返回
        if ' ' in name or any('\u4e00' <= c <= '\u9fff' for c in name):
            return name

        original_name = name.strip()

        # 1. 处理路径，提取最后一部分
        if '/' in original_name or '\\' in original_name:
            parts = original_name.replace('\\', '/').split('/')
            # 检查是否有目录名映射（对路径中的每个部分检查）
            for part in reversed(parts):
                if part:
                    dir_mapped = cls._check_dir_mapping(part, language)
                    if dir_mapped:
                        return dir_mapped
            # 如果没有目录映射，使用最后一部分
            name = parts[-1]
        else:
            # 2. 检查是否是简单目录名（没有扩展名）
            dir_mapped = cls._check_dir_mapping(original_name, language)
            if dir_mapped:
                return dir_mapped
            name = original_name

        # 3. 检查常见文件后缀映射
        for suffix, semantic_name in cls.FILE_SUFFIX_MAP.items():
            if name.lower().endswith(suffix.lower()):
                base_name = name[:-len(suffix)] if len(suffix) < len(name) else name
                if base_name and base_name not in ['_', '']:
                    base_name = cls._normalize_identifier(base_name)
                    # 如果是中文环境，翻译后缀映射
                    if language == 'zh':
                        semantic_name = cls._translate_suffix(semantic_name)
                    return f"{base_name}{semantic_name}"
                return semantic_name if language == 'en' else cls._translate_suffix(semantic_name)

        # 4. 去除文件扩展名
        name = re.sub(r'\.(py|js|ts|java|go|rs|cpp|c|h|md|txt|json|yaml|yml)$', '', name, flags=re.I)

        # 5. 标准化标识符
        return cls._normalize_identifier(name)

    @classmethod
    def _check_dir_mapping(cls, name: str, language: str) -> Optional[str]:
        """检查目录名映射"""
        name_lower = name.lower()
        mapping = cls.DIR_NAME_MAPPING.get(language, cls.DIR_NAME_MAPPING['en'])
        return mapping.get(name_lower)

    @classmethod
    def _translate_suffix(cls, suffix_name: str) -> str:
        """翻译后缀映射到中文"""
        translation = {
            'API 模块': 'API 模块',
            '服务模块': '服务模块',
            '工具模块': '工具模块',
            '处理模块': '处理模块',
            '智能体模块': '智能体模块',
            '模型模块': '模型模块',
            'Schema 模块': 'Schema 模块',
            '配置模块': '配置模块',
            '主程序入口': '主程序入口',
            '应用入口': '应用入口',
            '包初始化': '包初始化'
        }
        return translation.get(suffix_name, suffix_name)

    @classmethod
    def _normalize_identifier(cls, identifier: str) -> str:
        """标准化标识符（下划线、驼峰转空格分隔）"""
        if not identifier:
            return ""

        # 去除前后下划线
        identifier = identifier.strip('_')

        # snake_case 转空格
        if '_' in identifier:
            parts = identifier.split('_')
            parts = [p.capitalize() for p in parts if p]
            return ' '.join(parts)

        # kebab-case 转空格
        if '-' in identifier:
            parts = identifier.split('-')
            parts = [p.capitalize() for p in parts if p]
            return ' '.join(parts)

        # camelCase 转空格
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', identifier)
        normalized = re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1)
        return normalized.title()

    @classmethod
    def categorize_tech_stack(cls, tech_stack: List[str]) -> Dict[str, List[str]]:
        """
        将技术栈分类

        Args:
            tech_stack: 技术栈列表

        Returns:
            分类后的技术栈字典
        """
        categorized = {
            'frontend': [],
            'backend': [],
            'database': [],
            'ai': [],
            'tools': [],
            'other': []
        }

        for tech in tech_stack:
            tech_lower = tech.lower()
            found = False
            for category, keywords in cls.TECH_CATEGORIES.items():
                if any(kw.lower() in tech_lower for kw in keywords):
                    categorized[category].append(tech)
                    found = True
                    break
            if not found:
                categorized['other'].append(tech)

        # 移除空分类
        return {k: v for k, v in categorized.items() if v}

    @classmethod
    def format_tech_stack_for_display(cls, tech_stack: List[str], language: str = 'zh') -> str:
        """
        格式化技术栈用于图表展示

        Args:
            tech_stack: 技术栈列表
            language: 语言 ('zh' 或 'en')

        Returns:
            格式化后的文本
        """
        categorized = cls.categorize_tech_stack(tech_stack)

        labels = {
            'zh': {
                'frontend': '前端',
                'backend': '后端',
                'database': '数据存储',
                'ai': 'AI/ML',
                'tools': '工具',
                'other': '其他'
            },
            'en': {
                'frontend': 'Frontend',
                'backend': 'Backend',
                'database': 'Database',
                'ai': 'AI/ML',
                'tools': 'Tools',
                'other': 'Other'
            }
        }

        lines = []
        lang_labels = labels.get(language, labels['en'])

        for cat, items in categorized.items():
            if items:
                label = lang_labels.get(cat, cat)
                lines.append(f"{label}: {', '.join(items[:3])}")

        return '\n'.join(lines)

    @classmethod
    def generate_flow_steps(cls, project_description: str, language: str = 'zh') -> List[Tuple[str, str, str]]:
        """
        基于项目描述生成流程步骤

        Args:
            project_description: 项目描述
            language: 语言

        Returns:
            流程步骤列表 [(step_id, label, shape), ...]
        """
        labels = cls.FLOW_LABELS.get(language, cls.FLOW_LABELS['en'])

        # 从描述中提取关键词判断项目类型
        desc_lower = project_description.lower()

        # 默认流程
        default_steps = [
            ("start", labels['start'], "ellipse"),
            ("input", labels['input'], "rectangle"),
            ("parse", labels['parse'], "rectangle"),
            ("process", labels['process'], "rectangle"),
            ("generate", labels['generate'], "rectangle"),
            ("end", labels['end'], "ellipse")
        ]

        # AI/LLM 项目流程
        if any(kw in desc_lower for kw in ['llm', 'agent', 'chat', 'gpt', 'ai', '智能体', '对话']):
            ai_labels = {
                'zh': [
                    ("start", "开始", "ellipse"),
                    ("input", "用户输入", "rectangle"),
                    ("prompt", "Prompt 构建", "rectangle"),
                    ("llm", "LLM 调用", "rectangle"),
                    ("parse", "结果解析", "rectangle"),
                    ("output", "输出返回", "rectangle"),
                    ("end", "结束", "ellipse")
                ],
                'en': [
                    ("start", "Start", "ellipse"),
                    ("input", "User Input", "rectangle"),
                    ("prompt", "Build Prompt", "rectangle"),
                    ("llm", "LLM Call", "rectangle"),
                    ("parse", "Parse Result", "rectangle"),
                    ("output", "Return Output", "rectangle"),
                    ("end", "End", "ellipse")
                ]
            }
            return ai_labels.get(language, ai_labels['en'])

        # Web 应用流程
        if any(kw in desc_lower for kw in ['web', 'api', 'http', 'frontend', '后端', '前端']):
            web_labels = {
                'zh': [
                    ("start", "开始", "ellipse"),
                    ("request", "接收请求", "rectangle"),
                    ("auth", "认证授权", "rectangle"),
                    ("logic", "业务逻辑", "rectangle"),
                    ("db", "数据操作", "rectangle"),
                    ("response", "返回响应", "rectangle"),
                    ("end", "结束", "ellipse")
                ],
                'en': [
                    ("start", "Start", "ellipse"),
                    ("request", "Receive Request", "rectangle"),
                    ("auth", "Auth & Validate", "rectangle"),
                    ("logic", "Business Logic", "rectangle"),
                    ("db", "DB Operation", "rectangle"),
                    ("response", "Return Response", "rectangle"),
                    ("end", "End", "ellipse")
                ]
            }
            return web_labels.get(language, web_labels['en'])

        # 数据处理项目
        if any(kw in desc_lower for kw in ['data', 'dataset', 'pipeline', 'etl', '数据']):
            data_labels = {
                'zh': [
                    ("start", "开始", "ellipse"),
                    ("ingest", "数据采集", "rectangle"),
                    ("clean", "数据清洗", "rectangle"),
                    ("transform", "数据转换", "rectangle"),
                    ("analyze", "数据分析", "rectangle"),
                    ("export", "结果导出", "rectangle"),
                    ("end", "结束", "ellipse")
                ],
                'en': [
                    ("start", "Start", "ellipse"),
                    ("ingest", "Data Ingest", "rectangle"),
                    ("clean", "Data Clean", "rectangle"),
                    ("transform", "Transform", "rectangle"),
                    ("analyze", "Analyze", "rectangle"),
                    ("export", "Export", "rectangle"),
                    ("end", "End", "ellipse")
                ]
            }
            return data_labels.get(language, data_labels['en'])

        return default_steps

    @classmethod
    def extract_entities(cls, code_analysis: Dict[str, Any]) -> List[Tuple[str, List[str]]]:
        """
        从代码分析中提取实体（用于E-R图）

        Args:
            code_analysis: 代码分析结果

        Returns:
            实体列表 [(entity_name, attributes), ...]
        """
        entities = []

        # 尝试从 algorithms 中提取
        algorithms = code_analysis.get('algorithms', [])
        for algo in algorithms:
            name = algo.get('name', '')
            if name and len(entities) < 5:
                # 简单的实体属性推断
                attrs = cls._infer_attributes_for_entity(name)
                entities.append((name, attrs))

        # 尝试从 key_files 中提取可能的模型
        key_files = code_analysis.get('structure', {}).get('key_files', [])
        for f in key_files:
            f_lower = f.lower()
            if any(kw in f_lower for kw in ['model', 'entity', 'schema']):
                # 从文件名提取实体名
                entity_name = cls.normalize_module_name(f)
                if entity_name and len(entities) < 5:
                    attrs = cls._infer_attributes_for_entity(entity_name)
                    entities.append((entity_name, attrs))

        # 如果没有提取到实体，使用智能 fallback
        if not entities:
            entities = cls._generate_fallback_entities(code_analysis)

        return entities[:5]  # 最多返回5个实体

    @classmethod
    def _infer_attributes_for_entity(cls, entity_name: str) -> List[str]:
        """为实体推断属性"""
        name_lower = entity_name.lower()

        base_attrs = ['id', 'created_at', 'updated_at']

        # 根据实体类型推断属性
        if any(kw in name_lower for kw in ['user', '用户', 'account']):
            return ['id', 'name', 'email', 'created_at']
        elif any(kw in name_lower for kw in ['project', '项目']):
            return ['id', 'name', 'description', 'status']
        elif any(kw in name_lower for kw in ['task', '任务']):
            return ['id', 'title', 'status', 'priority']
        elif any(kw in name_lower for kw in ['config', '配置']):
            return ['id', 'key', 'value', 'type']
        elif any(kw in name_lower for kw in ['file', '文件', 'document']):
            return ['id', 'name', 'path', 'size']
        elif any(kw in name_lower for kw in ['message', '消息', 'chat']):
            return ['id', 'content', 'role', 'timestamp']
        else:
            return ['id', 'name', 'type', 'created_at']

    @classmethod
    def _generate_fallback_entities(cls, code_analysis: Dict[str, Any]) -> List[Tuple[str, List[str]]]:
        """生成 fallback 实体（基于项目类型）"""
        overview = code_analysis.get('project_overview', {})
        desc = overview.get('description', '').lower()
        name = overview.get('name', '').lower()

        # AI 代理项目
        if any(kw in desc + name for kw in ['agent', 'llm', 'chat', '智能体']):
            return [
                ('Conversation', ['id', 'title', 'created_at']),
                ('Message', ['id', 'content', 'role', 'timestamp']),
                ('AgentConfig', ['id', 'name', 'model', 'prompt'])
            ]

        # Web 项目
        elif any(kw in desc + name for kw in ['web', 'api', 'app']):
            return [
                ('User', ['id', 'name', 'email', 'created_at']),
                ('Session', ['id', 'user_id', 'token', 'expires_at']),
                ('Resource', ['id', 'name', 'type', 'owner_id'])
            ]

        # 数据项目
        elif any(kw in desc + name for kw in ['data', 'pipeline', 'etl']):
            return [
                ('DataSource', ['id', 'name', 'type', 'config']),
                ('Pipeline', ['id', 'name', 'status', 'schedule']),
                ('RunLog', ['id', 'pipeline_id', 'status', 'started_at'])
            ]

        # 默认
        return [
            ('Config', ['id', 'key', 'value', 'updated_at']),
            ('Task', ['id', 'name', 'status', 'created_at']),
            ('Result', ['id', 'task_id', 'data', 'generated_at'])
        ]


class DiagramGenerator(BaseAgent):
    """图表生成智能体"""

    def __init__(self, output_dir: Optional[str] = None):
        super().__init__("DiagramGenerator")
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "outputs",
                "diagrams"
            )
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.text_optimizer = DiagramTextOptimizer()

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行图表生成

        Args:
            input_data: 包含 code_analysis 和 repo_structure

        Returns:
            生成的图表信息
        """
        self._log_start()
        try:
            code_analysis = input_data.get("code_analysis", {})
            repo_structure = input_data.get("repo_structure", {})
            task_id = input_data.get("task_id", "unknown")
            language = input_data.get("language", "zh")

            diagrams = {}

            # 1. 生成系统架构图
            try:
                arch_path = self.generate_architecture_diagram(
                    code_analysis, task_id, language
                )
                if arch_path:
                    caption = "系统架构图" if language == 'zh' else "System Architecture"
                    diagrams["architecture"] = {
                        "path": str(arch_path),
                        "type": "architecture",
                        "caption": caption
                    }
            except Exception as e:
                logger.warning(f"生成架构图失败: {e}")

            # 2. 生成功能流程图
            try:
                flow_path = self.generate_flow_diagram(
                    code_analysis, task_id, language
                )
                if flow_path:
                    caption = "功能流程图" if language == 'zh' else "Flow Diagram"
                    diagrams["flow"] = {
                        "path": str(flow_path),
                        "type": "flow",
                        "caption": caption
                    }
            except Exception as e:
                logger.warning(f"生成流程图失败: {e}")

            # 3. 生成数据库E-R图
            try:
                er_path = self.generate_er_diagram(
                    code_analysis, repo_structure, task_id, language
                )
                if er_path:
                    caption = "数据库E-R图" if language == 'zh' else "ER Diagram"
                    diagrams["er"] = {
                        "path": str(er_path),
                        "type": "er",
                        "caption": caption
                    }
            except Exception as e:
                logger.warning(f"生成E-R图失败: {e}")

            result = {
                "success": True,
                "diagrams": diagrams
            }

            self._log_complete()
            return result

        except Exception as e:
            self._log_error(e)
            return {
                "success": False,
                "error": str(e),
                "diagrams": {}
            }

    def generate_architecture_diagram(
        self,
        code_analysis: Dict[str, Any],
        task_id: str,
        language: str = 'zh'
    ) -> Optional[Path]:
        """
        生成系统架构图（优化版：语义化模块名、分类技术栈）

        Args:
            code_analysis: 代码分析结果
            task_id: 任务ID
            language: 语言

        Returns:
            生成的图片路径
        """
        try:
            from graphviz import Digraph
        except ImportError:
            logger.warning("graphviz 未安装，跳过架构图生成")
            return None

        project_name = code_analysis.get("project_overview", {}).get("name", "System")
        main_modules = code_analysis.get("structure", {}).get("main_modules", [])
        tech_stack = code_analysis.get("project_overview", {}).get("tech_stack", [])

        # 如果 main_modules 为空，使用默认模块
        if not main_modules:
            default_modules = ['Core Module', 'API Module', 'Utils Module'] if language == 'en' else ['核心模块', 'API 模块', '工具模块']
            main_modules = default_modules

        dot = Digraph(
            name=f'arch_{task_id}',
            comment='System Architecture',
            format='png'
        )

        # 设置简约风格
        dot.attr(rankdir='TB', splines='ortho')
        dot.attr('node', shape='rectangle', style='rounded,filled',
                   fillcolor='#e3f2fd', color='#1976d2', fontname='Arial')
        dot.attr('edge', color='#616161', penwidth='1.5')

        # 添加系统节点
        dot.node('system', project_name, shape='box', style='filled',
                 fillcolor='#bbdefb', fontsize='14', fontname='Arial Bold')

        # 添加语义化后的模块节点 - 传递 language 参数
        for i, module in enumerate(main_modules[:6]):  # 限制最多6个模块
            module_id = f'module_{i}'
            semantic_name = self.text_optimizer.normalize_module_name(str(module), language)
            dot.node(module_id, semantic_name, fontsize='12')
            dot.edge('system', module_id)

        # 添加分类后的技术栈备注
        if tech_stack:
            tech_label = self.text_optimizer.format_tech_stack_for_display(tech_stack, language)
            dot.node('tech_stack', tech_label, shape='note',
                     style='filled', fillcolor='#fff9c4', fontsize='10')

        # 保存
        output_path = self.output_dir / f'arch_{task_id}'
        dot.render(str(output_path), cleanup=True)

        png_path = output_path.with_suffix('.png')
        logger.info(f"架构图已生成: {png_path}")
        return png_path

    def generate_flow_diagram(
        self,
        code_analysis: Dict[str, Any],
        task_id: str,
        language: str = 'zh'
    ) -> Optional[Path]:
        """
        生成功能流程图（优化版：基于项目描述动态生成）

        Args:
            code_analysis: 代码分析结果
            task_id: 任务ID
            language: 语言

        Returns:
            生成的图片路径
        """
        try:
            from graphviz import Digraph
        except ImportError:
            logger.warning("graphviz 未安装，跳过流程图生成")
            return None

        project_desc = code_analysis.get("project_overview", {}).get("description", "")

        dot = Digraph(
            name=f'flow_{task_id}',
            comment='Flow Diagram',
            format='png'
        )

        # 设置简约风格
        dot.attr(rankdir='TB', splines='ortho')
        dot.attr('node', shape='rectangle', style='filled',
                   fillcolor='#f3e5f5', color='#7b1fa2', fontname='Arial')
        dot.attr('edge', color='#616161', penwidth='1.5')

        # 基于项目描述生成流程步骤
        steps = self.text_optimizer.generate_flow_steps(project_desc, language)

        for step_id, label, shape in steps:
            attrs = {'style': 'filled', 'fontsize': '12'}
            if shape == 'ellipse':
                attrs['shape'] = 'ellipse'
                attrs['fillcolor'] = '#c8e6c9'
                attrs['color'] = '#388e3c'
            else:
                attrs['shape'] = 'rectangle'
                attrs['fillcolor'] = '#f3e5f5'
            dot.node(step_id, label, **attrs)

        # 连接节点
        for i in range(len(steps) - 1):
            dot.edge(steps[i][0], steps[i + 1][0])

        # 保存
        output_path = self.output_dir / f'flow_{task_id}'
        dot.render(str(output_path), cleanup=True)

        png_path = output_path.with_suffix('.png')
        logger.info(f"流程图已生成: {png_path}")
        return png_path

    def generate_er_diagram(
        self,
        code_analysis: Dict[str, Any],
        repo_structure: Dict[str, Any],
        task_id: str,
        language: str = 'zh'
    ) -> Optional[Path]:
        """
        生成数据库E-R图（优化版：从代码分析中提取实体）

        Args:
            code_analysis: 代码分析结果
            repo_structure: 仓库结构
            task_id: 任务ID
            language: 语言

        Returns:
            生成的图片路径
        """
        try:
            from graphviz import Digraph
        except ImportError:
            logger.warning("graphviz 未安装，跳过E-R图生成")
            return None

        dot = Digraph(
            name=f'er_{task_id}',
            comment='ER Diagram',
            format='png'
        )

        # 设置简约风格
        dot.attr(rankdir='LR', splines='ortho')
        dot.attr('node', shape='rectangle', style='filled',
                   fillcolor='#fff3e0', color='#f57c00', fontname='Arial')
        dot.attr('edge', color='#616161', penwidth='1.5')

        # 从代码分析中提取实体
        entities = self.text_optimizer.extract_entities(code_analysis)

        # 添加实体节点
        entity_names = []
        for entity_name, attributes in entities:
            label = f"{entity_name}|{{" + "|".join(attributes) + "}"
            dot.node(entity_name, label, shape='record',
                     fillcolor='#fff3e0', fontsize='11')
            entity_names.append(entity_name)

        # 添加关系（基于实体顺序）
        rel_labels = {
            'zh': ['关联', '包含', '引用', '使用'],
            'en': ['relates to', 'contains', 'references', 'uses']
        }
        labels = rel_labels.get(language, rel_labels['en'])

        for i in range(len(entity_names) - 1):
            rel_label = labels[i % len(labels)]
            dot.edge(entity_names[i], entity_names[i + 1],
                     label=rel_label, fontsize='10')

        # 保存
        output_path = self.output_dir / f'er_{task_id}'
        dot.render(str(output_path), cleanup=True)

        png_path = output_path.with_suffix('.png')
        logger.info(f"E-R图已生成: {png_path}")
        return png_path
