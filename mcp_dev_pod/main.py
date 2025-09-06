"""Main application for the MCP Multi-Agent Developer Pod."""

import asyncio
import logging
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .coordinator import AgentCoordinator
from .config import config

# Initialize CLI app
app = typer.Typer(help="MCP Multi-Agent Developer Pod")
console = Console()

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@app.command()
def start():
    """Start the MCP Multi-Agent Developer Pod."""
    console.print(Panel.fit(
        "[bold blue]MCP Multi-Agent Developer Pod[/bold blue]\n"
        "Starting autonomous development assistant...",
        title="🚀 Initializing"
    ))
    
    asyncio.run(_start_coordinator())


async def _start_coordinator():
    """Start the coordinator."""
    try:
        coordinator = AgentCoordinator()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing coordinator...", total=None)
            
            if not await coordinator.initialize():
                console.print("[red]Failed to initialize coordinator[/red]")
                return
            
            progress.update(task, description="Coordinator ready!")
        
        console.print("[green]✅ Coordinator started successfully![/green]")
        console.print("\n[bold]Available commands:[/bold]")
        console.print("• submit-task: Submit a new development task")
        console.print("• status: Check coordinator status")
        console.print("• tasks: List all tasks")
        console.print("• stop: Stop the coordinator")
        
        # Start the coordinator
        await coordinator.start()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down coordinator...[/yellow]")
        await coordinator.stop()
        console.print("[green]✅ Coordinator stopped[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Error starting coordinator: {e}")


@app.command()
def submit_task(
    title: str = typer.Argument(..., help="Task title"),
    description: str = typer.Argument(..., help="Task description"),
    project_path: str = typer.Option(".", help="Project path")
):
    """Submit a new development task."""
    asyncio.run(_submit_task(title, description, project_path))


async def _submit_task(title: str, description: str, project_path: str):
    """Submit a task to the coordinator."""
    try:
        coordinator = AgentCoordinator()
        if not await coordinator.initialize():
            console.print("[red]Failed to initialize coordinator[/red]")
            return
        
        task_id = await coordinator.submit_task(
            title=title,
            description=description,
            metadata={"project_path": project_path}
        )
        
        console.print(f"[green]✅ Task submitted successfully![/green]")
        console.print(f"Task ID: [bold]{task_id}[/bold]")
        console.print(f"Title: {title}")
        console.print(f"Description: {description}")
        console.print(f"Project Path: {project_path}")
        
    except Exception as e:
        console.print(f"[red]Error submitting task: {e}[/red]")
        logger.error(f"Error submitting task: {e}")


@app.command()
def status():
    """Check coordinator status."""
    asyncio.run(_check_status())


async def _check_status():
    """Check coordinator status."""
    try:
        coordinator = AgentCoordinator()
        if not await coordinator.initialize():
            console.print("[red]Failed to initialize coordinator[/red]")
            return
        
        status = await coordinator.get_coordinator_status()
        
        # Create status table
        table = Table(title="Coordinator Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Running", "✅ Yes" if status["is_running"] else "❌ No")
        table.add_row("Active Tasks", str(status["active_tasks_count"]))
        table.add_row("Completed Tasks", str(status["completed_tasks_count"]))
        table.add_row("Queue Size", str(status["queue_size"]))
        table.add_row("Max Concurrent Tasks", str(status["max_concurrent_tasks"]))
        
        console.print(table)
        
        # Agent status
        if status["agents"]:
            agent_table = Table(title="Agent Status")
            agent_table.add_column("Agent", style="cyan")
            agent_table.add_column("Status", style="green")
            agent_table.add_column("Busy", style="yellow")
            agent_table.add_column("Current Task", style="blue")
            
            for agent_type, agent_info in status["agents"].items():
                agent_table.add_row(
                    agent_type.title(),
                    "✅ Active",
                    "Yes" if agent_info.get("is_busy", False) else "No",
                    agent_info.get("current_task", "None")
                )
            
            console.print(agent_table)
        
    except Exception as e:
        console.print(f"[red]Error checking status: {e}[/red]")
        logger.error(f"Error checking status: {e}")


@app.command()
def tasks():
    """List all tasks."""
    asyncio.run(_list_tasks())


