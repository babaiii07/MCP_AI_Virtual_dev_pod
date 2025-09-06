"""Test the project generator directly."""

import asyncio
import os
from mcp_dev_pod.project_generator import ProjectGenerator
from mcp_dev_pod.models import Task

async def test_project_generator():
    """Test the project generator directly."""
    print("🚀 Testing Project Generator...")
    
    # Create a test task
    task = Task(
        id="test-blog-001",
        title="Build a Modern Blog Website",
        description="Create a complete blog application with user authentication, post creation, comments, and admin panel.",
        status="pending",
        metadata={"project_path": "./workspace", "project_type": "blog"}
    )
    
    # Initialize project generator
    generator = ProjectGenerator()
    
    # Generate project structure
    print("📋 Generating project structure...")
    files = await generator.generate_project_structure(task)
    
    print(f"✅ Generated {len(files)} files:")
    for file_info in files:
        print(f"   📄 {file_info['file_path']} ({file_info['type']})")
        print(f"      Content length: {len(file_info['content'])} characters")
    
    # Create workspace directory
    os.makedirs("./workspace", exist_ok=True)
    
    # Write files to workspace
    print("📝 Writing files to workspace...")
    for file_info in files:
        file_path = os.path.join("./workspace", file_info["file_path"])
        
        # Create directory if needed
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_info["content"])
        
        print(f"   ✅ Created: {file_path}")
    
    print("🎉 Project generator test completed!")
    print(f"📁 Check the './workspace' directory for generated files")

if __name__ == "__main__":
    asyncio.run(test_project_generator())

