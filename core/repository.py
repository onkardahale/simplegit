"""
Repository management for SimpleGit
"""

import os
import json
from pathlib import Path

from core.index import Index
from utils.file_operations import ensure_dir

class Repository:
    """Represents a SimpleGit repository"""
    
    def __init__(self, path="."):
        self.repo_path = os.path.abspath(path)
        self.git_dir = os.path.join(self.repo_path, ".simplegit")
        self.objects_dir = os.path.join(self.git_dir, "objects")
        self.refs_dir = os.path.join(self.git_dir, "refs")
        self.heads_dir = os.path.join(self.refs_dir, "heads")
        self.HEAD_file = os.path.join(self.git_dir, "HEAD")
        self.config_file = os.path.join(self.git_dir, "config")
        
        # Index is loaded on demand
        self._index = None
    
    @property
    def index(self):
        """Lazy-load the index"""
        if self._index is None:
            self._index = Index(self)
        return self._index
    
    def init(self):
        """Initialize a new SimpleGit repository"""
        if os.path.exists(self.git_dir):
            print(f"Repository already exists at {self.repo_path}")
            return False
        
        # Create directory structure
        ensure_dir(self.objects_dir)
        ensure_dir(self.heads_dir)
        
        # Create HEAD file pointing to master branch
        with open(self.HEAD_file, "w") as f:
            f.write("ref: refs/heads/master")
        
        # Create config file
        with open(self.config_file, "w") as f:
            f.write("[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false")
        
        # Create empty index
        self.index.save()
        
        print(f"Initialized empty SimpleGit repository in {self.git_dir}")
        return True
    
    def get_current_branch(self):
        """Get the name of the current branch"""
        if not os.path.exists(self.HEAD_file):
            return None
            
        with open(self.HEAD_file, "r") as f:
            head_content = f.read().strip()
        
        if head_content.startswith("ref: refs/heads/"):
            return head_content[16:]  # Remove "ref: refs/heads/"
        else:
            # Detached HEAD state
            return None
    
    def is_repository(self):
        """Check if this directory is a SimpleGit repository"""
        return os.path.exists(self.git_dir) and os.path.isdir(self.git_dir)
    
    @classmethod
    def find_repository(cls, path="."):
        """Find the repository by searching up from the current directory"""
        path = os.path.abspath(path)
        while path != "/":
            repo = cls(path)
            if repo.is_repository():
                return repo
            path = os.path.dirname(path)
        return None