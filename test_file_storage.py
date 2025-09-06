"""Test file storage functionality directly."""

import asyncio
import os
import shutil
from mcp_dev_pod.coordinator import AgentCoordinator

async def test_file_storage():
    """Test that files are properly stored when tasks are processed."""
    print("🚀 Testing File Storage...")
    
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
    
    # Submit a simple task
    print("📝 Submitting test task...")
    task_id = await coordinator.submit_task(
        title="Create a simple calculator",
        description="Build a basic calculator with add, subtract, multiply, and divide operations",
        metadata={"project_path": "./workspace"}
    )
    
    print(f"✅ Task submitted! Task ID: {task_id}")
    
    # Start the coordinator to process tasks
    print("🔄 Starting coordinator to process tasks...")
    
    # Create a task to process the queue
    async def process_single_task():
        try:
            # Get the task from the queue
            task = await coordinator.task_queue.get()
            print(f"📋 Processing task: {task.id}")
            
            # Process the task directly
            await coordinator._process_task(task)
            
            print("✅ Task processed successfully!")
            
        except Exception as e:
            print(f"❌ Error processing task: {e}")
    
    # Process the task
    await process_single_task()
    
    # Check if files were created
    if os.path.exists("./workspace"):
        print("📁 Checking generated files...")
        files = []
        for root, dirs, filenames in os.walk("./workspace"):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                files.append(file_path)
        
        print(f"✅ Generated {len(files)} files:")
        for file_path in sorted(files):
            print(f"   📄 {file_path}")
        
        # Check file contents
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"   📄 {file_path}: {len(content)} characters")
            except Exception as e:
                print(f"   ❌ Error reading {file_path}: {e}")
    
    else:
        print("❌ No workspace directory created")
    
    print("🎉 File storage test completed!")

if __name__ == "__main__":
    asyncio.run(test_file_storage())
