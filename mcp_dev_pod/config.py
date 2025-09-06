"""Configuration management for MCP Multi-Agent Developer Pod."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Config(BaseSettings):
	"""Configuration settings for the MCP Dev Pod."""
	
	# LLM Configuration
	groq_api_key: str = Field(default="", env="GROQ_API_KEY")
	groq_model: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")
	groq_base_url: str = Field(default="https://api.groq.com/openai/v1", env="GROQ_BASE_URL")
	
	# Agent Configuration
	max_concurrent_agents: int = Field(default=3, env="MAX_CONCURRENT_AGENTS")
	agent_timeout: int = Field(default=300, env="AGENT_TIMEOUT")
	planner_temperature: float = Field(default=0.7, env="PLANNER_TEMPERATURE")
	coder_temperature: float = Field(default=0.3, env="CODER_TEMPERATURE")
	tester_temperature: float = Field(default=0.5, env="TESTER_TEMPERATURE")
	
	# Git Configuration
	git_author_name: str = Field(default="MCP Dev Pod", env="GIT_AUTHOR_NAME")
	git_author_email: str = Field(default="dev@example.com", env="GIT_AUTHOR_EMAIL")
	
	# Logging
	log_level: str = Field(default="INFO", env="LOG_LEVEL")
	log_file: str = Field(default="logs/mcp_dev_pod.log", env="LOG_FILE")
	
	# Workspace
	default_workspace: str = Field(default="./workspace", env="DEFAULT_WORKSPACE")
	
	# pydantic-settings v2 configuration: load .env and ignore extra keys (e.g., legacy OLLAMA_* vars)
	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore",
	)


# Global config instance
config = Config()
