"""Coder agent for the MCP Multi-Agent Developer Pod."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import json
import os

from .base_agent import BaseAgent
from ..models import Task, AgentType, AgentResponse, TaskStatus, CodeChange

logger = logging.getLogger(__name__)


class CoderAgent(BaseAgent):
    """Coder agent that handles code generation and modification."""
    
    def __init__(self, llm_client):
        super().__init__(AgentType.CODER, llm_client)
    
    async def process_task(self, task: Task) -> AgentResponse:
        """Process a coding task."""
        try:
            self.is_busy = True
            self.current_task = task
            
            await self.log_activity("Starting coding task", {"task_id": task.id})
            
            # Analyze the coding requirements
            requirements = await self._analyze_coding_requirements(task)
            
            # Generate or modify code
            code_changes = await self._generate_code(task, requirements)
            
            # Apply code changes
            applied_changes = await self._apply_code_changes(code_changes, task)
            
            # Validate the code
            validation_result = await self._validate_code(applied_changes)
            
            # Update task with results
            task = await self.update_task_status(
                task,
                TaskStatus.COMPLETED.value,
                {
                    "code_changes": applied_changes,
                    "validation_result": validation_result,
                    "requirements": requirements
                }
            )
            
            await self.log_activity("Coding task completed", {
                "task_id": task.id,
                "files_modified": len(applied_changes)
            })
            
            return AgentResponse(
                agent_type=self.agent_type,
                task_id=task.id,
                success=True,
                result={
                    "code_changes": applied_changes,
                    "validation_result": validation_result,
                    "requirements": requirements
                },
                suggestions=self._generate_suggestions(applied_changes, validation_result)
            )
        
        except Exception as e:
            return await self.handle_error(e, task)
        finally:
            self.is_busy = False
            self.current_task = None
    
    async def _analyze_coding_requirements(self, task: Task) -> Dict[str, Any]:
        """Analyze coding requirements and context."""
        try:
            # Get project context
            project_context = await self.analyze_project_context(task.metadata.get("project_path", "."))
            
            # Get existing code if specified
            existing_code = {}
            if "file_path" in task.metadata:
                try:
                    existing_code[task.metadata["file_path"]] = await self.file_tools.read_file(
                        task.metadata["file_path"]
                    )
                except Exception:
                    pass
            
            # Create analysis prompt
            prompt = f"""
            Analyze the following coding task and provide implementation guidance:
            
            Task: {task.title}
            Description: {task.description}
            
            Project Context:
            {json.dumps(project_context, indent=2)}
            
            Existing Code:
            {json.dumps(existing_code, indent=2)}
            
            Please provide:
            1. Implementation approach and architecture
            2. Required imports and dependencies
            3. Code structure and organization
            4. Error handling requirements
            5. Performance considerations
            6. Integration points with existing code
            """
            
            # Get LLM analysis
            analysis_text = await self.llm_client.generate_coder_response(prompt)
            
            return {
                "analysis_text": analysis_text,
                "project_context": project_context,
                "existing_code": existing_code,
                "analysis_timestamp": asyncio.get_event_loop().time()
            }
        
        except Exception as e:
            logger.error(f"Error analyzing coding requirements: {e}")
            return {"error": str(e)}
    
    async def _generate_code(self, task: Task, requirements: Dict[str, Any]) -> List[CodeChange]:
        """Generate code based on requirements."""
        try:
            # Import project generator
            from ..project_generator import ProjectGenerator
            
            # Use project generator for comprehensive projects
            project_generator = ProjectGenerator()
            project_files = await project_generator.generate_project_structure(task)
            
            # Convert project files to CodeChange objects
            code_changes = []
            for file_info in project_files:
                code_changes.append(CodeChange(
                    file_path=file_info["file_path"],
                    change_type=file_info["type"],
                    content=file_info["content"]
                ))
            
            # If no files generated, fall back to LLM generation
            if not code_changes:
                prompt = f"""
                Based on the analysis, generate the required code:
                
                Task: {task.title}
                Description: {task.description}
                
                Requirements Analysis:
                {requirements.get('analysis_text', 'No analysis available')}
                
                Project Context:
                {json.dumps(requirements.get('project_context', {}), indent=2)}
                
                Generate complete, working code that:
                1. Follows Python best practices
                2. Includes proper error handling
                3. Has clear documentation and comments
                4. Is modular and maintainable
                5. Integrates well with existing code
                
                Provide the code with clear file structure and any necessary imports.
                """
                
                code_text = await self.llm_client.generate_coder_response(prompt)
                
                # Parse the generated code to extract files and content
                code_changes = await self._parse_generated_code(code_text, task)
            
            return code_changes
        
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return []
    
    async def _parse_generated_code(self, code_text: str, task: Task) -> List[CodeChange]:
        """Parse generated code text into CodeChange objects."""
        try:
            code_changes = []
            
            # Enhanced parsing for different code block formats
            lines = code_text.split('\n')
            current_file = None
            current_content = []
            in_code_block = False
            code_block_language = None
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Look for file indicators (multiple formats)
                if (line_stripped.startswith('File:') or 
                    line_stripped.startswith('Filename:') or
                    line_stripped.startswith('File: ') or
                    line_stripped.startswith('Filename: ')):
                    
                    # Save previous file if exists
                    if current_file and current_content:
                        code_changes.append(CodeChange(
                            file_path=current_file,
                            change_type="create" if not os.path.exists(current_file) else "modify",
                            content='\n'.join(current_content)
                        ))
                    
                    # Extract filename
                    if line_stripped.startswith('File:'):
                        current_file = line_stripped.replace('File:', '').strip()
                    elif line_stripped.startswith('Filename:'):
                        current_file = line_stripped.replace('Filename:', '').strip()
                    else:
                        # Handle other formats
                        current_file = line_stripped.split(':', 1)[1].strip() if ':' in line_stripped else line_stripped
                    
                    current_content = []
                    in_code_block = False
                
                # Look for code blocks
                elif line_stripped.startswith('```'):
                    if not in_code_block:
                        # Starting a code block
                        in_code_block = True
                        code_block_language = line_stripped[3:].strip()
                        
                        # If no current file, create one based on language and task
                        if not current_file:
                            current_file = self._generate_filename(task, code_block_language)
                    else:
                        # Ending a code block
                        in_code_block = False
                        code_block_language = None
                
                # Add content to current file
                elif current_file and (in_code_block or not line_stripped.startswith('```')):
                    current_content.append(line)
            
            # Save last file
            if current_file and current_content:
                code_changes.append(CodeChange(
                    file_path=current_file,
                    change_type="create" if not os.path.exists(current_file) else "modify",
                    content='\n'.join(current_content)
                ))
            
            # If no files were parsed, try to extract code from the text
            if not code_changes:
                # Look for different code patterns
                if self._has_code_patterns(code_text):
                    extracted_files = self._extract_multiple_files(code_text, task)
                    code_changes.extend(extracted_files)
                
                # If still no code, create a comprehensive implementation
                if not code_changes:
                    code_changes = self._generate_comprehensive_implementation(task, code_text)
            
            return code_changes
        
        except Exception as e:
            logger.error(f"Error parsing generated code: {e}")
            return []
    
    def _generate_filename(self, task: Task, language: str) -> str:
        """Generate appropriate filename based on task and language."""
        base_name = task.title.lower().replace(' ', '_').replace('-', '_')
        
        if language == 'python' or language == 'py':
            return f"{base_name}.py"
        elif language == 'javascript' or language == 'js':
            return f"{base_name}.js"
        elif language == 'html':
            return f"{base_name}.html"
        elif language == 'css':
            return f"{base_name}.css"
        elif language == 'json':
            return f"{base_name}.json"
        elif language == 'yaml' or language == 'yml':
            return f"{base_name}.yml"
        elif language == 'dockerfile':
            return "Dockerfile"
        elif language == 'txt':
            return f"{base_name}.txt"
        else:
            return f"{base_name}.{language or 'py'}"
    
    def _has_code_patterns(self, text: str) -> bool:
        """Check if text contains code patterns."""
        patterns = [
            'def ', 'class ', 'import ', 'from ',
            'function ', 'const ', 'let ', 'var ',
            '<!DOCTYPE', '<html', '<div', '<script',
            'SELECT ', 'INSERT ', 'UPDATE ', 'CREATE ',
            'from fastapi', 'from flask', 'from django',
            'app = FastAPI', 'app = Flask', 'from sqlalchemy'
        ]
        return any(pattern in text for pattern in patterns)
    
    def _extract_multiple_files(self, text: str, task: Task) -> List[CodeChange]:
        """Extract multiple files from text."""
        files = []
        
        # Try to extract different types of files
        if 'from fastapi' in text or 'app = FastAPI' in text:
            files.append(CodeChange(
                file_path="app.py",
                change_type="create",
                content=self._extract_python_code(text)
            ))
        
        if 'from sqlalchemy' in text or 'class ' in text:
            files.append(CodeChange(
                file_path="models.py",
                change_type="create",
                content=self._extract_python_code(text)
            ))
        
        if 'requirements' in text.lower() or 'pip install' in text:
            files.append(CodeChange(
                file_path="requirements.txt",
                change_type="create",
                content=self._extract_requirements(text)
            ))
        
        if 'FROM ' in text.upper() and 'python' in text.lower():
            files.append(CodeChange(
                file_path="Dockerfile",
                change_type="create",
                content=self._extract_dockerfile(text)
            ))
        
        return files
    
    def _extract_requirements(self, text: str) -> str:
        """Extract requirements from text."""
        lines = text.split('\n')
        requirements = []
        
        for line in lines:
            line = line.strip()
            if (line.startswith('pip install') or 
                line.startswith('fastapi') or 
                line.startswith('flask') or
                line.startswith('django') or
                line.startswith('sqlalchemy') or
                line.startswith('uvicorn') or
                line.startswith('pytest')):
                if line.startswith('pip install '):
                    line = line.replace('pip install ', '')
                requirements.append(line)
        
        return '\n'.join(requirements) if requirements else "fastapi==0.104.1\nuvicorn==0.24.0\nsqlalchemy==2.0.23"
    
    def _extract_dockerfile(self, text: str) -> str:
        """Extract Dockerfile content."""
        lines = text.split('\n')
        dockerfile_lines = []
        in_dockerfile = False
        
        for line in lines:
            if 'FROM ' in line.upper() or in_dockerfile:
                in_dockerfile = True
                dockerfile_lines.append(line)
                if line.strip() == '' and len(dockerfile_lines) > 3:
                    break
        
        return '\n'.join(dockerfile_lines) if dockerfile_lines else """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]"""
    
    def _generate_comprehensive_implementation(self, task: Task, llm_response: str) -> List[CodeChange]:
        """Generate comprehensive implementation files."""
        files = []
        
        # Main application file
        main_code = f'''"""
{task.title}
{task.description}

