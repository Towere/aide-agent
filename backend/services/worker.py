import logging
from typing import Callable, Dict, Any, Optional
from core.database import SessionLocal
from models.task import TaskStatus
from services.task_service import TaskService
from agents.code_parser import CodeParserAgent
from agents.experiment_analyzer import ExperimentAnalyzerAgent
from agents.paper_generator import PaperGeneratorAgent
from utils import file_utils

logger = logging.getLogger(__name__)


class TaskWorker:
    def __init__(self, task_id: str, repo_dir: str):
        self.task_id = task_id
        self.repo_dir = repo_dir
        self.db = SessionLocal()
        self.code_analysis: Optional[Dict[str, Any]] = None
        self.experiment_analysis: Optional[Dict[str, Any]] = None
        self.paper_content: Optional[str] = None
        self.template_config: Optional[Dict[str, Any]] = None
        logger.info(f"TaskWorker initialized for task {task_id}, repo_dir: {repo_dir}")

    def _update_status(self, status: TaskStatus, progress: int, message: str = ""):
        """更新任务状态并记录日志"""
        logger.info(f"[Task {self.task_id}] {status.value} - {message}" if message else f"[Task {self.task_id}] {status.value}")
        TaskService.update_task_status(self.db, self.task_id, status, progress=progress)

    def _update_result(self, **kwargs):
        """更新任务结果"""
        TaskService.update_task_result(self.db, self.task_id, **kwargs)

    def _set_failed(self, error_msg: str):
        """标记任务失败"""
        logger.error(f"[Task {self.task_id}] Task failed: {error_msg}")
        TaskService.set_task_failed(self.db, self.task_id, error_msg)

    def _execute_step(self, step_name: str, step_func: Callable[[], Dict[str, Any]],
                      success_status: TaskStatus, progress: int) -> bool:
        """
        执行单个步骤，包括状态更新、异常捕获和结果检查

        Returns:
            bool: 步骤是否成功
        """
        logger.info(f"[Task {self.task_id}] [Step: {step_name}] 开始执行")
        self._update_status(success_status, progress, f"执行 {step_name}")

        try:
            result = step_func()
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error")
                logger.error(f"[Task {self.task_id}] [Step: {step_name}] 失败: {error_msg}")
                self._set_failed(f"{step_name}失败: {error_msg}")
                return False

            logger.info(f"[Task {self.task_id}] [Step: {step_name}] 成功完成")
            return True

        except Exception as e:
            logger.exception(f"[Task {self.task_id}] [Step: {step_name}] 异常: {e}")
            self._set_failed(f"{step_name}异常: {str(e)}")
            return False

    def _step_parse_code(self) -> Dict[str, Any]:
        """步骤1: 解析代码"""
        code_parser = CodeParserAgent()
        result = code_parser.run({
            "repo_dir": self.repo_dir
        })
        if result.get("success"):
            self.code_analysis = result["code_analysis"]
            self._update_result(code_analysis=self.code_analysis)
        return result

    def _step_analyze_experiment(self) -> Dict[str, Any]:
        """步骤2: 分析实验"""
        if self.code_analysis is None:
            raise ValueError("代码分析结果为空，无法进行实验分析")

        exp_analyzer = ExperimentAnalyzerAgent()
        result = exp_analyzer.run({
            "repo_dir": self.repo_dir,
            "code_analysis": self.code_analysis
        })
        if result.get("success"):
            self.experiment_analysis = result["experiment_analysis"]
            self._update_result(experiment_analysis=self.experiment_analysis)
        return result

    def _step_generate_paper(self) -> Dict[str, Any]:
        """步骤3: 生成论文（使用新的模块化架构）"""
        if self.code_analysis is None or self.experiment_analysis is None:
            raise ValueError("代码分析或实验分析结果为空，无法生成论文")

        # 获取任务中的模板配置和语言设置
        task = TaskService.get_task(self.db, self.task_id)
        language = "en"
        if task:
            self.template_config = task.template_config
            if task.language:
                language = task.language.value if hasattr(task.language, 'value') else str(task.language)

        paper_gen = PaperGeneratorAgent()
        result = paper_gen.run({
            "code_analysis": self.code_analysis,
            "experiment_analysis": self.experiment_analysis,
            "template": self.template_config,
            "language": language
        })
        if result.get("success"):
            self.paper_content = result["paper_content"]
            self._update_result(paper_content=self.paper_content)
        return result

    def _step_complete(self) -> Dict[str, Any]:
        """步骤4: 完成任务"""
        logger.info(f"[Task {self.task_id}] 所有步骤完成，论文已生成")
        return {"success": True}

    def run(self):
        logger.info(f"========== 开始处理任务 {self.task_id} ==========")

        # 定义步骤序列
        steps = [
            {
                "name": "解析代码",
                "func": self._step_parse_code,
                "status": TaskStatus.PARSING_CODE,
                "progress": 10
            },
            {
                "name": "分析实验",
                "func": self._step_analyze_experiment,
                "status": TaskStatus.ANALYZING_EXPERIMENT,
                "progress": 40
            },
            {
                "name": "生成论文",
                "func": self._step_generate_paper,
                "status": TaskStatus.GENERATING_PAPER,
                "progress": 70
            },
            {
                "name": "完成任务",
                "func": self._step_complete,
                "status": TaskStatus.COMPLETED,
                "progress": 100
            }
        ]

        try:
            for step in steps:
                success = self._execute_step(
                    step_name=step["name"],
                    step_func=step["func"],
                    success_status=step["status"],
                    progress=step["progress"]
                )
                if not success:
                    logger.error(f"[Task {self.task_id}] 任务因步骤失败而中止")
                    return

            logger.info(f"========== 任务 {self.task_id} 完成 ==========")

        except Exception as e:
            logger.exception(f"[Task {self.task_id}] 任务执行过程中发生未捕获异常: {e}")
            self._set_failed(f"任务执行异常: {str(e)}")

        finally:
            try:
                logger.info(f"[Task {self.task_id}] 清理目录: {self.repo_dir}")
                file_utils.cleanup_directory(self.repo_dir)
            except Exception as e:
                logger.warning(f"[Task {self.task_id}] 目录清理失败: {e}")

            self.db.close()
            logger.info(f"[Task {self.task_id}] 数据库连接已关闭")
