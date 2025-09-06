"""Base agent class for the MCP Multi-Agent Developer Pod."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..models import Task, AgentType, AgentResponse, AgentMessage
from ..llm_client import LLMClient
from ..tools.git_tools import GitTools
from ..tools.file_tools import FileTools
from ..tools.python_tools import PythonTools
from ..tools.test_tools import TestTools

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the development pod."""
    
    def __init__(self, agent_type: AgentType, llm_client: LLMClient):
        self.agent_type = agent_type
        self.llm_client = llm_client
        self.git_tools = GitTools()
        self.file_tools = FileTools()
        self.python_tools = PythonTools()
        self.test_tools = TestTools()
        self.is_busy = False
        self.current_task: Optional[Task] = None
    
    @abstractmethod
    async def process_task(self, task: Task) -> AgentResponse:
        """Process a task and return a response."""
        pass
    
    async def send_message(self, to_agent: AgentType, message_type: str, content: Dict[str, Any], task_id: Optional[str] = None) -> AgentMessage:
        """Send a message to another agent."""
        message = AgentMessage(
            from_agent=self.agent_type,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            task_id=task_id
        )
        
        logger.info(f"Agent {self.agent_type.value} sending {message_type} to {to_agent.value}")
        return message
    
    async def analyze_project_context(self, project_path: str) -> Dict[str, Any]:
        """Analyze the current project context."""
        try:
            # Get git status
            git_status = await self.git_tools.get_status(project_path)
            
            # Get project structure
            project_files = await self.file_tools.list_directory(project_path)
            
            # Look for key files
            key_files = []
            for file_info in project_files:
                if file_info["name"] in [
                    "requirements.txt", "pyproject.toml", "package.json", 
                    "README.md", "setup.py", "main.py", "app.py"
                ]:
                    key_files.append(file_info)
            
            return {
                "project_path": project_path,
                "git_status": git_status,
                "project_files": project_files,
                "key_files": key_files,
                "analysis_timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error analyzing project context: {e}")
            return {"error": str(e)}
    
    async def validate_task(self, task: Task) -> bool:
        """Validate if the task can be processed by this agent."""
        # Basic validation - can be overridden by subclasses
        return task.status.value == "pending" and not self.is_busy
    
    async def update_task_status(self, task: Task, status: str, metadata: Optional[Dict[str, Any]] = None) -> Task:
        """Update task status and metadata."""
        task.status = status
        task.updated_at = datetime.now()
        
        if metadata:
            task.metadata.update(metadata)
        
        return task
    
    async def log_activity(self, activity: str, details: Optional[Dict[str, Any]] = None):
        """Log agent activity."""
        log_data = {
            "agent": self.agent_type.value,
            "activity": activity,
            "timestamp": datetime.now().isoformat(),
            "task_id": self.current_task.id if self.current_task else None
        }
        
        if details:
            log_data.update(details)
        
        logger.info(f"Agent {self.agent_type.value}: {activity}", extra=log_data)
    
    async def handle_error(self, error: Exception, task: Task) -> AgentResponse:
        """Handle errors and return appropriate response."""
        logger.error(f"Agent {self.agent_type.value} error in task {task.id}: {error}")
        
        return AgentResponse(
            agent_type=self.agent_type,
            task_id=task.id,
            success=False,
            result=None,
            error=str(error),
            suggestions=["Check logs for detailed error information", "Verify task requirements"]
        )
    
    async def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and status."""
        return {
            "agent_type": self.agent_type.value,
            "is_busy": self.is_busy,
            "current_task": self.current_task.id if self.current_task else None,
            "capabilities": self._get_capabilities(),
            "status": "active"
        }
    
    @abstractmethod
    def _get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        pass
