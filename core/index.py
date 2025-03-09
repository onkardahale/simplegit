"""
Index/staging area management
"""

import os
import json

from core.object import Blob, Tree
from utils.file_operations import list_files, ensure_dir, safe_write
from collections import defaultdict

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
            try:
                with open(self.index_file, "r") as f:
                    self.entries = json.load(f)
            except json.JSONDecodeError:
                self.entries = {}
        else:
            self.entries = {}
    
    def save(self):
        """Save the index to file using safe_write"""
        # Ensure the directory exists
        ensure_dir(os.path.dirname(self.index_file))
        # Use safe_write to atomically write the index
        safe_write(self.index_file, json.dumps(self.entries, indent=2))
    
    def add(self, path):
        """Add a file or directory to the index"""
        full_path = os.path.join(self.repo.repo_path, path)
        
        if not os.path.exists(full_path):
            print(f"Error: '{path}' does not exist")
            return False
        
        if os.path.isdir(full_path):
            # Add all files in directory using list_files
            success = True
            ignore_patterns = [".simplegit"]
            files = list_files(full_path, ignore_patterns)
            
            for rel_file in files:
                file_path = os.path.join(path, rel_file)
                if not self._add_file(file_path):
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
    
    def get_status(self):
        """
        Get status of working directory compared to index
        Returns a tuple (modified, untracked)
        """
        modified = []
        untracked = []
        
        # Check tracked files for modifications
        for path, info in self.entries.items():
            full_path = os.path.join(self.repo.repo_path, path)
            if os.path.exists(full_path):
                # File exists, check if modified
                try:
                    with open(full_path, "rb") as f:
                        content = f.read()
                    
                    blob = Blob(self.repo)
                    current_sha1 = blob.create(content)
                    if current_sha1 != info["sha1"]:
                        modified.append(path)
                except:
                    modified.append(path)
            else:
                # File deleted
                modified.append(path)
        
        # Check for untracked files using list_files
        all_files = list_files(self.repo.repo_path, [".simplegit"])
        untracked = [f for f in all_files if f not in self.entries]
        
        return modified, untracked
    
    def write_tree(self):
        """
        Create a tree object from the current index
        Returns the SHA-1 of the tree
        """
        # Group files by directory
        dirs = defaultdict(dict)
        
        for path, file_info in self.entries.items():
            # Split path into directory and filename
            dirname, filename = os.path.split(path)
            
            if dirname:
                dirs[dirname][filename] = file_info
            else:
                dirs[""][filename] = file_info
        
        # Create tree objects from bottom up
        tree = Tree(self.repo)
        return self._write_tree_recursive("", dirs, tree)
    
    def _write_tree_recursive(self, path, dirs, tree):
        """Recursively create tree objects"""
        entries = []
        
        # Add files for current directory
        for filename, file_info in dirs[path].items():
            entries.append((file_info["mode"], filename, file_info["sha1"]))
        
        # Add subdirectories
        subdirs = [d for d in dirs.keys() if d.startswith(path + "/") if d != path]
        for subdir in subdirs:
            rel_path = os.path.basename(subdir)
            subdir_sha1 = self._write_tree_recursive(subdir, dirs, tree)
            entries.append(("040000", rel_path, subdir_sha1))
        
        # Sort entries by name for deterministic tree hashing
        entries.sort(key=lambda x: x[1])  # Sort by filename (index 1)
        
        # Create tree object
        return tree.create(entries)