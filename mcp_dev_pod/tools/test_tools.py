"""Testing tools for the MCP Multi-Agent Developer Pod."""

import asyncio
import subprocess
import os
import logging
from typing import Dict, Any, List, Optional
import json
import tempfile
import uuid

from .file_tools import FileTools

logger = logging.getLogger(__name__)


class TestTools:
    """Testing operations for the development pod."""
    
    def __init__(self):
        self.file_tools = FileTools()
    
    async def run_tests(self, path: str = ".", pattern: str = "test_*.py") -> Dict[str, Any]:
        """Run tests using pytest."""
        try:
            # Find test files
            test_files = await self._find_test_files(path, pattern)
            
            if not test_files:
                return {
                    "success": False,
                    "error": f"No test files found matching pattern '{pattern}' in {path}",
                    "test_files": []
                }
            
            # Run pytest
            cmd = ["python", "-m", "pytest", "-v", "--tb=short", "--json-report", "--json-report-file=test_report.json"]
            cmd.extend(test_files)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path
            )
            
            stdout, stderr = await process.communicate()
            
            # Try to read JSON report if it exists
            report = None
            try:
                if os.path.exists("test_report.json"):
                    with open("test_report.json", "r") as f:
                        report = json.load(f)
                    os.remove("test_report.json")  # Clean up
            except Exception:
                pass
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8'),
                "error": stderr.decode('utf-8'),
                "return_code": process.returncode,
                "test_files": test_files,
                "report": report
            }
        
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_files": []
            }
    
    async def create_test(self, test_path: str, test_content: str) -> Dict[str, Any]:
        """Create a new test file."""
        try:
            # Validate and fix test path
            if not test_path or test_path.strip() == "":
                test_path = f"test_{uuid.uuid4().hex[:8]}.py"
            
            # Ensure test path has proper extension
            if not test_path.endswith('.py'):
                test_path = f"{test_path}.py"
            
            # Ensure path is relative to current directory
            if not test_path.startswith('./') and not test_path.startswith('/'):
                test_path = f"./{test_path}"
            
            result = await self.file_tools.write_file(test_path, test_content)
            
            if result["success"]:
                return {
                    "success": True,
                    "test_path": test_path,
                    "message": "Test file created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": result["error"]
                }
        
        except Exception as e:
            logger.error(f"Error creating test file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_specific_test(self, test_file: str, test_function: Optional[str] = None) -> Dict[str, Any]:
        """Run a specific test file or function."""
        try:
            cmd = ["python", "-m", "pytest", "-v", "--tb=short"]
            
            if test_function:
                cmd.append(f"{test_file}::{test_function}")
            else:
                cmd.append(test_file)
            
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
                "test_file": test_file,
                "test_function": test_function
            }
        
        except Exception as e:
            logger.error(f"Error running specific test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_test_template(self, module_path: str, test_path: str) -> Dict[str, Any]:
        """Generate a test template for a module."""
        try:
            # Read the module to analyze its functions
            module_content = await self.file_tools.read_file(module_path)
            
            # Simple analysis to find functions and classes
            lines = module_content.split('\n')
            functions = []
            classes = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('def ') and not line.startswith('def _'):
                    func_name = line.split('(')[0].replace('def ', '')
                    functions.append(func_name)
                elif line.startswith('class ') and not line.startswith('class _'):
                    class_name = line.split('(')[0].replace('class ', '').replace(':', '')
                    classes.append(class_name)
            
            # Generate test template
            test_template = self._generate_test_content(module_path, functions, classes)
            
            # Write test file
            result = await self.file_tools.write_file(test_path, test_template)
            
            if result["success"]:
                return {
                    "success": True,
                    "test_path": test_path,
                    "module_path": module_path,
                    "functions_found": functions,
                    "classes_found": classes
                }
            else:
                return {
                    "success": False,
                    "error": result["error"]
                }
        
        except Exception as e:
            logger.error(f"Error generating test template: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_test_content(self, module_path: str, functions: List[str], classes: List[str]) -> str:
        """Generate test file content."""
        module_name = os.path.basename(module_path).replace('.py', '')
        
        content = f'''"""Tests for {module_name} module."""

import pytest
import sys
import os

# Add the module path to sys.path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from {module_name} import *
'''
        
        # Add class tests
        for class_name in classes:
            content += f'''

class Test{class_name}:
    """Test cases for {class_name} class."""
    
    def test_{class_name.lower()}_initialization(self):
        """Test {class_name} initialization."""
        # TODO: Implement test
        pass
    
    def test_{class_name.lower()}_methods(self):
        """Test {class_name} methods."""
        # TODO: Implement test
        pass
'''
        
        # Add function tests
        for func_name in functions:
            content += f'''

def test_{func_name}():
    """Test {func_name} function."""
    # TODO: Implement test
    pass
'''
        
        content += '''

if __name__ == "__main__":
    pytest.main([__file__])
'''
        
        return content
    
    async def _find_test_files(self, path: str, pattern: str) -> List[str]:
        """Find test files matching the pattern."""
        try:
            import fnmatch
            
            test_files = []
            
            if os.path.isfile(path):
                if fnmatch.fnmatch(os.path.basename(path), pattern):
                    test_files.append(path)
            else:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if fnmatch.fnmatch(file, pattern):
                            test_files.append(os.path.join(root, file))
            
            return test_files
        
        except Exception as e:
            logger.error(f"Error finding test files: {e}")
            return []
    
    async def get_test_coverage(self, path: str = ".") -> Dict[str, Any]:
        """Get test coverage information."""
        try:
            cmd = ["python", "-m", "pytest", "--cov=.", "--cov-report=json", "--cov-report=term"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path
            )
            
            stdout, stderr = await process.communicate()
            
            # Try to read coverage report
            coverage_report = None
            try:
                if os.path.exists("coverage.json"):
                    with open("coverage.json", "r") as f:
                        coverage_report = json.load(f)
            except Exception:
                pass
            
            return {
                "success": True,
                "output": stdout.decode('utf-8'),
                "error": stderr.decode('utf-8'),
                "coverage_report": coverage_report
            }
        
        except Exception as e:
            logger.error(f"Error getting test coverage: {e}")
            return {
                "success": False,
                "error": str(e)
            }
