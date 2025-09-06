# MCP Multi-Agent Developer Pod

A sophisticated multi-agent system for autonomous development tasks using the Model Context Protocol (MCP). This system features specialized agents that collaborate to handle planning, coding, and testing tasks autonomously.

## 🤖 Features

- **Multi-Agent Architecture**: Three specialized agents (Planner, Coder, Tester) that work together
- **MCP Integration**: Full Model Context Protocol support for tool integration
- **LLM-Powered**: Uses Ollama with Llama 3.1 for intelligent task processing
- **Git Integration**: Built-in Git operations for version control
- **File System Tools**: Comprehensive file operations and project analysis
- **Python Execution**: Safe Python code execution and validation
- **Testing Framework**: Automated test generation and execution
- **Task Coordination**: Intelligent task routing and dependency management
- **Rich CLI**: Beautiful command-line interface with progress tracking

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Multi-Agent Dev Pod                 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Planner   │  │    Coder    │  │   Tester    │        │
│  │    Agent    │  │    Agent    │  │    Agent    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                │                │               │
│         └────────────────┼────────────────┘               │
│                          │                                │
│  ┌─────────────────────────────────────────────────────────┤
│  │              Agent Coordinator                          │
│  │  • Task Management  • Agent Communication              │
│  │  • Dependency Resolution  • Status Monitoring          │
│  └─────────────────────────────────────────────────────────┤
│                          │                                │
│  ┌─────────────────────────────────────────────────────────┤
│  │                MCP Server                               │
│  │  • Git Tools  • File Tools  • Python Tools             │
│  │  • Test Tools  • Project Analysis                      │
│  └─────────────────────────────────────────────────────────┤
│                          │                                │
│  ┌─────────────────────────────────────────────────────────┤
│  │              LLM Client (Ollama)                        │
│  │  • Llama 3.1 Integration  • Agent-Specific Prompts     │
│  └─────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Git
- Groq API key (get it from [console.groq.com](https://console.groq.com))

### Installation

#### Linux/macOS
```bash
# Clone the repository
git clone <repository-url>
cd mcp-multi-agent-dev-pod

# Run installation script
./install.sh
```

#### Windows
```cmd
# Clone the repository
git clone <repository-url>
cd mcp-multi-agent-dev-pod

# Run installation script
install.bat
```

#### Manual Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Create configuration
cp config.env.example .env
```

### Configuration

Edit the `.env` file to customize your setup:

```env
# LLM Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1

# Agent Configuration
MAX_CONCURRENT_AGENTS=3
AGENT_TIMEOUT=300
PLANNER_TEMPERATURE=0.7
CODER_TEMPERATURE=0.3
TESTER_TEMPERATURE=0.5

# Git Configuration
GIT_AUTHOR_NAME=MCP Dev Pod
GIT_AUTHOR_EMAIL=dev@example.com

# Workspace
DEFAULT_WORKSPACE=./workspace
```

## 🎯 Usage

### Starting the System

#### Option 1: Streamlit Web Interface (Recommended)
```bash
# Start the Streamlit web interface
streamlit run streamlit_app.py
```

The web interface provides:
- **Task Submission**: Easy form-based task creation
- **Real-time Monitoring**: Live task status updates
- **Agent Status**: Visual agent availability and performance
- **Analytics Dashboard**: Task completion statistics
- **Settings Panel**: Configuration management

#### Option 2: Command Line Interface
```bash
# Start the MCP Dev Pod
python -m mcp_dev_pod.main start
```

### Interactive Mode

```bash
python -m mcp_dev_pod.main interactive
```

### Command Line Interface

```bash
# Submit a new task
python -m mcp_dev_pod.main submit-task "Create a calculator" "Implement a basic calculator with add, subtract, multiply, and divide operations"

# Check system status
python -m mcp_dev_pod.main status

# List all tasks
python -m mcp_dev_pod.main tasks

# Get specific task status
python -m mcp_dev_pod.main task-status <task-id>
```

## 🤖 Agents

### Planner Agent
- **Role**: Task analysis and planning
- **Capabilities**:
  - Breaks down complex tasks into subtasks
  - Identifies dependencies and risks
  - Estimates effort and resources
  - Coordinates with other agents
- **Temperature**: 0.7 (creative planning)

### Coder Agent
- **Role**: Code generation and modification
- **Capabilities**:
  - Writes clean, efficient code
  - Follows best practices and standards
  - Handles error cases and edge conditions
  - Integrates with existing codebases
- **Temperature**: 0.3 (precise coding)

### Tester Agent
- **Role**: Test creation and validation
- **Capabilities**:
  - Generates comprehensive test cases
  - Identifies edge cases and potential bugs
  - Runs tests and analyzes results
  - Ensures code quality and reliability
- **Temperature**: 0.5 (balanced testing)

## 🛠️ Tools

### Git Tools
- Repository status and information
- Commit operations with custom author
- Branch management
- Change tracking

### File Tools
- File reading and writing
- Directory operations
- File search and analysis
- Project structure analysis

### Python Tools
- Safe code execution
- Syntax validation
- Package management
- Environment information

### Test Tools
- Test file creation
- Test execution with pytest
- Coverage analysis
- Test result reporting

## 📊 Task Flow

1. **Task Submission**: User submits a development task
2. **Task Analysis**: Planner agent analyzes requirements and context
3. **Plan Generation**: Planner creates detailed implementation plan
4. **Subtask Creation**: Planner breaks down task into actionable subtasks
5. **Agent Assignment**: Coordinator assigns subtasks to appropriate agents
6. **Code Implementation**: Coder agent implements the required functionality
7. **Test Creation**: Tester agent creates comprehensive tests
8. **Validation**: System validates code and runs tests
9. **Integration**: Results are integrated and task is marked complete

## 🔧 Development

### Project Structure

```
mcp_dev_pod/
├── __init__.py
├── config.py              # Configuration management
├── models.py              # Data models
├── llm_client.py          # LLM integration
├── coordinator.py         # Agent coordination
├── mcp_server.py          # MCP server implementation
├── main.py                # CLI application
├── agents/                # Agent implementations
│   ├── __init__.py
│   ├── base_agent.py      # Base agent class
│   ├── planner_agent.py   # Planner agent
│   ├── coder_agent.py     # Coder agent
│   └── tester_agent.py    # Tester agent
└── tools/                 # Tool implementations
    ├── __init__.py
    ├── git_tools.py       # Git operations
    ├── file_tools.py      # File system operations
    ├── python_tools.py    # Python execution
    └── test_tools.py      # Testing operations
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_dev_pod

# Run specific test file
pytest tests/test_agents.py
```

### Code Quality

```bash
# Format code
black mcp_dev_pod/

# Sort imports
isort mcp_dev_pod/

# Lint code
flake8 mcp_dev_pod/

# Type checking
mypy mcp_dev_pod/
```

## 🚨 Troubleshooting

### Common Issues

1. **Ollama Connection Error**
   - Ensure Ollama is running: `ollama serve`
   - Check the base URL in configuration
   - Verify the model is pulled: `ollama list`

2. **Agent Initialization Failed**
   - Check Python version (3.9+ required)
   - Verify all dependencies are installed
   - Check log files for detailed errors

3. **Task Processing Stuck**
   - Check agent status: `mcp-dev-pod status`
   - Review task dependencies
   - Restart the coordinator if needed

### Logs

Logs are written to `logs/mcp_dev_pod.log` by default. Check this file for detailed error information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for LLM integration
- [MCP](https://modelcontextprotocol.io/) for the protocol specification
- [Llama 3.1](https://llama.meta.com/) for the language model
- [Rich](https://rich.readthedocs.io/) for beautiful CLI output

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting section

---

**Happy coding with your autonomous development assistant! 🚀**
