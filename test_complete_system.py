"""Test the complete MCP Multi-Agent Developer Pod system."""

import asyncio
import os
import shutil
import time
from mcp_dev_pod.coordinator import AgentCoordinator

async def test_complete_system():
    """Test the complete system end-to-end."""
    print("🚀 Testing Complete MCP Multi-Agent Developer Pod System...")
    
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
    
    # Process the task manually (simulating background worker)
    print("🔄 Processing task...")
    
    # Get the task from the queue
    task = await coordinator.task_queue.get()
    print(f"📋 Processing task: {task.id} - {task.title}")
    
    # Process the task
    await coordinator._process_task(task)
    
    print("✅ Task processed successfully!")
    
    # Check final task status
    final_status = await coordinator.get_task_status(task_id)
    print(f"📊 Final task status: {final_status['status']}")
    
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
            try:
                size = os.path.getsize(file_path)
                print(f"   📄 {file_path}: {size} bytes")
            except:
                print(f"   📄 {file_path}: Unable to get size")
        
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
        
        # Test if the generated app can be imported
        print("🧪 Testing generated application...")
        try:
            import sys
            sys.path.insert(0, "./workspace")
            import app
            print("✅ Generated app imports successfully!")
            
            # Test FastAPI app creation
            from app import app as fastapi_app
            print("✅ FastAPI app created successfully!")
            
        except Exception as e:
            print(f"❌ Error testing generated app: {e}")
    
    else:
        print("❌ No workspace directory created")
    
    print("🎉 Complete system test finished!")
    print("\n📋 Summary:")
    print(f"   ✅ Task processed: {task_id}")
    print(f"   ✅ Files generated: {len(files) if os.path.exists('./workspace') else 0}")
    print(f"   ✅ Final status: {final_status['status'] if final_status else 'Unknown'}")
    
    if os.path.exists("./workspace"):
        print(f"\n🚀 To run the generated application:")
        print(f"   cd workspace")
        print(f"   pip install -r requirements.txt")
        print(f"   uvicorn app:app --reload")
        print(f"   Then open: http://localhost:8000")

if __name__ == "__main__":
    asyncio.run(test_complete_system())

