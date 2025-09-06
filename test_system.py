"""Quick test of the MCP Multi-Agent Developer Pod system."""

import asyncio
import os
from mcp_dev_pod.coordinator import AgentCoordinator

async def test_system():
    """Test the system with a simple task."""
    print("🚀 Testing MCP Multi-Agent Developer Pod...")
    
    # Initialize coordinator
    coordinator = AgentCoordinator()
    print("📋 Initializing coordinator...")
    
    success = await coordinator.initialize()
    if not success:
        print("❌ Failed to initialize coordinator")
        return
    
    print("✅ Coordinator initialized successfully!")
    
    # Submit a simple task
    print("📝 Submitting test task...")
    task_id = await coordinator.submit_task(
        title="Create a simple calculator",
        description="Build a basic calculator with add, subtract, multiply, and divide operations",
        metadata={"project_path": "./workspace"}
    )
    
    print(f"✅ Task submitted! Task ID: {task_id}")
    
    # Check task status
    print("📊 Checking task status...")
    status = await coordinator.get_task_status(task_id)
    print(f"Task status: {status}")
    
    # Wait a bit and check again
    print("⏳ Waiting 10 seconds for processing...")
    await asyncio.sleep(10)
    
    status = await coordinator.get_task_status(task_id)
    print(f"Updated task status: {status}")
    
    # Check if any files were created
    if os.path.exists("./workspace"):
        files = os.listdir("./workspace")
        print(f"📁 Files created in workspace: {files}")
    
    print("🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_system())
