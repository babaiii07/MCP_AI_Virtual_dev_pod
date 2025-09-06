"""Python execution tools for the MCP Multi-Agent Developer Pod."""

import asyncio
import subprocess
import sys
import tempfile
import os
import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class PythonTools:
    """Python code execution for the development pod."""
    
    def __init__(self):
        self.python_executable = sys.executable
    
    async def execute_code(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute Python code safely."""
        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute the code
                result = await asyncio.wait_for(
                    self._run_python_file(temp_file),
                    timeout=timeout
                )
                
                return {
                    "success": True,
                    "output": result["output"],
                    "error": result["error"],
                    "return_code": result["return_code"],
                    "execution_time": result["execution_time"]
                }
            
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass
        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Code execution timed out after {timeout} seconds",
                "output": "",
                "return_code": -1
            }
        except Exception as e:
            logger.error(f"Error executing Python code: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "return_code": -1
            }
    
    async def _run_python_file(self, file_path: str) -> Dict[str, Any]:
        """Run a Python file and capture output."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                self.python_executable, file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "output": stdout.decode('utf-8'),
                "error": stderr.decode('utf-8'),
                "return_code": process.returncode,
                "execution_time": execution_time
            }
        
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            return {
                "output": "",
                "error": str(e),
                "return_code": -1,
                "execution_time": execution_time
            }
    
    async def install_package(self, package: str) -> Dict[str, Any]:
        """Install a Python package."""
        try:
            process = await asyncio.create_subprocess_exec(
                self.python_executable, "-m", "pip", "install", package,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8'),
                "error": stderr.decode('utf-8'),
                "package": package
            }
        
        except Exception as e:
            logger.error(f"Error installing package {package}: {e}")
            return {
                "success": False,
                "error": str(e),
                "package": package
            }
    
    async def check_syntax(self, code: str) -> Dict[str, Any]:
        """Check Python code syntax."""
        try:
            compile(code, '<string>', 'exec')
            return {
                "success": True,
                "syntax_valid": True,
                "error": None
            }
        except SyntaxError as e:
            return {
                "success": True,
                "syntax_valid": False,
                "error": {
                    "message": str(e),
                    "line": e.lineno,
                    "column": e.offset,
                    "text": e.text
                }
            }
        except Exception as e:
            return {
                "success": False,
                "syntax_valid": False,
                "error": str(e)
            }
    
    async def run_script(self, script_path: str, args: Optional[list] = None) -> Dict[str, Any]:
        """Run a Python script with arguments."""
        try:
            cmd = [self.python_executable, script_path]
            if args:
                cmd.extend(args)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8'),
                "error": stderr.decode('utf-8'),
                "return_code": process.returncode,
                "script": script_path,
                "args": args or []
            }
        
        except Exception as e:
            logger.error(f"Error running script {script_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "script": script_path,
                "args": args or []
            }
    
    async def get_python_info(self) -> Dict[str, Any]:
        """Get Python environment information."""
        try:
            import platform
            import sys
            
            # Get installed packages
            process = await asyncio.create_subprocess_exec(
                self.python_executable, "-m", "pip", "list", "--format=json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            packages = []
            
            if process.returncode == 0:
                try:
                    packages = json.loads(stdout.decode('utf-8'))
                except json.JSONDecodeError:
                    packages = []
            
            return {
                "python_version": sys.version,
                "python_executable": sys.executable,
                "platform": platform.platform(),
                "architecture": platform.architecture(),
                "packages": packages[:20],  # Limit to first 20 packages
                "total_packages": len(packages)
            }
        
        except Exception as e:
            logger.error(f"Error getting Python info: {e}")
            return {
                "error": str(e)
            }
