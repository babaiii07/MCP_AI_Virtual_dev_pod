"""Basic usage example for MCP Multi-Agent Developer Pod."""

import asyncio
import logging
from mcp_dev_pod.coordinator import AgentCoordinator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Basic usage example."""
    # Initialize coordinator
    coordinator = AgentCoordinator()
    
    if not await coordinator.initialize():
        logger.error("Failed to initialize coordinator")
        return
    
    # Submit a simple task
    task_id = await coordinator.submit_task(
        title="Create a simple calculator",
        description="Implement a basic calculator with add, subtract, multiply, and divide operations",
        metadata={"project_path": "./workspace"}
    )
    
    logger.info(f"Task submitted: {task_id}")
    
    # Check task status
    status = await coordinator.get_task_status(task_id)
    logger.info(f"Task status: {status}")
    
    # Get coordinator status
    coordinator_status = await coordinator.get_coordinator_status()
    logger.info(f"Coordinator status: {coordinator_status}")
    
    # List all tasks
    all_tasks = await coordinator.get_all_tasks()
    logger.info(f"All tasks: {all_tasks}")


if __name__ == "__main__":
    asyncio.run(main())
