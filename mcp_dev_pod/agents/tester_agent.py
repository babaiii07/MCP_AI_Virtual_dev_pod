"""Tester agent for the MCP Multi-Agent Developer Pod."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import json
import os
import uuid

from .base_agent import BaseAgent
from ..models import Task, AgentType, AgentResponse, TaskStatus, TestResult

logger = logging.getLogger(__name__)


class TesterAgent(BaseAgent):
    """Tester agent that writes and runs tests."""
    
    def __init__(self, llm_client):
        super().__init__(AgentType.TESTER, llm_client)
    
    async def process_task(self, task: Task) -> AgentResponse:
        """Process a testing task."""
        try:
            self.is_busy = True
            self.current_task = task
            
            await self.log_activity("Starting testing task", {"task_id": task.id})
            
            # Analyze testing requirements
            requirements = await self._analyze_testing_requirements(task)
            
            # Generate test cases
            test_cases = await self._generate_test_cases(task, requirements)
            
            # Create test files
            test_files = await self._create_test_files(test_cases)
            
            # Run tests
            test_results = await self._run_tests(test_files)
            
            # Analyze results
            analysis = await self._analyze_test_results(test_results)
            
            # Update task with results
            task = await self.update_task_status(
                task,
                TaskStatus.COMPLETED.value,
                {
                    "test_cases": test_cases,
                    "test_files": test_files,
                    "test_results": test_results,
                    "analysis": analysis,
                    "requirements": requirements
                }
            )
            
            await self.log_activity("Testing task completed", {
                "task_id": task.id,
                "tests_created": len(test_files),
                "tests_passed": len([r for r in test_results if r.get("success", False)])
            })
            
            return AgentResponse(
                agent_type=self.agent_type,
                task_id=task.id,
                success=True,
                result={
                    "test_cases": test_cases,
                    "test_files": test_files,
                    "test_results": test_results,
                    "analysis": analysis,
                    "requirements": requirements
                },
                suggestions=self._generate_suggestions(test_results, analysis)
            )
        
        except Exception as e:
            return await self.handle_error(e, task)
        finally:
            self.is_busy = False
            self.current_task = None
    
    async def _analyze_testing_requirements(self, task: Task) -> Dict[str, Any]:
        """Analyze testing requirements and context."""
        try:
            # Get project context
            project_context = await self.analyze_project_context(task.metadata.get("project_path", "."))
            
            # Get code to test if specified
            code_to_test = {}
            if "file_path" in task.metadata:
                try:
                    code_to_test[task.metadata["file_path"]] = await self.file_tools.read_file(
                        task.metadata["file_path"]
                    )
                except Exception:
                    pass
            
            # Look for existing tests
            existing_tests = await self._find_existing_tests(project_context.get("project_path", "."))
            
            # Create analysis prompt
            prompt = f"""
            Analyze the following testing task and provide testing strategy:
            
            Task: {task.title}
            Description: {task.description}
            
            Project Context:
            {json.dumps(project_context, indent=2)}
            
            Code to Test:
            {json.dumps(code_to_test, indent=2)}
            
            Existing Tests:
            {json.dumps(existing_tests, indent=2)}
            
            Please provide:
            1. Testing strategy and approach
            2. Types of tests needed (unit, integration, etc.)
            3. Test coverage requirements
            4. Edge cases to consider
            5. Mocking and fixture requirements
            6. Performance testing considerations
            """
            
            # Get LLM analysis
            analysis_text = await self.llm_client.generate_tester_response(prompt)
            
            return {
                "analysis_text": analysis_text,
                "project_context": project_context,
                "code_to_test": code_to_test,
                "existing_tests": existing_tests,
                "analysis_timestamp": asyncio.get_event_loop().time()
            }
        
        except Exception as e:
            logger.error(f"Error analyzing testing requirements: {e}")
            return {"error": str(e)}
    
    async def _generate_test_cases(self, task: Task, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test cases based on requirements."""
        try:
            prompt = f"""
            Based on the testing analysis, generate comprehensive test cases:
            
            Task: {task.title}
            Description: {task.description}
            
            Testing Analysis:
            {requirements.get('analysis_text', 'No analysis available')}
            
            Code to Test:
            {json.dumps(requirements.get('code_to_test', {}), indent=2)}
            
            Generate test cases that:
            1. Cover all major functionality
            2. Include edge cases and error conditions
            3. Test both positive and negative scenarios
            4. Are well-structured and maintainable
            5. Include proper assertions and documentation
            
            Provide the test cases with clear descriptions and expected outcomes.
            """
            
            test_cases_text = await self.llm_client.generate_tester_response(prompt)
            
            # Parse test cases from the response
            test_cases = await self._parse_test_cases(test_cases_text, task)
            
            return test_cases
        
        except Exception as e:
            logger.error(f"Error generating test cases: {e}")
            return []
    
    async def _parse_test_cases(self, test_cases_text: str, task: Task) -> List[Dict[str, Any]]:
        """Parse test cases from generated text."""
        try:
            # Simple parsing - in a more sophisticated implementation,
            # we'd use more advanced parsing techniques
            test_cases = []
            
            # Split by test case indicators
            lines = test_cases_text.split('\n')
            current_test = None
            
            for line in lines:
                line = line.strip()
                
                # Look for test case indicators
                if line.startswith('Test Case:') or line.startswith('def test_'):
                    # Save previous test if exists
                    if current_test:
                        test_cases.append(current_test)
                    
                    # Start new test
                    if line.startswith('Test Case:'):
                        current_test = {
                            "name": line.replace('Test Case:', '').strip(),
                            "description": "",
                            "test_function": f"test_{line.replace('Test Case:', '').strip().lower().replace(' ', '_')}",
                            "assertions": [],
                            "setup": [],
                            "teardown": []
                        }
                    elif line.startswith('def test_'):
                        test_name = line.split('(')[0].replace('def ', '')
                        current_test = {
                            "name": test_name,
                            "description": "",
                            "test_function": test_name,
                            "assertions": [],
                            "setup": [],
                            "teardown": []
                        }
                elif current_test and line:
                    if line.startswith('Description:'):
                        current_test["description"] = line.replace('Description:', '').strip()
                    elif line.startswith('Assert:'):
                        current_test["assertions"].append(line.replace('Assert:', '').strip())
                    elif line.startswith('Setup:'):
                        current_test["setup"].append(line.replace('Setup:', '').strip())
            
            # Save last test
            if current_test:
                test_cases.append(current_test)
            
            # If no tests were parsed, create a basic test
            if not test_cases:
                test_cases.append({
                    "name": f"test_{task.id}",
                    "description": f"Basic test for {task.title}",
                    "test_function": f"test_{task.id}",
                    "assertions": ["assert True"],  # Placeholder
                    "setup": [],
                    "teardown": []
                })
            
            return test_cases
        
        except Exception as e:
            logger.error(f"Error parsing test cases: {e}")
            return []
    
    async def _create_test_files(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create test files from test cases."""
        test_files = []
        
        for test_case in test_cases:
            try:
                # Generate test file content
                test_content = await self._generate_test_file_content(test_case)
                
                # Determine test file path with proper validation
                test_name = test_case.get('name', 'test_case')
                if not test_name or test_name.strip() == "":
                    test_name = f"test_{uuid.uuid4().hex[:8]}"
                
                # Clean the test name for filename
                clean_name = test_name.lower().replace(' ', '_').replace('-', '_')
                test_file_path = f"test_{clean_name}.py"
                
                # Create the test file
                result = await self.test_tools.create_test(test_file_path, test_content)
                
                test_files.append({
                    "test_case": test_case,
                    "file_path": result.get("test_path", test_file_path),
                    "content": test_content,
                    "creation_result": result
                })
            
            except Exception as e:
                logger.error(f"Error creating test file for {test_case.get('name', 'unknown')}: {e}")
                test_files.append({
                    "test_case": test_case,
                    "file_path": None,
                    "content": None,
                    "creation_result": {"success": False, "error": str(e)}
                })
        
        return test_files
    
    async def _generate_test_file_content(self, test_case: Dict[str, Any]) -> str:
        """Generate test file content from test case."""
        content = f'''"""Test case: {test_case['name']}"""

import pytest
import sys
import os

# Add the project root to sys.path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Test{test_case['name'].title().replace('_', '')}:
    """Test class for {test_case['name']}"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Setup code here
        pass
    
    def teardown_method(self):
        """Teardown for each test method"""
        # Teardown code here
        pass
    
    def {test_case['test_function']}(self):
        """{test_case['description']}"""
        # Test implementation
        {chr(10).join(f"        # {assertion}" for assertion in test_case.get('assertions', ['assert True']))}
        assert True  # Placeholder assertion
'''
        
        return content
    
    async def _run_tests(self, test_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run the created tests."""
        test_results = []
        
        for test_file in test_files:
            if not test_file.get("file_path"):
                continue
            
            try:
                # Run the specific test file
                result = await self.test_tools.run_specific_test(test_file["file_path"])
                
                test_results.append({
                    "test_file": test_file["file_path"],
                    "test_case": test_file["test_case"],
                    "result": result,
                    "success": result.get("success", False)
                })
            
            except Exception as e:
                logger.error(f"Error running test {test_file['file_path']}: {e}")
                test_results.append({
                    "test_file": test_file["file_path"],
                    "test_case": test_file["test_case"],
                    "result": {"success": False, "error": str(e)},
                    "success": False
                })
        
        return test_results
    
    async def _analyze_test_results(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze test results and provide insights."""
        try:
            total_tests = len(test_results)
            passed_tests = len([r for r in test_results if r.get("success", False)])
            failed_tests = total_tests - passed_tests
            
            # Get overall test coverage if possible
            coverage_result = await self.test_tools.get_test_coverage()
            
            analysis = {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "coverage_info": coverage_result,
                "analysis_timestamp": asyncio.get_event_loop().time()
            }
            
            # Analyze failures
            failures = [r for r in test_results if not r.get("success", False)]
            if failures:
                analysis["failure_analysis"] = [
                    {
                        "test_file": f["test_file"],
                        "error": f["result"].get("error", "Unknown error")
                    }
                    for f in failures
                ]
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing test results: {e}")
            return {"error": str(e)}
    
    async def _find_existing_tests(self, project_path: str) -> List[Dict[str, Any]]:
        """Find existing test files in the project."""
        try:
            test_files = []
            
            # Look for test files
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.startswith('test_') and file.endswith('.py'):
                        test_files.append({
                            "name": file,
                            "path": os.path.join(root, file),
                            "directory": root
                        })
            
            return test_files
        
        except Exception as e:
            logger.error(f"Error finding existing tests: {e}")
            return []
    
    def _generate_suggestions(self, test_results: List[Dict[str, Any]], analysis: Dict[str, Any]) -> List[str]:
        """Generate suggestions based on test results and analysis."""
        suggestions = []
        
        # Check success rate
        success_rate = analysis.get("success_rate", 0)
        if success_rate < 100:
            suggestions.append(f"Test success rate is {success_rate:.1f}% - investigate failures")
        
        # Check for failed tests
        failed_tests = analysis.get("failed_tests", 0)
        if failed_tests > 0:
            suggestions.append(f"{failed_tests} tests failed - review and fix issues")
        
        # Check test coverage
        coverage_info = analysis.get("coverage_info", {})
        if coverage_info.get("success", False):
            suggestions.append("Consider improving test coverage")
        
        # Suggest improvements
        if analysis.get("total_tests", 0) == 0:
            suggestions.append("No tests were created - consider adding basic test cases")
        
        return suggestions
    
    def _get_capabilities(self) -> List[str]:
        """Get tester agent capabilities."""
        return [
            "test_case_generation",
            "test_file_creation",
            "test_execution",
            "test_analysis",
            "coverage_analysis",
            "edge_case_testing",
            "integration_testing",
            "performance_testing"
        ]
