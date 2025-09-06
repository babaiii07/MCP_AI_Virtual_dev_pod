"""Debug the coder agent to see what's happening."""

import asyncio
import os
import shutil
from mcp_dev_pod.coordinator import AgentCoordinator
from mcp_dev_pod.models import Task, AgentType

async def debug_coder_agent():
    """Debug the coder agent to see what's happening."""
    print("🔍 Debugging Coder Agent...")
    
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
        status="pending",
        metadata={"project_path": "./workspace", "project_type": "blog"}
    )
    
    # Get the coder agent
    coder_agent = coordinator.agents[AgentType.CODER]
    print("🤖 Got coder agent")
    
    # Test the project generator directly
    print("🔧 Testing project generator...")
    from mcp_dev_pod.project_generator import ProjectGenerator
    project_generator = ProjectGenerator()
    project_files = await project_generator.generate_project_structure(task)
    print(f"📁 Project generator created {len(project_files)} files")
    
    for file_info in project_files:
        print(f"   📄 {file_info['file_path']} ({file_info['type']})")
    
    # Test the _generate_code method
    print("🔧 Testing _generate_code method...")
    requirements = await coder_agent._analyze_coding_requirements(task)
    print(f"📋 Requirements analysis: {len(requirements)} items")
    
    code_changes = await coder_agent._generate_code(task, requirements)
    print(f"📝 Generated {len(code_changes)} code changes")
    
    for change in code_changes:
        print(f"   📄 {change.file_path} ({change.change_type}) - {len(change.content or '')} chars")
    
    # Test applying code changes
    if code_changes:
        print("🔧 Testing _apply_code_changes method...")
        applied_changes = await coder_agent._apply_code_changes(code_changes)
        print(f"✅ Applied {len(applied_changes)} changes")
        
        for change in applied_changes:
            print(f"   📄 {change['file_path']} - Success: {change['success']}")
    
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
    asyncio.run(debug_coder_agent())
