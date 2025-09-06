"""Test the enhanced MCP Multi-Agent Developer Pod system."""

import asyncio
import os
import shutil
from mcp_dev_pod.coordinator import AgentCoordinator

async def test_enhanced_system():
    """Test the enhanced system with a blog project."""
    print("🚀 Testing Enhanced MCP Multi-Agent Developer Pod...")
    
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
    
    # Submit a blog project task
    print("📝 Submitting blog project task...")
    task_id = await coordinator.submit_task(
        title="Build a Modern Blog Website",
        description="Create a complete blog application with user authentication, post creation, comments, and admin panel. Include FastAPI backend, modern frontend, database models, and Docker deployment.",
        metadata={"project_path": "./workspace", "project_type": "blog"}
    )
    
    print(f"✅ Task submitted! Task ID: {task_id}")
    
    # Monitor task progress
    print("📊 Monitoring task progress...")
    max_wait_time = 120  # 2 minutes
    wait_interval = 5    # 5 seconds
    elapsed_time = 0
    
    while elapsed_time < max_wait_time:
        status = await coordinator.get_task_status(task_id)
        print(f"⏱️  [{elapsed_time}s] Task status: {status['status']}")
        
        if status['status'] == 'completed':
            print("🎉 Task completed successfully!")
            break
        elif status['status'] == 'failed':
            print("❌ Task failed!")
            break
        
        await asyncio.sleep(wait_interval)
        elapsed_time += wait_interval
    
    # Check final status
    final_status = await coordinator.get_task_status(task_id)
    print(f"📋 Final task status: {final_status['status']}")
    
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
        
        # Check for key files
        key_files = [
            "app.py",
            "requirements.txt", 
            "Dockerfile",
            "templates/index.html",
            "static/css/style.css",
            "static/js/app.js",
            "README.md"
        ]
        
        missing_files = []
        for key_file in key_files:
            if not any(key_file in f for f in files):
                missing_files.append(key_file)
        
        if missing_files:
            print(f"⚠️  Missing key files: {missing_files}")
        else:
            print("✅ All key files generated successfully!")
        
        # Check file sizes
        print("📊 File sizes:")
        for file_path in sorted(files):
            try:
                size = os.path.getsize(file_path)
                print(f"   📄 {file_path}: {size} bytes")
            except:
                print(f"   📄 {file_path}: Unable to get size")
    
    else:
        print("❌ No workspace directory created")
    
    print("🎉 Enhanced system test completed!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_system())
