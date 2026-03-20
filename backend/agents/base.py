from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def _log_start(self):
        logger.info(f"[{self.name}] 开始执行...")

    def _log_complete(self):
        logger.info(f"[{self.name}] 执行完成")

    def _log_error(self, error: Exception):
        logger.error(f"[{self.name}] 执行失败: {str(error)}")
