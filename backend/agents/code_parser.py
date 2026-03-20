from typing import Dict, Any
from agents.base import BaseAgent
from adapters.repo_agent import RepoAgentAdapter
from services.code_fetcher import CodeFetcher
import logging

logger = logging.getLogger(__name__)

class CodeParserAgent(BaseAgent):
    def __init__(self):
        super().__init__("CodeParserAgent")

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self._log_start()
        try:
            repo_dir = input_data["repo_dir"]

            code_fetcher = CodeFetcher()
            repo_structure = code_fetcher.scan_repo_structure(repo_dir)

            repo_agent = RepoAgentAdapter(repo_dir)
            analysis = repo_agent.analyze(repo_structure)

            result = {
                "success": True,
                "repo_structure": repo_structure,
                "code_analysis": analysis
            }

            self._log_complete()
            return result

        except Exception as e:
            self._log_error(e)
            return {
                "success": False,
                "error": str(e)
            }
