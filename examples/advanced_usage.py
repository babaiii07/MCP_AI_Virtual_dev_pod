"""Advanced usage example for MCP Multi-Agent Developer Pod."""

import asyncio
import logging
from mcp_dev_pod.coordinator import AgentCoordinator
from mcp_dev_pod.models import Task, AgentType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Advanced usage example with multiple tasks and agent coordination."""
    # Initialize coordinator
    coordinator = AgentCoordinator()
    
    if not await coordinator.initialize():
        logger.error("Failed to initialize coordinator")
        return
    
    # Submit multiple related tasks
    tasks = [
        {
            "title": "Design REST API",
            "description": "Design a REST API for a todo application with CRUD operations",
            "metadata": {"project_path": "./workspace", "type": "planning"}
        },
        {
            "title": "Implement API endpoints",
            "description": "Implement the REST API endpoints for todo operations",
            "metadata": {"project_path": "./workspace", "type": "coding"}
        },
        {
            "title": "Write API tests",
            "description": "Write comprehensive tests for the REST API",
            "metadata": {"project_path": "./workspace", "type": "testing"}
        }
    ]
    
    task_ids = []
    for task_data in tasks:
        task_id = await coordinator.submit_task(**task_data)
        task_ids.append(task_id)
        logger.info(f"Task submitted: {task_id} - {task_data['title']}")
    
    # Monitor task progress
    while True:
        all_tasks = await coordinator.get_all_tasks()
        active_count = len(all_tasks["active_tasks"])
        completed_count = len(all_tasks["completed_tasks"])
        
        logger.info(f"Active tasks: {active_count}, Completed: {completed_count}")
        
        if active_count == 0:
            break
        
        await asyncio.sleep(5)  # Check every 5 seconds
    
    # Get final results
    final_tasks = await coordinator.get_all_tasks()
    logger.info("All tasks completed!")
    
    for task_id, task_info in final_tasks["completed_tasks"].items():
        logger.info(f"Completed: {task_info['title']} - Status: {task_info['status']}")


if __name__ == "__main__":
    asyncio.run(main())
