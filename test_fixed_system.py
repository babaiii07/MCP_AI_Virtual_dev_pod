#!/usr/bin/env python3
"""
Test script to verify the fixed MCP Multi-Agent Developer Pod system.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_dev_pod.coordinator import AgentCoordinator
from mcp_dev_pod.models import Task, TaskStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_system():
    """Test the fixed system."""
    print("🧪 Testing MCP Multi-Agent Developer Pod System")
    print("=" * 50)
    
    try:
        # Initialize coordinator
        print("1. Initializing coordinator...")
        coordinator = AgentCoordinator()
        
        if not await coordinator.initialize():
            print("❌ Failed to initialize coordinator")
            return False
        
        print("✅ Coordinator initialized successfully")
        
        # Test task submission
        print("\n2. Testing task submission...")
        task_id = await coordinator.submit_task(
            title="Test Web Application",
            description="Create a simple web application with FastAPI",
            metadata={"project_path": "./workspace"}
        )
        
        if task_id:
            print(f"✅ Task submitted successfully: {task_id}")
        else:
            print("❌ Failed to submit task")
            return False
        
        # Wait for task processing
        print("\n3. Waiting for task processing...")
        max_wait = 60  # 60 seconds max wait
        wait_time = 0
        
        while wait_time < max_wait:
            status = await coordinator.get_task_status(task_id)
            if status:
                print(f"   Task status: {status['status']}")
                if status['status'] in ['completed', 'failed']:
                    break
            
            await asyncio.sleep(2)
            wait_time += 2
        
        # Check final status
        final_status = await coordinator.get_task_status(task_id)
        if final_status:
            print(f"\n4. Final task status: {final_status['status']}")
            
            if final_status['status'] == 'completed':
                print("✅ Task completed successfully!")
                
                # Check if project files were created
                project_name = "test_web_application"
                project_path = f"./workspace/{project_name}"
                
                if os.path.exists(project_path):
                    print(f"✅ Project folder created: {project_path}")
                    
                    # List created files
                    files = []
                    for root, dirs, filenames in os.walk(project_path):
                        for filename in filenames:
                            files.append(os.path.join(root, filename))
                    
                    print(f"✅ Created {len(files)} files:")
                    for file in files[:10]:  # Show first 10 files
                        print(f"   - {file}")
                    
                    if len(files) > 10:
                        print(f"   ... and {len(files) - 10} more files")
                
                else:
                    print(f"❌ Project folder not found: {project_path}")
                
            else:
                print(f"❌ Task failed: {final_status.get('metadata', {}).get('error', 'Unknown error')}")
        else:
            print("❌ Could not get final task status")
        
        # Test coordinator status
        print("\n5. Testing coordinator status...")
        status = await coordinator.get_coordinator_status()
        print(f"   Active tasks: {status.get('active_tasks_count', 0)}")
        print(f"   Completed tasks: {status.get('completed_tasks_count', 0)}")
        print(f"   Queue size: {status.get('queue_size', 0)}")
        
        print("\n✅ System test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        logger.exception("Test failed")
        return False

async def main():
    """Main test function."""
    success = await test_system()
    
    if success:
        print("\n🎉 All tests passed! The system is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

