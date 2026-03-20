from typing import Dict, Any
from agents.base import BaseAgent
from adapters.rd_agent import RDAgentAdapter
import logging

logger = logging.getLogger(__name__)

class ExperimentAnalyzerAgent(BaseAgent):
    def __init__(self):
        super().__init__("ExperimentAnalyzerAgent")

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self._log_start()
        try:
            repo_dir = input_data["repo_dir"]
            code_analysis = input_data["code_analysis"]

            rd_agent = RDAgentAdapter(repo_dir)
            analysis = rd_agent.analyze(code_analysis)

            result = {
                "success": True,
                "experiment_analysis": analysis
            }

            self._log_complete()
            return result

        except Exception as e:
            self._log_error(e)
            return {
                "success": False,
                "error": str(e)
            }
