import logging
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
        logger.info(f"TaskWorker initialized for task {task_id}, repo_dir: {repo_dir}")

    def run(self):
        logger.info(f"========== 开始处理任务 {self.task_id} ==========")
        try:
            # Step 1: Parse code
            logger.info(f"[Step 1/4] Parsing code...")
            TaskService.update_task_status(
                self.db, self.task_id, TaskStatus.PARSING_CODE, progress=10
            )

            code_parser = CodeParserAgent()
            code_result = code_parser.run({
                "repo_dir": self.repo_dir
            })
            logger.info(f"Code parser result: success={code_result.get('success')}")

            if not code_result["success"]:
                error_msg = code_result.get("error", "Unknown error")
                logger.error(f"Code parsing failed: {error_msg}")
                TaskService.set_task_failed(self.db, self.task_id, error_msg)
                return

            code_analysis = code_result["code_analysis"]
            logger.info(f"Code analysis obtained, updating task...")
            TaskService.update_task_result(
                self.db, self.task_id, code_analysis=code_analysis
            )

            # Step 2: Analyze experiment
            logger.info(f"[Step 2/4] Analyzing experiment...")
            TaskService.update_task_status(
                self.db, self.task_id, TaskStatus.ANALYZING_EXPERIMENT, progress=40
            )

            exp_analyzer = ExperimentAnalyzerAgent()
            exp_result = exp_analyzer.run({
                "repo_dir": self.repo_dir,
                "code_analysis": code_analysis
            })
            logger.info(f"Experiment analyzer result: success={exp_result.get('success')}")

            if not exp_result["success"]:
                error_msg = exp_result.get("error", "Unknown error")
                logger.error(f"Experiment analysis failed: {error_msg}")
                TaskService.set_task_failed(self.db, self.task_id, error_msg)
                return

            experiment_analysis = exp_result["experiment_analysis"]
            TaskService.update_task_result(
                self.db, self.task_id, experiment_analysis=experiment_analysis
            )

            # Step 3: Generate paper
            logger.info(f"[Step 3/4] Generating paper...")
            TaskService.update_task_status(
                self.db, self.task_id, TaskStatus.GENERATING_PAPER, progress=70
            )

            paper_gen = PaperGeneratorAgent()
            paper_result = paper_gen.run({
                "code_analysis": code_analysis,
                "experiment_analysis": experiment_analysis
            })
            logger.info(f"Paper generator result: success={paper_result.get('success')}")

            if not paper_result["success"]:
                error_msg = paper_result.get("error", "Unknown error")
                logger.error(f"Paper generation failed: {error_msg}")
                TaskService.set_task_failed(self.db, self.task_id, error_msg)
                return

            paper_content = paper_result["paper_content"]
            logger.info(f"Paper generated, length: {len(paper_content)} chars")

            # Step 4: Complete
            logger.info(f"[Step 4/4] Saving paper and completing...")
            TaskService.update_task_result(
                self.db, self.task_id, paper_content=paper_content
            )
            TaskService.update_task_status(
                self.db, self.task_id, TaskStatus.COMPLETED, progress=100
            )

            logger.info(f"========== 任务 {self.task_id} 完成 ==========")

        except Exception as e:
            logger.exception(f"任务 {self.task_id} 异常: {e}")
            TaskService.set_task_failed(self.db, self.task_id, str(e))
        finally:
            try:
                logger.info(f"Cleaning up directory: {self.repo_dir}")
                file_utils.cleanup_directory(self.repo_dir)
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")
            self.db.close()
            logger.info(f"Database connection closed")
