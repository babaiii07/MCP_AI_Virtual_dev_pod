"""Debug the coordinator to see what's happening."""

import asyncio
import os
import shutil
from mcp_dev_pod.coordinator import AgentCoordinator
from mcp_dev_pod.models import Task, AgentType, TaskStatus

async def debug_coordinator():
    """Debug the coordinator to see what's happening."""
    print("🔍 Debugging Coordinator...")
    
    # Clean up any existing workspace
    if os.path.exists("./workspace"):
        shutil.rmtree("./workspace")
    
    # Initialize coordinator
    coordinator = AgentCoordinator()
    print("📋 Initializing coordinator...")
    
    success = await coordinator.initialize()
    if not success:
        print("❌ Failed to initialize coordinator")
        return
    
    print("✅ Coordinator initialized successfully!")
    
    # Create a test task
    task = Task(
        id="debug-task-001",
        title="Build a Modern Blog Website",
        description="Create a complete blog application with user authentication, post creation, comments, and admin panel.",
        status=TaskStatus.PENDING,
        metadata={"project_path": "./workspace", "project_type": "blog"}
    )
    
    print(f"📋 Created task: {task.id} - {task.title}")
    
    # Test agent assignment
    print("🔧 Testing agent assignment...")
    assigned_agent = await coordinator._assign_agent(task)
    print(f"🤖 Assigned agent: {assigned_agent}")
    
    if assigned_agent:
        print(f"✅ Task assigned to: {assigned_agent.value}")
        
        # Get the agent
        agent = coordinator.agents[assigned_agent]
        print(f"🤖 Got agent: {type(agent).__name__}")
        
        # Process the task
        print("🔄 Processing task with agent...")
        response = await agent.process_task(task)
        print(f"📊 Agent response: Success={response.success}")
        
        if response.success:
            print("✅ Task processed successfully!")
            print(f"📊 Response result keys: {list(response.result.keys()) if response.result else 'None'}")
        else:
            print("❌ Task processing failed!")
            print(f"📊 Error: {response.error if hasattr(response, 'error') else 'Unknown'}")
    
    else:
        print("❌ No agent assigned!")
    
    # Check if files were created
    if os.path.exists("./workspace"):
        print("📁 Files created in workspace:")
        for root, dirs, filenames in os.walk("./workspace"):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                size = os.path.getsize(file_path)
                print(f"   📄 {file_path}: {size} bytes")
    else:
        print("❌ No workspace directory created")
    
    print("🎉 Debug completed!")

if __name__ == "__main__":
    asyncio.run(debug_coordinator())

