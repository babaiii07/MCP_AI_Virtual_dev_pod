"""File system tools for the MCP Multi-Agent Developer Pod."""

import asyncio
import aiofiles
import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FileTools:
    """File system operations for the development pod."""
    
    async def read_file(self, path: str) -> str:
        """Read file contents."""
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return content
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            raise
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            return {
                "success": True,
                "path": path,
                "size": len(content.encode('utf-8'))
            }
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_directory(self, path: str) -> List[Dict[str, Any]]:
        """List directory contents."""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Directory not found: {path}")
            
            if not os.path.isdir(path):
                raise NotADirectoryError(f"Path is not a directory: {path}")
            
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                stat = os.stat(item_path)
                
                items.append({
                    "name": item,
                    "path": item_path,
                    "is_directory": os.path.isdir(item_path),
                    "is_file": os.path.isfile(item_path),
                    "size": stat.st_size if os.path.isfile(item_path) else None,
                    "modified": stat.st_mtime
                })
            
            return sorted(items, key=lambda x: (not x["is_directory"], x["name"]))
        
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            raise
    
    async def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory."""
        try:
            os.makedirs(path, exist_ok=True)
            return {
                "success": True,
                "path": path
            }
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file."""
        try:
            if not os.path.exists(path):
                return {
                    "success": False,
                    "error": f"File not found: {path}"
                }
            
            os.remove(path)
            return {
                "success": True,
                "path": path
            }
        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def copy_file(self, src: str, dst: str) -> Dict[str, Any]:
        """Copy a file."""
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            
            async with aiofiles.open(src, 'rb') as src_file:
                content = await src_file.read()
            
            async with aiofiles.open(dst, 'wb') as dst_file:
                await dst_file.write(content)
            
            return {
                "success": True,
                "source": src,
                "destination": dst
            }
        except Exception as e:
            logger.error(f"Error copying file {src} to {dst}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def move_file(self, src: str, dst: str) -> Dict[str, Any]:
        """Move a file."""
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            
            os.rename(src, dst)
            return {
                "success": True,
                "source": src,
                "destination": dst
            }
        except Exception as e:
            logger.error(f"Error moving file {src} to {dst}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_files(self, directory: str, pattern: str, recursive: bool = True) -> List[str]:
        """Search for files matching a pattern."""
        try:
            import fnmatch
            
            matches = []
            if recursive:
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if fnmatch.fnmatch(file, pattern):
                            matches.append(os.path.join(root, file))
            else:
                for file in os.listdir(directory):
                    if fnmatch.fnmatch(file, pattern):
                        matches.append(os.path.join(directory, file))
            
            return matches
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return []
    
    async def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get detailed file information."""
        try:
            if not os.path.exists(path):
                return {
                    "exists": False,
                    "error": f"File not found: {path}"
                }
            
            stat = os.stat(path)
            return {
                "exists": True,
                "path": path,
                "is_directory": os.path.isdir(path),
                "is_file": os.path.isfile(path),
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "permissions": oct(stat.st_mode)[-3:]
            }
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return {
                "exists": False,
                "error": str(e)
            }
