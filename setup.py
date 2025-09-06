"""Setup script for MCP Multi-Agent Developer Pod."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-multi-agent-dev-pod",
    version="0.1.0",
    author="MCP Dev Pod",
    author_email="dev@example.com",
    description="MCP Multi-Agent Developer Pod with planner, coder, and tester agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/mcp-multi-agent-dev-pod",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "mcp>=1.0.0",
        "ollama>=0.1.0",
        "pydantic>=2.0.0",
        "aiofiles>=23.0.0",
        "gitpython>=3.1.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "rich>=13.0.0",
        "typer>=0.9.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.25.0",
    ],
    extras_require={
        "dev": [
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mcp-dev-pod=mcp_dev_pod.main:app",
        ],
    },
)
