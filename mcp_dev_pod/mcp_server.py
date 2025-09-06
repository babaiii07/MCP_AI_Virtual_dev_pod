"""MCP Server implementation for the Multi-Agent Developer Pod."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult, ListToolsRequest, ListToolsResult,
    ListResourcesRequest, ListResourcesResult, ReadResourceRequest, ReadResourceResult
)

from .config import config
from .models import Task, AgentType, ProjectContext
from .tools.git_tools import GitTools
from .tools.file_tools import FileTools
from .tools.python_tools import PythonTools
from .tools.test_tools import TestTools

logger = logging.getLogger(__name__)


class MCPDevPodServer:
    """MCP Server for the Multi-Agent Developer Pod."""
    
    def __init__(self):
        self.server = Server("mcp-dev-pod")
        self.git_tools = GitTools()
        self.file_tools = FileTools()
        self.python_tools = PythonTools()
        self.test_tools = TestTools()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="git_status",
                    description="Get git repository status",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to git repository"
                            }
                        }
                    }
                ),
                Tool(
                    name="git_commit",
                    description="Commit changes to git",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Commit message"
                            },
                            "path": {
                                "type": "string",
                                "description": "Path to git repository"
                            }
                        },
                        "required": ["message"]
                    }
                ),
                Tool(
                    name="read_file",
                    description="Read file contents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to file to read"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="write_file",
                    description="Write content to file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to file to write"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write"
                            }
                        },
                        "required": ["path", "content"]
                    }
                ),
                Tool(
                    name="list_directory",
                    description="List directory contents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to directory"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="execute_python",
                    description="Execute Python code",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute"
                            },
                            "timeout": {
                                "type": "number",
                                "description": "Execution timeout in seconds",
                                "default": 30
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="run_tests",
                    description="Run tests in the project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to test directory or file"
                            },
                            "pattern": {
                                "type": "string",
                                "description": "Test pattern to match",
                                "default": "test_*.py"
                            }
                        }
                    }
                ),
                Tool(
                    name="create_test",
                    description="Create a new test file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "test_path": {
                                "type": "string",
                                "description": "Path for the test file"
                            },
                            "test_content": {
                                "type": "string",
                                "description": "Test content to write"
                            }
                        },
                        "required": ["test_path", "test_content"]
                    }
                ),
                Tool(
                    name="analyze_project",
                    description="Analyze project structure and dependencies",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to project root"
                            }
                        },
                        "required": ["path"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "git_status":
                    result = await self.git_tools.get_status(arguments.get("path", "."))
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "git_commit":
                    result = await self.git_tools.commit(
                        arguments["message"],
                        arguments.get("path", ".")
                    )
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "read_file":
                    result = await self.file_tools.read_file(arguments["path"])
                    return [TextContent(type="text", text=result)]
                
                elif name == "write_file":
                    result = await self.file_tools.write_file(
                        arguments["path"],
                        arguments["content"]
                    )
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "list_directory":
                    result = await self.file_tools.list_directory(arguments["path"])
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "execute_python":
                    result = await self.python_tools.execute_code(
                        arguments["code"],
                        arguments.get("timeout", 30)
                    )
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "run_tests":
                    result = await self.test_tools.run_tests(
                        arguments.get("path", "."),
                        arguments.get("pattern", "test_*.py")
                    )
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "create_test":
                    result = await self.test_tools.create_test(
                        arguments["test_path"],
                        arguments["test_content"]
                    )
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "analyze_project":
                    result = await self._analyze_project(arguments["path"])
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _analyze_project(self, path: str) -> Dict[str, Any]:
        """Analyze project structure and dependencies."""
        try:
            # Get project structure
            files = await self.file_tools.list_directory(path)
            
            # Get git info
            git_status = await self.git_tools.get_status(path)
            
            # Look for dependency files
            dependencies = []
            for file_info in files:
                if file_info["name"] in ["requirements.txt", "pyproject.toml", "package.json", "Cargo.toml"]:
                    content = await self.file_tools.read_file(file_info["path"])
                    dependencies.append({
                        "file": file_info["name"],
                        "content": content
                    })
            
            return {
                "project_path": path,
                "files": files,
                "git_status": git_status,
                "dependencies": dependencies,
                "analysis_timestamp": asyncio.get_event_loop().time()
            }
        
        except Exception as e:
            logger.error(f"Error analyzing project: {e}")
            return {"error": str(e)}
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-dev-pod",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Main entry point for the MCP server."""
    server = MCPDevPodServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