Generated by MCP Multi-Agent Developer Pod
Task ID: {task.id}
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import logging
import os
from typing import List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="{task.title}",
    description="{task.description}",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    """Root endpoint."""
    return templates.TemplateResponse("index.html", {{"request": request}})

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {{"status": "healthy", "timestamp": datetime.now()}}

@app.get("/api/status")
async def api_status():
    """API status endpoint."""
    return {{
        "message": "API is running",
        "task": "{task.title}",
        "description": "{task.description}"
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        
        files.append(CodeChange(
            file_path="app.py",
            change_type="create",
            content=main_code
        ))
        
        # Requirements file
        requirements = """fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
python-multipart==0.0.6
jinja2==3.1.2
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
"""
        
        files.append(CodeChange(
            file_path="requirements.txt",
            change_type="create",
            content=requirements
        ))
        
        # Dockerfile
        dockerfile = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        
        files.append(CodeChange(
            file_path="Dockerfile",
            change_type="create",
            content=dockerfile
        ))
        
        # HTML template
        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{task.title}</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <h1 class="nav-title">{task.title}</h1>
            <div class="nav-links">
                <a href="/" class="nav-link">Home</a>
                <a href="/api/status" class="nav-link">API Status</a>
            </div>
        </div>
    </nav>
    
    <main class="main-content">
        <div class="container">
            <div class="hero-section">
                <h1 class="hero-title">{task.title}</h1>
                <p class="hero-description">{task.description}</p>
                <div class="hero-actions">
                    <button class="btn btn-primary" onclick="checkStatus()">
                        <i class="fas fa-check"></i> Check Status
                    </button>
                    <button class="btn btn-secondary" onclick="showInfo()">
                        <i class="fas fa-info"></i> Show Info
                    </button>
                </div>
            </div>
            
            <div class="features-grid">
                <div class="feature-card">
                    <i class="fas fa-rocket"></i>
                    <h3>Fast & Modern</h3>
                    <p>Built with FastAPI for high performance</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-shield-alt"></i>
                    <h3>Secure</h3>
                    <p>Production-ready security features</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-mobile-alt"></i>
                    <h3>Responsive</h3>
                    <p>Works on all devices and screen sizes</p>
                </div>
            </div>
        </div>
    </main>
    
    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 MCP Multi-Agent Developer Pod. Generated automatically.</p>
        </div>
    </footer>
    
    <script src="/static/js/app.js"></script>
</body>
</html>'''
        
        files.append(CodeChange(
            file_path="templates/index.html",
            change_type="create",
            content=html_template
        ))
        
        # CSS file
        css_content = """/* Modern CSS Variables */
:root {
  --primary-color: #667eea;
  --secondary-color: #764ba2;
  --accent-color: #f093fb;
  --text-color: #333;
  --bg-color: #f8f9fa;
  --card-bg: #ffffff;
  --border-color: #e9ecef;
  --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.15);
}

/* Reset and Base Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.6;
  color: var(--text-color);
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
  min-height: 100vh;
}

/* Navigation */
.navbar {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-title {
  color: var(--primary-color);
  font-size: 1.5rem;
  font-weight: 700;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-link {
  text-decoration: none;
  color: var(--text-color);
  font-weight: 500;
  transition: color 0.3s ease;
}

.nav-link:hover {
  color: var(--primary-color);
}

/* Main Content */
.main-content {
  padding: 2rem 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

/* Hero Section */
.hero-section {
  text-align: center;
  padding: 4rem 0;
  color: white;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.hero-description {
  font-size: 1.25rem;
  margin-bottom: 2rem;
  opacity: 0.9;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

/* Buttons */
.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
}

.btn-primary {
  background: white;
  color: var(--primary-color);
  box-shadow: var(--shadow);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid white;
}

.btn-secondary:hover {
  background: white;
  color: var(--primary-color);
}

/* Features Grid */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 4rem;
}

.feature-card {
  background: var(--card-bg);
  padding: 2rem;
  border-radius: 15px;
  text-align: center;
  box-shadow: var(--shadow);
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.feature-card i {
  font-size: 3rem;
  color: var(--primary-color);
  margin-bottom: 1rem;
}

.feature-card h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: var(--text-color);
}

.feature-card p {
  color: #666;
  line-height: 1.6;
}

/* Footer */
.footer {
  background: rgba(0, 0, 0, 0.1);
  color: white;
  text-align: center;
  padding: 2rem 0;
  margin-top: 4rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    gap: 1rem;
  }
  
  .nav-links {
    gap: 1rem;
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
}

/* Animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero-section {
  animation: fadeInUp 0.8s ease-out;
}

.feature-card {
  animation: fadeInUp 0.8s ease-out;
  animation-fill-mode: both;
}

.feature-card:nth-child(2) {
  animation-delay: 0.2s;
}

.feature-card:nth-child(3) {
  animation-delay: 0.4s;
}"""
        
        files.append(CodeChange(
            file_path="static/css/style.css",
            change_type="create",
            content=css_content
        ))
        
        # JavaScript file
        js_content = """// Modern JavaScript for the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Application loaded successfully');
    
    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});

// Check API status
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // Create a modern modal
        showModal('API Status', `
            <div class="status-info">
                <p><strong>Status:</strong> ${data.message}</p>
                <p><strong>Task:</strong> ${data.task}</p>
                <p><strong>Description:</strong> ${data.description}</p>
            </div>
        `);
    } catch (error) {
        showModal('Error', '<p>Failed to fetch API status</p>');
    }
}

// Show application info
function showInfo() {
    showModal('Application Info', `
        <div class="info-content">
            <h3>MCP Multi-Agent Developer Pod</h3>
            <p>This application was generated automatically using AI agents.</p>
            <ul>
                <li>Built with FastAPI</li>
                <li>Modern responsive design</li>
                <li>Production-ready code</li>
                <li>Docker support included</li>
            </ul>
        </div>
    `);
}

// Modern modal system
function showModal(title, content) {
    // Remove existing modal
    const existingModal = document.querySelector('.modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-overlay">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${title}</h2>
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="closeModal()">Close</button>
                </div>
            </div>
        </div>
    `;
    
    // Add modal styles
    const style = document.createElement('style');
    style.textContent = `
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 2000;
        }
        
        .modal-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }
        
        .modal-content {
            background: white;
            border-radius: 15px;
            max-width: 500px;
            width: 100%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            animation: modalSlideIn 0.3s ease-out;
        }
        
        .modal-header {
            padding: 1.5rem;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-header h2 {
            margin: 0;
            color: var(--primary-color);
        }
        
        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #999;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .modal-close:hover {
            color: #333;
        }
        
        .modal-body {
            padding: 1.5rem;
        }
        
        .modal-footer {
            padding: 1.5rem;
            border-top: 1px solid #eee;
            text-align: right;
        }
        
        @keyframes modalSlideIn {
            from {
                opacity: 0;
                transform: translateY(-50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .status-info p {
            margin-bottom: 0.5rem;
        }
        
        .info-content ul {
            margin-top: 1rem;
            padding-left: 1.5rem;
        }
        
        .info-content li {
            margin-bottom: 0.5rem;
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(modal);
    
    // Close on overlay click
    modal.querySelector('.modal-overlay').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
    
    // Close on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

function closeModal() {
    const modal = document.querySelector('.modal');
    if (modal) {
        modal.remove();
    }
}"""
        
        files.append(CodeChange(
            file_path="static/js/app.js",
            change_type="create",
            content=js_content
        ))
        
        return files
    
    def _extract_python_code(self, text: str) -> str:
        """Extract Python code from mixed text."""
        lines = text.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            # Start of code block
            if line.strip().startswith('```') and ('python' in line or 'py' in line):
                in_code = True
                continue
            # End of code block
            elif line.strip().startswith('```') and in_code:
                break
            # Add code lines
            elif in_code:
                code_lines.append(line)
            # Look for standalone code patterns
            elif (line.strip().startswith('def ') or 
                  line.strip().startswith('class ') or 
                  line.strip().startswith('import ') or
                  line.strip().startswith('from ')):
                code_lines.append(line)
        
        return '\n'.join(code_lines) if code_lines else ""
    
    def _generate_basic_implementation(self, task: Task, llm_response: str) -> str:
        """Generate a basic implementation file when parsing fails."""
        return f'''"""
{task.title}
{task.description}

Generated by MCP Multi-Agent Developer Pod
Task ID: {task.id}
"""

# TODO: Implement the functionality described in the task
# LLM Response: {llm_response[:200]}...

def main():
    """Main function to implement the required functionality."""
    print("Hello! This is a placeholder implementation.")
    print(f"Task: {task.title}")
    print(f"Description: {task.description}")
    
    # TODO: Add your implementation here
    pass

if __name__ == "__main__":
    main()
'''
    
    async def _apply_code_changes(self, code_changes: List[CodeChange], task: Task = None) -> List[Dict[str, Any]]:
        """Apply code changes to files."""
        applied_changes = []
        
        # Get workspace path from task metadata
        current_task = task or self.current_task
        if current_task:
            workspace_path = current_task.metadata.get("project_path", "./workspace")
            # Create project-specific folder using task title
            project_name = current_task.title.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace('[', '').replace(']', '')
            # Remove any special characters and limit length
            project_name = ''.join(c for c in project_name if c.isalnum() or c in '_-')[:50]
            project_folder = os.path.join(workspace_path, project_name)
        else:
            workspace_path = "./workspace"
            project_folder = os.path.join(workspace_path, "default_project")
        
        # Ensure project folder exists
        try:
            await self.file_tools.create_directory(project_folder)
        except Exception as e:
            logger.error(f"Error creating project folder {project_folder}: {e}")
        
        for change in code_changes:
            try:
                # Ensure the file path is relative to the project folder
                if not change.file_path.startswith(project_folder):
                    full_path = os.path.join(project_folder, change.file_path)
                else:
                    full_path = change.file_path
                
                if change.change_type == "create":
                    result = await self.file_tools.write_file(full_path, change.content or "")
                elif change.change_type == "modify":
                    # Read existing content first
                    try:
                        existing_content = await self.file_tools.read_file(full_path)
                        # For now, just replace the content
                        # In a more sophisticated implementation, we'd do proper diff/merge
                        result = await self.file_tools.write_file(full_path, change.content or "")
                    except FileNotFoundError:
                        # File doesn't exist, create it
                        result = await self.file_tools.write_file(full_path, change.content or "")
                elif change.change_type == "delete":
                    result = await self.file_tools.delete_file(full_path)
                else:
                    continue
                
                applied_changes.append({
                    "file_path": full_path,
                    "change_type": change.change_type,
                    "success": result.get("success", False),
                    "result": result
                })
            
            except Exception as e:
                logger.error(f"Error applying change to {change.file_path}: {e}")
                applied_changes.append({
                    "file_path": change.file_path,
                    "change_type": change.change_type,
                    "success": False,
                    "error": str(e)
                })
        
        return applied_changes
    
    async def _validate_code(self, applied_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate the applied code changes."""
        validation_results = {
            "syntax_validation": {},
            "import_validation": {},
            "overall_success": True
        }
        
        for change in applied_changes:
            if not change.get("success", False):
                continue
            
            file_path = change["file_path"]
            
            # Skip non-Python files
            if not file_path.endswith('.py'):
                continue
            
            try:
                # Read the file content
                content = await self.file_tools.read_file(file_path)
                
                # Validate syntax
                syntax_result = await self.python_tools.check_syntax(content)
                validation_results["syntax_validation"][file_path] = syntax_result
                
                # Check for import issues
                if not syntax_result.get("syntax_valid", False):
                    validation_results["overall_success"] = False
                
            except Exception as e:
                logger.error(f"Error validating {file_path}: {e}")
                validation_results["syntax_validation"][file_path] = {
                    "success": False,
                    "error": str(e)
                }
                validation_results["overall_success"] = False
        
        return validation_results
    
    def _generate_suggestions(self, applied_changes: List[Dict[str, Any]], validation_result: Dict[str, Any]) -> List[str]:
        """Generate suggestions based on code changes and validation."""
        suggestions = []
        
        # Check for syntax errors
        if not validation_result.get("overall_success", True):
            suggestions.append("Fix syntax errors before proceeding")
        
        # Check for successful changes
        successful_changes = [c for c in applied_changes if c.get("success", False)]
        if len(successful_changes) > 0:
            suggestions.append("Code changes applied successfully - consider running tests")
        
        # Check for failed changes
        failed_changes = [c for c in applied_changes if not c.get("success", False)]
        if len(failed_changes) > 0:
            suggestions.append("Some code changes failed - review and fix issues")
        
        # Suggest testing
        if len(successful_changes) > 0:
            suggestions.append("Consider writing unit tests for the new code")
        
        return suggestions
    
    def _get_capabilities(self) -> List[str]:
        """Get coder agent capabilities."""
        return [
            "code_generation",
            "code_modification",
            "syntax_validation",
            "file_operations",
            "import_management",
            "error_handling",
            "code_documentation",
            "refactoring"
        ]
