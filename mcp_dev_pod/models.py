"""Data models for the MCP Multi-Agent Developer Pod."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    """Agent type enumeration."""
    PLANNER = "planner"
    CODER = "coder"
    TESTER = "tester"


class Task(BaseModel):
    """Represents a development task."""
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[AgentType] = None
    dependencies: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentMessage(BaseModel):
    """Message between agents."""
    from_agent: AgentType
    to_agent: AgentType
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    task_id: Optional[str] = None


class CodeChange(BaseModel):
    """Represents a code change."""
    file_path: str
    change_type: str  # "create", "modify", "delete"
    content: Optional[str] = None
    diff: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestResult(BaseModel):
    """Represents a test result."""
    test_name: str
    status: str  # "passed", "failed", "skipped"
    output: str
    duration: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectContext(BaseModel):
    """Project context information."""
    project_path: str
    git_branch: str
    git_commit: str
    files: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Response from an agent."""
    agent_type: AgentType
    task_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
