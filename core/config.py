"""
Configuration management for SimpleGit
"""

import os

class Config:
    """Manages Git configuration"""
    
    def __init__(self, repo):
        self.repo = repo
        self.config_file = os.path.join(repo.git_dir, "config")
        self.config = {}
        self.load()