async def _list_tasks():
    """List all tasks."""
    try:
        coordinator = AgentCoordinator()
        if not await coordinator.initialize():
            console.print("[red]Failed to initialize coordinator[/red]")
            return
        
        all_tasks = await coordinator.get_all_tasks()
        
        # Active tasks
        if all_tasks["active_tasks"]:
            active_table = Table(title="Active Tasks")
            active_table.add_column("ID", style="cyan")
            active_table.add_column("Title", style="green")
            active_table.add_column("Status", style="yellow")
            active_table.add_column("Agent", style="blue")
            active_table.add_column("Created", style="magenta")
            
            for task_id, task_info in all_tasks["active_tasks"].items():
                if task_info:
                    active_table.add_row(
                        task_id[:8] + "...",
                        task_info["title"],
                        task_info["status"],
                        task_info["assigned_agent"] or "Unassigned",
                        task_info["created_at"][:19]
                    )
            
            console.print(active_table)
        else:
            console.print("[yellow]No active tasks[/yellow]")
        
        # Completed tasks
        if all_tasks["completed_tasks"]:
            completed_table = Table(title="Completed Tasks")
            completed_table.add_column("ID", style="cyan")
            completed_table.add_column("Title", style="green")
            completed_table.add_column("Status", style="yellow")
            completed_table.add_column("Agent", style="blue")
            completed_table.add_column("Updated", style="magenta")
            
            for task_id, task_info in all_tasks["completed_tasks"].items():
                if task_info:
                    completed_table.add_row(
                        task_id[:8] + "...",
                        task_info["title"],
                        task_info["status"],
                        task_info["assigned_agent"] or "Unassigned",
                        task_info["updated_at"][:19]
                    )
            
            console.print(completed_table)
        else:
            console.print("[yellow]No completed tasks[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error listing tasks: {e}[/red]")
        logger.error(f"Error listing tasks: {e}")


@app.command()
def task_status(task_id: str = typer.Argument(..., help="Task ID")):
    """Get status of a specific task."""
    asyncio.run(_get_task_status(task_id))


async def _get_task_status(task_id: str):
    """Get status of a specific task."""
    try:
        coordinator = AgentCoordinator()
        if not await coordinator.initialize():
            console.print("[red]Failed to initialize coordinator[/red]")
            return
        
        task_info = await coordinator.get_task_status(task_id)
        
        if not task_info:
            console.print(f"[red]Task not found: {task_id}[/red]")
            return
        
        # Create task info panel
        info_text = f"""
[bold]Title:[/bold] {task_info['title']}
[bold]Status:[/bold] {task_info['status']}
[bold]Assigned Agent:[/bold] {task_info['assigned_agent'] or 'Unassigned'}
[bold]Created:[/bold] {task_info['created_at']}
[bold]Updated:[/bold] {task_info['updated_at']}
[bold]ID:[/bold] {task_info['id']}
        """
        
        console.print(Panel(info_text, title="Task Information"))
        
    except Exception as e:
        console.print(f"[red]Error getting task status: {e}[/red]")
        logger.error(f"Error getting task status: {e}")


@app.command()
def interactive():
    """Start interactive mode."""
    asyncio.run(_interactive_mode())


async def _interactive_mode():
    """Start interactive mode."""
    console.print(Panel.fit(
        "[bold blue]MCP Multi-Agent Developer Pod - Interactive Mode[/bold blue]\n"
        "Type 'help' for available commands or 'exit' to quit.",
        title="🎯 Interactive Mode"
    ))
    
    coordinator = AgentCoordinator()
    if not await coordinator.initialize():
        console.print("[red]Failed to initialize coordinator[/red]")
        return
    
    while True:
        try:
            command = typer.prompt("mcp-dev-pod>")
            
            if command.lower() in ['exit', 'quit']:
                break
            elif command.lower() == 'help':
                console.print("\n[bold]Available commands:[/bold]")
                console.print("• submit <title> <description> - Submit a new task")
                console.print("• status - Check coordinator status")
                console.print("• tasks - List all tasks")
                console.print("• task <id> - Get task status")
                console.print("• help - Show this help")
                console.print("• exit - Exit interactive mode")
            elif command.lower() == 'status':
                await _check_status()
            elif command.lower() == 'tasks':
                await _list_tasks()
            elif command.startswith('submit '):
                parts = command.split(' ', 2)
                if len(parts) >= 3:
                    await _submit_task(parts[1], parts[2], ".")
                else:
                    console.print("[red]Usage: submit <title> <description>[/red]")
            elif command.startswith('task '):
                parts = command.split(' ', 1)
                if len(parts) >= 2:
                    await _get_task_status(parts[1])
                else:
                    console.print("[red]Usage: task <id>[/red]")
            else:
                console.print(f"[red]Unknown command: {command}[/red]")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    console.print("[green]Goodbye![/green]")


if __name__ == "__main__":
    app()
