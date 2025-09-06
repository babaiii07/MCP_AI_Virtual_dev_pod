"""Planner agent for the MCP Multi-Agent Developer Pod."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import json

from .base_agent import BaseAgent
from ..models import Task, AgentType, AgentResponse, TaskStatus

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """Planner agent that breaks down tasks and coordinates other agents."""
    
    def __init__(self, llm_client):
        super().__init__(AgentType.PLANNER, llm_client)
    
    async def process_task(self, task: Task) -> AgentResponse:
        """Process a planning task."""
        try:
            self.is_busy = True
            self.current_task = task
            
            await self.log_activity("Starting task planning", {"task_id": task.id})
            
            # Analyze the task requirements
            analysis = await self._analyze_task_requirements(task)
            
            # Generate a plan using LLM
            plan = await self._generate_plan(task, analysis)
            
            # Break down into subtasks
            subtasks = await self._create_subtasks(task, plan)
            
            # Update task with plan
            task = await self.update_task_status(
                task, 
                TaskStatus.COMPLETED.value,
                {
                    "plan": plan,
                    "subtasks": subtasks,
                    "analysis": analysis
                }
            )
            
            await self.log_activity("Task planning completed", {
                "task_id": task.id,
                "subtasks_count": len(subtasks)
            })
            
            return AgentResponse(
                agent_type=self.agent_type,
                task_id=task.id,
                success=True,
                result={
                    "plan": plan,
                    "subtasks": subtasks,
                    "analysis": analysis
                },
                suggestions=self._generate_suggestions(plan, subtasks)
            )
        
        except Exception as e:
            return await self.handle_error(e, task)
        finally:
            self.is_busy = False
            self.current_task = None
    
    async def _analyze_task_requirements(self, task: Task) -> Dict[str, Any]:
        """Analyze task requirements and context."""
        try:
            # Get project context
            project_context = await self.analyze_project_context(task.metadata.get("project_path", "."))
            
            # Create analysis prompt
            prompt = f"""
            Analyze the following development task and provide a comprehensive analysis:
            
            Task: {task.title}
            Description: {task.description}
            
            Project Context:
            {json.dumps(project_context, indent=2)}
            
            Please provide:
            1. Task complexity assessment (low/medium/high)
            2. Required skills and technologies
            3. Potential challenges and risks
            4. Estimated effort (in hours)
            5. Dependencies on other tasks or systems
            6. Suggested approach and methodology
            """
            
            # Get LLM analysis
            analysis_text = await self.llm_client.generate_planner_response(prompt)
            
            return {
                "analysis_text": analysis_text,
                "project_context": project_context,
                "analysis_timestamp": asyncio.get_event_loop().time()
            }
        
        except Exception as e:
            logger.error(f"Error analyzing task requirements: {e}")
            return {"error": str(e)}
    
    async def _generate_plan(self, task: Task, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed implementation plan."""
        try:
            prompt = f"""
            Based on the task analysis, create a detailed implementation plan:
            
            Task: {task.title}
            Description: {task.description}
            
            Analysis: {analysis.get('analysis_text', 'No analysis available')}
            
            Create a step-by-step plan that includes:
            1. High-level approach
            2. Detailed implementation steps
            3. Code structure and organization
            4. Testing strategy
            5. Deployment considerations
            6. Risk mitigation strategies
            
            Format the response as a structured plan with clear phases and deliverables.
            """
            
            plan_text = await self.llm_client.generate_planner_response(prompt)
            
            return {
                "plan_text": plan_text,
                "plan_type": "implementation",
                "generated_at": asyncio.get_event_loop().time()
            }
        
        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return {"error": str(e)}
    
    async def _create_subtasks(self, task: Task, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create subtasks based on the plan."""
        try:
            prompt = f"""
            Based on the implementation plan, break down the task into specific, actionable subtasks:
            
            Original Task: {task.title}
            Plan: {plan.get('plan_text', 'No plan available')}
            
            Create subtasks that:
            1. Are specific and actionable
            2. Can be assigned to coder or tester agents
            3. Have clear acceptance criteria
            4. Include estimated effort
            5. Identify dependencies between subtasks
            
            Format as a JSON list of subtasks with the following structure:
            [
                {{
                    "title": "Subtask title",
                    "description": "Detailed description",
                    "assigned_agent": "coder" or "tester",
                    "estimated_effort": "X hours",
                    "dependencies": ["subtask_id_1", "subtask_id_2"],
                    "acceptance_criteria": ["criteria 1", "criteria 2"],
                    "priority": "high/medium/low"
                }}
            ]
            """
            
            subtasks_text = await self.llm_client.generate_planner_response(prompt)
            
            # Try to parse JSON from the response
            try:
                # Extract JSON from the response if it's embedded in text
                import re
                json_match = re.search(r'\[.*\]', subtasks_text, re.DOTALL)
                if json_match:
                    subtasks = json.loads(json_match.group())
                else:
                    # Fallback: create basic subtasks
                    subtasks = self._create_fallback_subtasks(task)
            except json.JSONDecodeError:
                logger.warning("Could not parse subtasks JSON, using fallback")
                subtasks = self._create_fallback_subtasks(task)
            
            # Add unique IDs to subtasks
            for i, subtask in enumerate(subtasks):
                subtask["id"] = f"{task.id}_subtask_{i+1}"
                subtask["parent_task_id"] = task.id
            
            return subtasks
        
        except Exception as e:
            logger.error(f"Error creating subtasks: {e}")
            return self._create_fallback_subtasks(task)
    
    def _create_fallback_subtasks(self, task: Task) -> List[Dict[str, Any]]:
        """Create basic fallback subtasks if LLM parsing fails."""
        return [
            {
                "id": f"{task.id}_subtask_1",
                "title": "Implement core functionality",
                "description": f"Implement the main functionality for: {task.title}",
                "assigned_agent": "coder",
                "estimated_effort": "4 hours",
                "dependencies": [],
                "acceptance_criteria": ["Code is implemented", "Basic functionality works"],
                "priority": "high",
                "parent_task_id": task.id
            },
            {
                "id": f"{task.id}_subtask_2",
                "title": "Write tests",
                "description": f"Write comprehensive tests for: {task.title}",
                "assigned_agent": "tester",
                "estimated_effort": "2 hours",
                "dependencies": [f"{task.id}_subtask_1"],
                "acceptance_criteria": ["Tests are written", "All tests pass"],
                "priority": "high",
                "parent_task_id": task.id
            }
        ]
    
    def _generate_suggestions(self, plan: Dict[str, Any], subtasks: List[Dict[str, Any]]) -> List[str]:
        """Generate suggestions based on the plan and subtasks."""
        suggestions = []
        
        # Analyze subtasks for suggestions
        coder_tasks = [t for t in subtasks if t.get("assigned_agent") == "coder"]
        tester_tasks = [t for t in subtasks if t.get("assigned_agent") == "tester"]
        
        if len(coder_tasks) > 3:
            suggestions.append("Consider breaking down coder tasks into smaller chunks")
        
        if len(tester_tasks) == 0:
            suggestions.append("Consider adding testing tasks to ensure quality")
        
        # Check for high-priority tasks
        high_priority = [t for t in subtasks if t.get("priority") == "high"]
        if len(high_priority) > 2:
            suggestions.append("Multiple high-priority tasks detected - consider sequencing")
        
        # Check for dependencies
        tasks_with_deps = [t for t in subtasks if t.get("dependencies")]
        if len(tasks_with_deps) > 0:
            suggestions.append("Tasks have dependencies - ensure proper sequencing")
        
        return suggestions
    
    def _get_capabilities(self) -> List[str]:
        """Get planner agent capabilities."""
        return [
            "task_analysis",
            "plan_generation",
            "subtask_creation",
            "dependency_analysis",
            "effort_estimation",
            "risk_assessment",
            "project_coordination"
        ]
