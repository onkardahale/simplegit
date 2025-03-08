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
