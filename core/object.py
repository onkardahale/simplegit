"""
Git object handling (blobs, trees, commits)
"""

import os
import hashlib
import zlib
import time
from datetime import datetime

from utils.file_operations import ensure_dir
from utils.compression import compress, decompress

class GitObject:
    """Base class for Git objects"""
    def __init__(self, repo):
        self.repo = repo
    
    def hash_object(self, data, obj_type):
        """
        Hash an object and store it in the objects directory
        Returns the SHA-1 hash of the object
        """
        # Prepare content with header
        header = f"{obj_type} {len(data)}\0"
        store = header.encode() + data if isinstance(data, bytes) else header.encode() + data.encode()
        
        # Calculate SHA-1 hash
        sha1 = hashlib.sha1(store).hexdigest()
        
        # Store the object
        object_path = os.path.join(self.repo.objects_dir, sha1[:2], sha1[2:])
        ensure_dir(os.path.dirname(object_path))
        
        # Compress and write
        with open(object_path, "wb") as f:
            f.write(compress(store))
        
        return sha1
    
    def read_object(self, sha1):
        """Read an object from the objects directory"""
        object_path = os.path.join(self.repo.objects_dir, sha1[:2], sha1[2:])
        
        if not os.path.exists(object_path):
            print(f"Object {sha1} not found")
            return None, None
        
        # Read and decompress
        with open(object_path, "rb") as f:
            data = decompress(f.read())
        
        # Parse header and content
        null_index = data.find(b'\0')
        header = data[:null_index].decode()
        object_type = header.split()[0]
        content = data[null_index + 1:]
        
        return object_type, content


class Blob(GitObject):
    """Represents a file in Git"""
    
    def create(self, content):
        """Create a blob object from content"""
        if isinstance(content, str):
            content = content.encode()
        return self.hash_object(content, "blob")
    
    def read(self, sha1):
        """Read a blob object"""
        obj_type, content = self.read_object(sha1)
        if obj_type != "blob":
            raise ValueError(f"Expected blob, got {obj_type}")
        return content


class Tree(GitObject):
    """Represents a directory in Git"""
    
    def create(self, entries):
        """
        Create a tree object from entries
        entries: List of (mode, name, sha1) tuples
        """
        # Build tree content
        tree_content = b""
        for mode, name, sha1 in sorted(entries, key=lambda x: x[1]):
            entry = f"{mode} {name}\0".encode()
            entry += bytes.fromhex(sha1)
            tree_content += entry
        
        return self.hash_object(tree_content, "tree")
    
    def read(self, sha1):
        """
        Read a tree object
        Returns a list of (mode, name, sha1) tuples
        """
        obj_type, content = self.read_object(sha1)
        if obj_type != "tree":
            raise ValueError(f"Expected tree, got {obj_type}")
        
        entries = []
        i = 0
        while i < len(content):
            # Find the null byte that separates mode+name from SHA-1
            null_pos = content.find(b'\0', i)
            if null_pos == -1:
                break
            
            # Parse mode and name
            mode_name = content[i:null_pos].decode()
            space_pos = mode_name.find(" ")
            mode = mode_name[:space_pos]
            name = mode_name[space_pos + 1:]
            
            # Extract SHA-1 (20 bytes)
            sha1_bytes = content[null_pos + 1:null_pos + 21]
            sha1 = "".join(f"{b:02x}" for b in sha1_bytes)
            
            entries.append((mode, name, sha1))
            
            # Move to next entry
            i = null_pos + 21
        
        return entries