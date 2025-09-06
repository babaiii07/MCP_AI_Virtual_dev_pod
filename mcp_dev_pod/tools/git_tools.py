"""Git tools for the MCP Multi-Agent Developer Pod."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from git import Repo, InvalidGitRepositoryError
from git.exc import GitCommandError
import os

from ..config import config

logger = logging.getLogger(__name__)


class GitTools:
    """Git operations for the development pod."""
    
    def __init__(self):
        self.author_name = config.git_author_name
        self.author_email = config.git_author_email
    
    async def get_status(self, path: str = ".") -> Dict[str, Any]:
        """Get git repository status."""
        try:
            repo = Repo(path)
            
            # Get current branch
            current_branch = repo.active_branch.name if not repo.head.is_detached else "detached"
            
            # Get status
            status = {
                "is_git_repo": True,
                "current_branch": current_branch,
                "is_dirty": repo.is_dirty(),
                "untracked_files": repo.untracked_files,
                "modified_files": [item.a_path for item in repo.index.diff(None)],
                "staged_files": [item.a_path for item in repo.index.diff("HEAD")],
                "last_commit": {
                    "hash": repo.head.commit.hexsha[:8],
                    "message": repo.head.commit.message.strip(),
                    "author": repo.head.commit.author.name,
                    "date": repo.head.commit.committed_datetime.isoformat()
                } if repo.head.commit else None
            }
            
            return status
        
        except InvalidGitRepositoryError:
            return {
                "is_git_repo": False,
                "error": "Not a git repository"
            }
        except Exception as e:
            logger.error(f"Error getting git status: {e}")
            return {
                "is_git_repo": False,
                "error": str(e)
            }
    
    async def commit(self, message: str, path: str = ".") -> Dict[str, Any]:
        """Commit changes to git."""
        try:
            repo = Repo(path)
            
            # Check if there are changes to commit
            if not repo.is_dirty() and not repo.untracked_files:
                return {
                    "success": False,
                    "message": "No changes to commit"
                }
            
            # Add all changes
            repo.git.add(A=True)
            
            # Commit with custom author
            commit = repo.index.commit(
                message,
                author=f"{self.author_name} <{self.author_email}>"
            )
            
            return {
                "success": True,
                "commit_hash": commit.hexsha[:8],
                "message": message,
                "files_committed": len(repo.index.diff("HEAD~1"))
            }
        
        except InvalidGitRepositoryError:
            return {
                "success": False,
                "error": "Not a git repository"
            }
        except GitCommandError as e:
            logger.error(f"Git command error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error committing: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_branch(self, branch_name: str, path: str = ".") -> Dict[str, Any]:
        """Create a new git branch."""
        try:
            repo = Repo(path)
            
            # Check if branch already exists
            if branch_name in [branch.name for branch in repo.branches]:
                return {
                    "success": False,
                    "error": f"Branch '{branch_name}' already exists"
                }
            
            # Create and checkout new branch
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            
            return {
                "success": True,
                "branch_name": branch_name,
                "current_branch": repo.active_branch.name
            }
        
        except InvalidGitRepositoryError:
            return {
                "success": False,
                "error": "Not a git repository"
            }
        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def switch_branch(self, branch_name: str, path: str = ".") -> Dict[str, Any]:
        """Switch to a different git branch."""
        try:
            repo = Repo(path)
            
            # Check if branch exists
            if branch_name not in [branch.name for branch in repo.branches]:
                return {
                    "success": False,
                    "error": f"Branch '{branch_name}' does not exist"
                }
            
            # Switch to branch
            repo.git.checkout(branch_name)
            
            return {
                "success": True,
                "current_branch": repo.active_branch.name
            }
        
        except InvalidGitRepositoryError:
            return {
                "success": False,
                "error": "Not a git repository"
            }
        except Exception as e:
            logger.error(f"Error switching branch: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_branches(self, path: str = ".") -> Dict[str, Any]:
        """Get list of git branches."""
        try:
            repo = Repo(path)
            
            branches = []
            for branch in repo.branches:
                branches.append({
                    "name": branch.name,
                    "is_current": branch == repo.active_branch,
                    "last_commit": branch.commit.hexsha[:8] if branch.commit else None
                })
            
            return {
                "success": True,
                "branches": branches,
                "current_branch": repo.active_branch.name if not repo.head.is_detached else "detached"
            }
        
        except InvalidGitRepositoryError:
            return {
                "success": False,
                "error": "Not a git repository"
            }
        except Exception as e:
            logger.error(f"Error getting branches: {e}")
            return {
                "success": False,
                "error": str(e)
            }
