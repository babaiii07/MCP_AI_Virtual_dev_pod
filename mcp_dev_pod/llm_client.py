"""LLM client for the MCP Multi-Agent Developer Pod using Groq."""

import asyncio
import httpx
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
import json
import time
import random

from .config import config

logger = logging.getLogger(__name__)


class GroqClient:
    """Groq LLM client for the development pod."""
    
    def __init__(self):
        self.api_key = config.groq_api_key
        self.model = config.groq_model
        self.base_url = config.groq_base_url
        self.timeout = httpx.Timeout(30.0)
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        self.max_retries = 3
        self.retry_delay = 2.0
    
    async def generate_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate a response from the LLM with rate limiting and retry logic."""
        try:
            if not self.api_key:
                return "Error: Groq API key not configured"
            
            # Rate limiting
            await self._rate_limit()
            
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": False
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Retry logic
            for attempt in range(self.max_retries):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.post(
                            f"{self.base_url}/chat/completions",
                            json=payload,
                            headers=headers
                        )
                        
                        if response.status_code == 429:
                            # Rate limited - wait and retry
                            wait_time = self.retry_delay * (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(f"Rate limited, waiting {wait_time:.2f} seconds before retry {attempt + 1}/{self.max_retries}")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        response.raise_for_status()
                        
                        result = response.json()
                        self.last_request_time = time.time()
                        return result["choices"][0]["message"]["content"]
                
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        # Rate limited - wait and retry
                        wait_time = self.retry_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Rate limited (HTTP 429), waiting {wait_time:.2f} seconds before retry {attempt + 1}/{self.max_retries}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"HTTP error: {e}")
                        return f"Error: HTTP {e.response.status_code}"
                
                except httpx.TimeoutException:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Request timed out, retrying {attempt + 1}/{self.max_retries}")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        logger.error("LLM request timed out after all retries")
                        return "Error: Request timed out after all retries"
            
            return "Error: Max retries exceeded"
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error: {str(e)}"
    
    async def _rate_limit(self):
        """Ensure minimum time between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)
    
    async def generate_streaming_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM."""
        try:
            if not self.api_key:
                yield "Error: Groq API key not configured"
                return
            
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip() and line.startswith("data: "):
                            try:
                                data_str = line[6:]  # Remove "data: " prefix
                                if data_str.strip() == "[DONE]":
                                    break
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
        
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield f"Error: {str(e)}"
    
    async def check_model_availability(self) -> Dict[str, Any]:
        """Check if the model is available."""
        try:
            if not self.api_key:
                return {
                    "available": False,
                    "error": "Groq API key not configured",
                    "model": self.model
                }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=headers
                )
                response.raise_for_status()
                
                models = response.json()
                available_models = [model["id"] for model in models.get("data", [])]
                
                return {
                    "available": self.model in available_models,
                    "model": self.model,
                    "available_models": available_models
                }
        
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return {
                "available": False,
                "error": str(e),
                "model": self.model
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Groq API."""
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "Groq API key not configured"
                }
            
            # Test with a simple request
            test_response = await self.generate_response("Hello", temperature=0.1)
            
            if test_response.startswith("Error:"):
                return {
                    "success": False,
                    "error": test_response
                }
            
            return {
                "success": True,
                "message": "Connection successful",
                "model": self.model
            }
        
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class LLMClient:
    """Main LLM client interface for the development pod."""
    
    def __init__(self):
        self.groq = GroqClient()
    
    async def initialize(self) -> bool:
        """Initialize the LLM client and ensure model is available."""
        try:
            # Check if API key is configured
            if not self.groq.api_key:
                logger.error("Groq API key not configured. Please set GROQ_API_KEY in .env file")
                return False
            
            # Test connection
            connection_test = await self.groq.test_connection()
            
            if not connection_test["success"]:
                logger.error(f"Failed to connect to Groq: {connection_test['error']}")
                return False
            
            # Check if model is available
            availability = await self.groq.check_model_availability()
            
            if not availability["available"]:
                logger.error(f"Model {self.groq.model} not available. Available models: {availability.get('available_models', [])}")
                return False
            
            logger.info(f"LLM client initialized with model: {self.groq.model}")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing LLM client: {e}")
            return False
    
    async def generate_planner_response(self, prompt: str) -> str:
        """Generate response for planner agent."""
        system_prompt = """You are a software development planner agent. Your role is to:
1. Break down complex development tasks into smaller, manageable subtasks
2. Identify dependencies between tasks
3. Suggest the best approach for implementation
4. Coordinate with other agents (coder, tester)

Always provide structured, actionable plans with clear task descriptions and dependencies.

Format your response as a detailed implementation plan with:
1. **Project Overview**: Brief description of what will be built
2. **Architecture**: High-level design and structure
3. **Implementation Steps**: Detailed step-by-step breakdown
4. **File Structure**: What files need to be created
5. **Dependencies**: External libraries or modules needed
6. **Testing Strategy**: How the project will be tested

Be specific about file names, functions, and implementation details."""
        
        return await self.groq.generate_response(
            prompt,
            temperature=config.planner_temperature,
            system_prompt=system_prompt
        )
    
    async def generate_coder_response(self, prompt: str) -> str:
        """Generate response for coder agent."""
        system_prompt = """You are an expert software development coder agent specializing in production-ready code. Your role is to:

1. Write clean, efficient, and well-documented production-ready code
2. Follow industry best practices and coding standards
3. Implement features with proper error handling and validation
4. Use modern frameworks and libraries
5. Create scalable and maintainable code
6. Include comprehensive logging and monitoring
7. Implement security best practices
8. Add proper configuration management
9. Include database migrations and seeders
10. Create API documentation and endpoints

CRITICAL REQUIREMENTS:
- Generate COMPLETE, WORKING, PRODUCTION-READY code
- Use modern Python frameworks (FastAPI, Flask, Django)
- Include proper error handling, logging, and validation
- Add database models with relationships
- Include authentication and authorization
- Create beautiful, responsive frontend with modern CSS/JS
- Add Docker configuration for deployment
- Include comprehensive tests
- Add API documentation
- Use environment variables for configuration

FORMAT: Always provide complete files in this exact format:

File: app.py
```python
# Complete production-ready application code
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
import logging
import os
from typing import List, Optional
# ... complete implementation
```

File: models.py
```python
# Complete database models with relationships
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
# ... complete models
```

File: requirements.txt
```txt
# All required dependencies with versions
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
# ... complete dependencies
```

File: Dockerfile
```dockerfile
# Complete Docker configuration
FROM python:3.11-slim
# ... complete Docker setup
```

File: static/css/style.css
```css
/* Modern, responsive CSS */
:root {
  --primary-color: #667eea;
  --secondary-color: #764ba2;
}
/* ... complete styling */
```

File: templates/index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Modern Web App</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <!-- Complete HTML structure -->
</body>
</html>
```

ALWAYS generate multiple files for a complete application. Make it production-ready with:
- Proper project structure
- Database configuration
- Authentication system
- API endpoints
- Frontend interface
- Error handling
- Logging
- Configuration management
- Docker setup
- Tests
- Documentation"""
        
        return await self.groq.generate_response(
            prompt,
            temperature=config.coder_temperature,
            system_prompt=system_prompt
        )
    
    async def generate_tester_response(self, prompt: str) -> str:
        """Generate response for tester agent."""
        system_prompt = """You are a software testing agent. Your role is to:
1. Write comprehensive test cases
2. Identify edge cases and potential bugs
3. Ensure code quality and reliability
4. Run tests and analyze results
5. Suggest improvements for test coverage

IMPORTANT: Always provide complete, working test files. Use this format:

File: test_filename.py
```python
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from your_module import your_function

class TestYourFunction:
    def test_basic_functionality(self):
        # Test basic functionality
        result = your_function("test_input")
        assert result is not None
    
    def test_edge_cases(self):
        # Test edge cases
        with pytest.raises(ValueError):
            your_function(None)
    
    def test_error_handling(self):
        # Test error handling
        pass

if __name__ == "__main__":
    pytest.main([__file__])
```

Always include proper imports, test classes, and executable test code."""
        
        return await self.groq.generate_response(
            prompt,
            temperature=config.tester_temperature,
            system_prompt=system_prompt
        )
    
    async def generate_general_response(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate a general response."""
        return await self.groq.generate_response(prompt, temperature=temperature)
