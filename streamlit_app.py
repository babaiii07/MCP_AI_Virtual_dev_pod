"""Streamlit frontend for MCP Multi-Agent Developer Pod."""

import streamlit as st
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import threading
import queue
import os

from mcp_dev_pod.coordinator import AgentCoordinator
from mcp_dev_pod.models import TaskStatus
from mcp_dev_pod.config import config

# Configure Streamlit page
st.set_page_config(
	page_title="MCP Multi-Agent Developer Pod",
	page_icon="🤖",
	layout="wide",
	initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
	.main-header {
		font-size: 3rem;
		font-weight: bold;
		text-align: center;
		margin-bottom: 2rem;
		background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}
	.agent-card {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		padding: 1rem;
		border-radius: 10px;
		color: white;
		margin: 0.5rem 0;
	}
	.task-card {
		background: #f8f9fa;
		padding: 1rem;
		border-radius: 10px;
		border-left: 4px solid #667eea;
		margin: 0.5rem 0;
	}
	.status-success {
		color: #28a745;
		font-weight: bold;
	}
	.status-error {
		color: #dc3545;
		font-weight: bold;
	}
	.status-pending {
		color: #ffc107;
		font-weight: bold;
	}
	.status-in-progress {
		color: #17a2b8;
		font-weight: bold;
	}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'coordinator_wrapper' not in st.session_state:
	st.session_state.coordinator_wrapper = None
if 'tasks' not in st.session_state:
	st.session_state.tasks = {}
if 'task_updates' not in st.session_state:
	st.session_state.task_updates = queue.Queue()
if 'system_ready' not in st.session_state:
	st.session_state.system_ready = False


class StreamlitCoordinator:
	"""Wrapper for the coordinator to work with Streamlit."""
	
	def __init__(self):
		self.coordinator: AgentCoordinator | None = None
		self.initialized = False
		self._worker_thread: threading.Thread | None = None
		self._worker_running = False
	
	def _run_coordinator(self):
		"""Background target that runs the coordinator processing loop."""
		async def _start():
			# Initialize again in this loop to ensure client state in this thread
			if not self.initialized:
				ok = await self.coordinator.initialize()
				self.initialized = ok
				if not ok:
					return
			
			# Start processing tasks continuously with proper error handling
			consecutive_errors = 0
			max_consecutive_errors = 5
			
			while self._worker_running:
				try:
					# Process tasks from the queue
					if not self.coordinator.task_queue.empty():
						task = await self.coordinator.task_queue.get()
						await self.coordinator._process_task(task)
						consecutive_errors = 0  # Reset error counter on success
					else:
						# Wait a bit if no tasks - increased wait time
						await asyncio.sleep(2)
				except Exception as e:
					consecutive_errors += 1
					print(f"Error in background worker (attempt {consecutive_errors}): {e}")
					
					# If too many consecutive errors, stop the worker
					if consecutive_errors >= max_consecutive_errors:
						print(f"Too many consecutive errors ({consecutive_errors}), stopping worker")
						self._worker_running = False
						break
					
					# Exponential backoff for errors
					wait_time = min(5 * (2 ** consecutive_errors), 60)  # Max 60 seconds
					await asyncio.sleep(wait_time)
		
		try:
			asyncio.run(_start())
		except Exception as e:
			print(f"Background worker error: {e}")
			self._worker_running = False
	
	async def initialize(self):
		"""Initialize the coordinator and start processing in background."""
		if self.initialized and self._worker_running:
			return True
		self.coordinator = AgentCoordinator()
		self.initialized = await self.coordinator.initialize()
		if not self.initialized:
			return False
		# Start background worker if not running
		if not self._worker_running:
			self._worker_running = True
			self._worker_thread = threading.Thread(target=self._run_coordinator, daemon=True)
			self._worker_thread.start()
		return True
	
	async def submit_task(self, title: str, description: str, project_path: str = "./workspace"):
		"""Submit a task."""
		if self.coordinator:
			return await self.coordinator.submit_task(title, description, {"project_path": project_path})
		return None
	
	async def get_all_tasks(self):
		"""Get all tasks."""
		if self.coordinator:
			return await self.coordinator.get_all_tasks()
		return {"active_tasks": {}, "completed_tasks": {}}
	
	async def get_task_status(self, task_id: str):
		"""Get task status."""
		if self.coordinator:
			return await self.coordinator.get_task_status(task_id)
		return None
	
	async def get_coordinator_status(self):
		"""Get coordinator status."""
		if self.coordinator:
			return await self.coordinator.get_coordinator_status()
		return {}
	
	def stop_worker(self):
		"""Stop the background worker."""
		self._worker_running = False
		if self._worker_thread and self._worker_thread.is_alive():
			self._worker_thread.join(timeout=5)


def run_async(coro):
	"""Run async function in a new event loop."""
	try:
		loop = asyncio.get_event_loop()
	except RuntimeError:
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
	return loop.run_until_complete(coro)


def main():
	"""Main Streamlit application."""
	
	# Header
	st.markdown('<h1 class="main-header">🤖 MCP Multi-Agent Developer Pod</h1>', unsafe_allow_html=True)
	st.markdown("### Autonomous Development Assistant with AI Agents")
	
	# Sidebar
	with st.sidebar:
		st.header("🎛️ Control Panel")
		
		# LLM key quick check
		if not config.groq_api_key:
			st.error("GROQ_API_KEY missing in .env. Add it and reload.")
		else:
			st.success("Groq key detected")
		
		# Initialize coordinator
		if st.button("🚀 Initialize System", type="primary"):
			with st.spinner("Initializing MCP Dev Pod..."):
				if st.session_state.coordinator_wrapper is None:
					st.session_state.coordinator_wrapper = StreamlitCoordinator()
				
				success = run_async(st.session_state.coordinator_wrapper.initialize())
				
				if success:
					st.success("✅ System initialized and processing loop started!")
					st.session_state.system_ready = True
				else:
					st.error("❌ Failed to initialize system. Check your Groq API key in .env file.")
					st.session_state.system_ready = False
		
		# System status
		if st.session_state.coordinator_wrapper and st.session_state.system_ready:
			# Get coordinator status
			status = run_async(st.session_state.coordinator_wrapper.get_coordinator_status())
			st.success("🟢 System Ready")
			st.metric("Active Tasks", status.get("active_tasks_count", 0))
			st.metric("Completed Tasks", status.get("completed_tasks_count", 0))
			st.metric("Queue Size", status.get("queue_size", 0))
			# Agent status
			st.subheader("🤖 Agent Status")
			agents = status.get("agents", {})
			for agent_type, agent_info in agents.items():
				status_icon = "🟢" if not agent_info.get("is_busy", False) else "🟡"
				st.write(f"{status_icon} {agent_type.title()}: {'Busy' if agent_info.get('is_busy', False) else 'Available'}")
		else:
			st.warning("🟡 System Not Ready")
	
	# Main content
	tab1, tab2, tab3, tab4 = st.tabs(["📝 Submit Task", "📊 Task Monitor", "📈 Analytics", "⚙️ Settings"])
	
	with tab1:
		st.header("📝 Submit New Task")
		
		if st.session_state.coordinator_wrapper and st.session_state.system_ready:
			with st.form("task_form"):
				col1, col2 = st.columns([2, 1])
				
				with col1:
					task_title = st.text_input("Task Title", placeholder="e.g., Create a web scraper")
					task_description = st.text_area(
						"Task Description", 
						placeholder="Describe what you want to build or implement...",
						height=100
					)
				
				with col2:
					project_path = st.text_input("Project Path", value="./workspace")
					priority = st.selectbox("Priority", ["Low", "Medium", "High"])
				
				submitted = st.form_submit_button("🚀 Submit Task", type="primary")
				
				if submitted and task_title and task_description:
					with st.spinner("Submitting task..."):
						task_id = run_async(
							st.session_state.coordinator_wrapper.submit_task(
								task_title, 
								task_description, 
								project_path
							)
						)
						
						if task_id:
							st.success(f"✅ Task submitted successfully! Task ID: {task_id[:8]}...")
							st.session_state.tasks[task_id] = {
								"title": task_title,
								"description": task_description,
								"status": "pending",
								"submitted_at": datetime.now()
							}
						else:
							st.error("❌ Failed to submit task")
		else:
			st.warning("⚠️ Please initialize the system first using the sidebar.")
	
	with tab2:
		st.header("📊 Task Monitor")
		
		if st.session_state.coordinator_wrapper and st.session_state.system_ready:
			# Manual refresh button with proper state management
			col1, col2 = st.columns([1, 3])
			with col1:
				if st.button("🔄 Refresh Tasks", key="manual_refresh"):
					# Clear any cached data and force refresh
					if 'last_refresh' in st.session_state:
						del st.session_state.last_refresh
					st.rerun()
			
			with col2:
				# Auto-refresh every 30 seconds
				if 'last_refresh' not in st.session_state:
					st.session_state.last_refresh = time.time()
				
				time_since_refresh = time.time() - st.session_state.last_refresh
				if time_since_refresh > 30:  # 30 seconds
					st.session_state.last_refresh = time.time()
					st.rerun()
			
			# Get all tasks
			all_tasks = run_async(st.session_state.coordinator_wrapper.get_all_tasks())
			
			# Active tasks
			st.subheader("🟡 Active Tasks")
			active_tasks = all_tasks.get("active_tasks", {})
			
			if active_tasks:
				for task_id, task_info in active_tasks.items():
					if task_info:
						with st.expander(f"🟡 {task_info['title']} - {task_info['status']}"):
							col1, col2 = st.columns([3, 1])
							
							with col1:
								st.write(f"**Description:** {task_info.get('description', 'No description')}")
								st.write(f"**Assigned Agent:** {task_info.get('assigned_agent', 'Unassigned')}")
								st.write(f"**Created:** {task_info.get('created_at', 'Unknown')}")
								st.write(f"**Updated:** {task_info.get('updated_at', 'Unknown')}")
							
							with col2:
								status = task_info.get('status', 'unknown')
								if status == 'in_progress':
									st.markdown('<span class="status-in-progress">In Progress</span>', unsafe_allow_html=True)
								elif status == 'pending':
									st.markdown('<span class="status-pending">Pending</span>', unsafe_allow_html=True)
								else:
									st.write(f"Status: {status}")
			else:
				st.info("No active tasks")
			
			# Completed tasks
			st.subheader("✅ Completed Tasks")
			completed_tasks = all_tasks.get("completed_tasks", {})
			
			if completed_tasks:
				for task_id, task_info in completed_tasks.items():
					if task_info:
						status_color = "status-success" if task_info['status'] == 'completed' else "status-error"
						with st.expander(f"✅ {task_info['title']} - {task_info['status']}"):
							col1, col2 = st.columns([3, 1])
							
							with col1:
								st.write(f"**Description:** {task_info.get('description', 'No description')}")
								st.write(f"**Assigned Agent:** {task_info.get('assigned_agent', 'Unassigned')}")
								st.write(f"**Created:** {task_info.get('created_at', 'Unknown')}")
								st.write(f"**Completed:** {task_info.get('updated_at', 'Unknown')}")
								
							# Show results if available
							if 'metadata' in task_info and task_info['metadata']:
								st.write("**Results:**")
								st.json(task_info['metadata'])
							
							with col2:
								if task_info['status'] == 'completed':
									st.markdown('<span class="status-success">Completed</span>', unsafe_allow_html=True)
								else:
									st.markdown('<span class="status-error">Failed</span>', unsafe_allow_html=True)
			else:
				st.info("No completed tasks")
		else:
			st.warning("⚠️ Please initialize the system first using the sidebar.")
	
	with tab3:
		st.header("📈 Analytics")
		
		if st.session_state.coordinator_wrapper and st.session_state.system_ready:
			# Get coordinator status
			status = run_async(st.session_state.coordinator_wrapper.get_coordinator_status())
			
			col1, col2, col3 = st.columns(3)
			
			with col1:
				st.metric("Total Active Tasks", status.get("active_tasks_count", 0))
			
			with col2:
				st.metric("Total Completed Tasks", status.get("completed_tasks_count", 0))
			
			with col3:
				st.metric("Queue Size", status.get("queue_size", 0))
			
			# Agent performance
			st.subheader("🤖 Agent Performance")
			agents = status.get("agents", {})
			
			for agent_type, agent_info in agents.items():
				st.write(f"**{agent_type.title()} Agent:**")
				col1, col2 = st.columns(2)
				
				with col1:
					st.write(f"Status: {'🟢 Available' if not agent_info.get('is_busy', False) else '🟡 Busy'}")
				
				with col2:
					current_task = agent_info.get('current_task', 'None')
					st.write(f"Current Task: {current_task}")
				
				st.write("---")
		else:
			st.warning("⚠️ Please initialize the system first using the sidebar.")
	
	with tab4:
		st.header("⚙️ Settings")
		
		st.subheader("🛠️ Configuration")
		st.info("Configuration is managed through the .env file. Key settings:")
		
		config_info = {
			"GROQ_API_KEY": "Your Groq API key",
			"GROQ_MODEL": "llama-3.3-70b-versatile",
			"PLANNER_TEMPERATURE": "0.7 (creative planning)",
			"CODER_TEMPERATURE": "0.3 (precise coding)",
			"TESTER_TEMPERATURE": "0.5 (balanced testing)",
			"MAX_CONCURRENT_AGENTS": "3",
			"AGENT_TIMEOUT": "300 seconds"
		}
		
		for key, description in config_info.items():
			st.write(f"**{key}:** {description}")
		
		st.subheader("📚 Available Commands")
		st.code("""
# Submit a task via CLI
python -m mcp_dev_pod.main submit-task "Create a calculator" "Implement basic math operations"

# Check status
python -m mcp_dev_pod.main status

# List all tasks
python -m mcp_dev_pod.main tasks

# Interactive mode
python -m mcp_dev_pod.main interactive
		""")
		
		st.subheader("🔗 Useful Links")
		st.markdown("""
		- [Groq API Documentation](https://console.groq.com/docs)
		- [MCP Documentation](https://modelcontextprotocol.io/)
		- [Streamlit Documentation](https://docs.streamlit.io/)
		""")

if __name__ == "__main__":
	main()
