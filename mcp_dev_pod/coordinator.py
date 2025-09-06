"""Agent coordinator for the MCP Multi-Agent Developer Pod."""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import uuid

from .models import Task, AgentType, AgentResponse, AgentMessage, TaskStatus
from .llm_client import LLMClient
from .agents.planner_agent import PlannerAgent
from .agents.coder_agent import CoderAgent
from .agents.tester_agent import TesterAgent
from .config import config

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """Coordinates multiple agents for autonomous development tasks."""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.agents = {}
        self.task_queue = asyncio.Queue()
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.message_queue = asyncio.Queue()
        self.is_running = False
        self.max_concurrent_tasks = config.max_concurrent_agents
        
    async def initialize(self) -> bool:
        """Initialize the coordinator and all agents."""
        try:
            # Initialize LLM client
            if not await self.llm_client.initialize():
                logger.error("Failed to initialize LLM client")
                return False
            
            # Initialize agents
            self.agents[AgentType.PLANNER] = PlannerAgent(self.llm_client)
            self.agents[AgentType.CODER] = CoderAgent(self.llm_client)
            self.agents[AgentType.TESTER] = TesterAgent(self.llm_client)
            
            logger.info("Agent coordinator initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing coordinator: {e}")
            return False
    
    async def start(self):
        """Start the coordinator and begin processing tasks."""
        if not await self.initialize():
            raise RuntimeError("Failed to initialize coordinator")
        
        self.is_running = True
        logger.info("Agent coordinator started")
        
        # Start background tasks
        await asyncio.gather(
            self._process_task_queue(),
            self._process_message_queue(),
            self._monitor_agents()
        )
    
    async def stop(self):
        """Stop the coordinator and all agents."""
        self.is_running = False
        logger.info("Agent coordinator stopped")
    
    async def submit_task(self, title: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Submit a new task to the coordinator."""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            title=title,
            description=description,
            metadata=metadata or {}
        )
        
        await self.task_queue.put(task)
        self.active_tasks[task_id] = task
        
        logger.info(f"Task submitted: {task_id} - {title}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
        elif task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
        else:
            return None
        
        return {
            "id": task.id,
            "title": task.title,
            "status": task.status.value,
            "assigned_agent": task.assigned_agent.value if task.assigned_agent else None,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "metadata": task.metadata
        }
    
    async def get_all_tasks(self) -> Dict[str, Any]:
        """Get all tasks (active and completed)."""
        return {
            "active_tasks": {
                task_id: await self.get_task_status(task_id)
                for task_id in self.active_tasks.keys()
            },
            "completed_tasks": {
                task_id: await self.get_task_status(task_id)
                for task_id in self.completed_tasks.keys()
            }
        }
    
    async def _process_task_queue(self):
        """Process tasks from the queue."""
        while self.is_running:
            try:
                # Wait for a task with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Check if we can process more tasks
                if len(self.active_tasks) >= self.max_concurrent_tasks:
                    # Put task back and wait
                    await self.task_queue.put(task)
                    await asyncio.sleep(2)  # Increased wait time
                    continue
                
                # Process the task
                asyncio.create_task(self._process_task(task))
                
            except asyncio.TimeoutError:
                # No tasks available, sleep briefly
                await asyncio.sleep(0.5)
                continue
            except Exception as e:
                logger.error(f"Error processing task queue: {e}")
                await asyncio.sleep(1)  # Wait before retrying
    
    async def _process_task(self, task: Task):
        """Process a single task."""
        try:
            logger.info(f"Processing task: {task.id} - {task.title}")
            
            # Determine which agent should handle this task
            assigned_agent = await self._assign_agent(task)
            if not assigned_agent:
                logger.error(f"No available agent for task: {task.id}")
                await self._mark_task_failed(task, "No available agent")
                return
            
            # Assign task to agent
            task.assigned_agent = assigned_agent
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = datetime.now()
            
            # Process with the assigned agent
            agent = self.agents[assigned_agent]
            response = await agent.process_task(task)
            
            # Handle the response
            await self._handle_agent_response(task, response)
            
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")
            await self._mark_task_failed(task, str(e))
    
    async def _assign_agent(self, task: Task) -> Optional[AgentType]:
        """Assign an agent to handle the task."""
        # Simple assignment logic - can be enhanced with more sophisticated routing
        task_lower = task.title.lower()
        description_lower = task.description.lower()
        combined_text = f"{task_lower} {description_lower}"
        
        if any(keyword in combined_text for keyword in ['plan', 'design', 'architecture', 'strategy']):
            return AgentType.PLANNER
        elif any(keyword in combined_text for keyword in ['test', 'testing', 'validate', 'verify']):
            return AgentType.TESTER
        elif any(keyword in combined_text for keyword in ['code', 'implement', 'develop', 'create', 'write', 'build', 'make', 'generate', 'app', 'website', 'application']):
            return AgentType.CODER
        else:
            # Default to coder for implementation tasks
            return AgentType.CODER
    
    async def _handle_agent_response(self, task: Task, response: AgentResponse):
        """Handle response from an agent."""
        try:
            if response.success:
                # Task completed successfully
                task.status = TaskStatus.COMPLETED
                task.metadata.update(response.result or {})
                
                # Move to completed tasks
                self.completed_tasks[task.id] = task
                if task.id in self.active_tasks:
                    del self.active_tasks[task.id]
                
                logger.info(f"Task completed successfully: {task.id}")
                
                # Check if we need to create follow-up tasks
                await self._create_follow_up_tasks(task, response)
                
            else:
                # Task failed
                await self._mark_task_failed(task, response.error or "Unknown error")
                
        except Exception as e:
            logger.error(f"Error handling agent response: {e}")
            await self._mark_task_failed(task, str(e))
    
    async def _mark_task_failed(self, task: Task, error: str):
        """Mark a task as failed."""
        task.status = TaskStatus.FAILED
        task.metadata["error"] = error
        task.updated_at = datetime.now()
        
        # Move to completed tasks
        self.completed_tasks[task.id] = task
        if task.id in self.active_tasks:
            del self.active_tasks[task.id]
        
        logger.error(f"Task failed: {task.id} - {error}")
    
    async def _create_follow_up_tasks(self, completed_task: Task, response: AgentResponse):
        """Create follow-up tasks based on agent response."""
        try:
            # Check if the response suggests follow-up tasks
            if not response.suggestions:
                return
            
            # Create tasks based on suggestions
            for suggestion in response.suggestions:
                if "test" in suggestion.lower():
                    # Create a testing task
                    test_task_id = await self.submit_task(
                        title=f"Test {completed_task.title}",
                        description=f"Create and run tests for: {completed_task.title}",
                        metadata={
                            "parent_task_id": completed_task.id,
                            "project_path": completed_task.metadata.get("project_path", ".")
                        }
                    )
                    logger.info(f"Created follow-up test task: {test_task_id}")
                
                elif "review" in suggestion.lower() or "check" in suggestion.lower():
                    # Create a review task
                    review_task_id = await self.submit_task(
                        title=f"Review {completed_task.title}",
                        description=f"Review and validate: {completed_task.title}",
                        metadata={
                            "parent_task_id": completed_task.id,
                            "project_path": completed_task.metadata.get("project_path", ".")
                        }
                    )
                    logger.info(f"Created follow-up review task: {review_task_id}")
        
        except Exception as e:
            logger.error(f"Error creating follow-up tasks: {e}")
    
    async def _process_message_queue(self):
        """Process messages between agents."""
        while self.is_running:
            try:
                # Wait for a message with timeout
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                # Process the message
                await self._handle_agent_message(message)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing message queue: {e}")
    
    async def _handle_agent_message(self, message: AgentMessage):
        """Handle a message between agents."""
        try:
            logger.info(f"Handling message from {message.from_agent.value} to {message.to_agent.value}")
            
            # Route message to appropriate agent
            if message.to_agent in self.agents:
                # In a more sophisticated implementation, we'd have agent message handlers
                logger.info(f"Message content: {message.content}")
            
        except Exception as e:
            logger.error(f"Error handling agent message: {e}")
    
    async def _monitor_agents(self):
        """Monitor agent health and status."""
        while self.is_running:
            try:
                for agent_type, agent in self.agents.items():
                    capabilities = await agent.get_agent_capabilities()
                    logger.debug(f"Agent {agent_type.value} status: {capabilities}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
            
            except Exception as e:
                logger.error(f"Error monitoring agents: {e}")
                await asyncio.sleep(30)
    
    async def send_message(self, from_agent: AgentType, to_agent: AgentType, message_type: str, content: Dict[str, Any], task_id: Optional[str] = None):
        """Send a message between agents."""
        message = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            task_id=task_id
        )
        
        await self.message_queue.put(message)
    
    async def get_coordinator_status(self) -> Dict[str, Any]:
        """Get coordinator status and statistics."""
        return {
            "is_running": self.is_running,
            "active_tasks_count": len(self.active_tasks),
            "completed_tasks_count": len(self.completed_tasks),
            "queue_size": self.task_queue.qsize(),
            "message_queue_size": self.message_queue.qsize(),
            "agents": {
                agent_type.value: await agent.get_agent_capabilities()
                for agent_type, agent in self.agents.items()
            },
            "max_concurrent_tasks": self.max_concurrent_tasks
        }
