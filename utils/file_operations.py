"""
File system utilities for SimpleGit
"""

import os
import shutil
import tempfile

def ensure_dir(path):
    """Ensure a directory exists, creating it if necessary"""
    if not os.path.exists(path):
        os.makedirs(path)

def safe_write(path, content, mode="w"):
    """
    Safely write content to a file using a temporary file
    to avoid corrupting the file if the process is interrupted
    """
    # Create temporary file in the same directory
    dir_name = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile(mode=mode, dir=dir_name, delete=False) as temp_file:
        if mode.startswith("w") and isinstance(content, str):
            temp_file.write(content)
        else:
            temp_file.write(content)
    
    # Atomic replace
    shutil.move(temp_file.name, path)

def list_files(directory, ignore_patterns=None):
    """
    List all files in a directory recursively
    Ignores files/directories matching patterns in ignore_patterns
    """
    ignore_patterns = ignore_patterns or [".simplegit"]
    files = []
    
    for root, dirs, filenames in os.walk(directory):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in ignore_patterns)]
        
        for filename in filenames:
            # Skip ignored files
            if any(pattern in filename for pattern in ignore_patterns):
                continue
            
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, directory)
            files.append(rel_path)
    
    return sorted(files)

def calculate_relative_path(path, relative_to):
    """Calculate a path relative to another path"""
    return os.path.relpath(path, relative_to)