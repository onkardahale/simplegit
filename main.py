#!/usr/bin/env python3
"""
SimpleGit: A rudimentary Git implementation

This script implements basic Git functionality including:
- Initializing a repository
"""

import os
import sys
import json

class SimpleGit:
    def __init__(self, repo_path="."):
        self.repo_path = os.path.abspath(repo_path)
        self.git_dir = os.path.join(self.repo_path, ".simplegit")
        self.objects_dir = os.path.join(self.git_dir, "objects")
        self.refs_dir = os.path.join(self.git_dir, "refs")
        self.heads_dir = os.path.join(self.refs_dir, "heads")
        self.index_file = os.path.join(self.git_dir, "index")
        self.HEAD_file = os.path.join(self.git_dir, "HEAD")
        self.config_file = os.path.join(self.git_dir, "config")
        
        self.index = {}  # Staged files
        self.current_branch = "master"
        
    def init(self):
        """Initialize a new SimpleGit repository"""
        if os.path.exists(self.git_dir):
            print(f"Repository already exists at {self.repo_path}")
            return
        
        # Create directory structure
        os.makedirs(self.objects_dir, exist_ok=True)
        os.makedirs(self.heads_dir, exist_ok=True)
        
        # Create HEAD file pointing to master branch
        with open(self.HEAD_file, "w") as f:
            f.write("ref: refs/heads/master")
        
        # Create empty index file
        with open(self.index_file, "w") as f:
            json.dump({}, f)
        
        # Create config file
        with open(self.config_file, "w") as f:
            f.write("[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false")
        
        print(f"Initialized empty SimpleGit repository in {self.git_dir}")
    

def main():
    if len(sys.argv) < 2:
        print("Usage: simplegit <command> [<args>]")
        return
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    git = SimpleGit()
    
    if command == "init":
        git.init()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()