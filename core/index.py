"""
Index/staging area management
"""

import os
import json

from core.object import Blob

class Index:
    """Represents the Git index (staging area)"""
    
    def __init__(self, repo):
        self.repo = repo
        self.index_file = os.path.join(repo.git_dir, "index")
        self.entries = {}
        self.load()
    
    def load(self):
        """Load the index from file"""
        if os.path.exists(self.index_file):
            with open(self.index_file, "r") as f:
                try:
                    self.entries = json.load(f)
                except json.JSONDecodeError:
                    self.entries = {}
        else:
            self.entries = {}
    
    def save(self):
        """Save the index to file"""
        with open(self.index_file, "w") as f:
            json.dump(self.entries, f, indent=2)
    
    def add(self, path):
        """Add a file or directory to the index"""
        full_path = os.path.join(self.repo.repo_path, path)
        
        if not os.path.exists(full_path):
            print(f"Error: '{path}' does not exist")
            return False
        
        if os.path.isdir(full_path):
            # Add all files in directory
            success = True
            for root, _, files in os.walk(full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.repo.repo_path)
                    if not self._is_git_file(rel_path):
                        if not self._add_file(rel_path):
                            success = False
            return success
        else:
            # Add single file
            rel_path = os.path.relpath(full_path, self.repo.repo_path)
            if not self._is_git_file(rel_path):
                return self._add_file(rel_path)
        
        return False
    
    def _is_git_file(self, path):
        """Check if a file is in the .simplegit directory"""
        return path.startswith(".simplegit")
    
    def _add_file(self, path):
        """Add a single file to the index"""
        full_path = os.path.join(self.repo.repo_path, path)
        
        try:
            # Read file content
            with open(full_path, "rb") as f:
                content = f.read()
            
            # Hash and store the content
            blob = Blob(self.repo)
            sha1 = blob.create(content)
            
            # Add to index
            self.entries[path] = {
                "sha1": sha1,
                "mode": "100644",  # Regular file
                "size": len(content),
                "mtime": os.path.getmtime(full_path)
            }
            
            print(f"Added {path} to index")
            return True
        except Exception as e:
            print(f"Error adding {path}: {e}")
            return False
    
    