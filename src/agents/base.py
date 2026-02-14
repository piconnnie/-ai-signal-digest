import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.core.config import Config
from src.core.logger import setup_logger

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the pipeline.
    Enforces a standard execution interface and logging.
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = setup_logger(agent_name)
        self.config = Config

    def run(self, *args, **kwargs) -> Any:
        """
        Wrapper method to handle logging, timing, and error boundaries.
        Actual logic lives in `_execute`.
        """
        self.logger.info(f"Starting execution of {self.agent_name}...")
        start_time = time.time()
        
        try:
            result = self._execute(*args, **kwargs)
            duration = time.time() - start_time
            self.logger.info(f"Finished {self.agent_name} in {duration:.2f}s.")
            return result
        except Exception as e:
            self.logger.error(f"Error in {self.agent_name}: {str(e)}", exc_info=True)
            # In a real system, we might decide to re-raise or return a Failure object
            # For now, re-raising to bubble up to the scheduler/orchestrator
            raise e

    @abstractmethod
    def _execute(self, *args, **kwargs) -> Any:
        """
        Core logic of the agent. Must be implemented by subclasses.
        """
        pass
