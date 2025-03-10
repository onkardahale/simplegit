"""
Reference management for SimpleGit (branches, HEAD, etc.)
"""

import os
from utils.file_operations import ensure_dir, safe_write

class Reference:
    """Manages Git references (branches, HEAD, etc.)"""
    
    def __init__(self, repo):
        self.repo = repo
    
    def update_ref(self, ref_name, sha1):
        """Update a reference to point to the given SHA-1"""
        ref_path = os.path.join(self.repo.git_dir, ref_name)
        ensure_dir(os.path.dirname(ref_path))
        safe_write(ref_path, f"{sha1}\n")
        return True
    
    def get_ref(self, ref_name):
        """Get the SHA-1 that a reference points to"""
        ref_path = os.path.join(self.repo.git_dir, ref_name)
        if not os.path.exists(ref_path):
            return None
        
        with open(ref_path, "r") as f:
            return f.read().strip()
    
    def delete_ref(self, ref_name):
        """Delete a reference"""
        ref_path = os.path.join(self.repo.git_dir, ref_name)
        if os.path.exists(ref_path):
            os.remove(ref_path)
            return True
        return False
    
    def list_refs(self, prefix="refs/"):
        """List all references with the given prefix"""
        base_path = os.path.join(self.repo.git_dir, prefix)
        if not os.path.exists(base_path):
            return {}
        
        refs = {}
        for root, dirs, files in os.walk(base_path):
            for file in files:
                full_path = os.path.join(root, file)
                ref_path = os.path.relpath(full_path, self.repo.git_dir)
                refs[ref_path] = self.get_ref(ref_path)
        
        return refs
    
    def create_branch(self, branch_name, sha1):
        """Create a new branch pointing to the given commit"""
        ref_path = f"refs/heads/{branch_name}"
        return self.update_ref(ref_path, sha1)
    
    def get_branch(self, branch_name):
        """Get the SHA-1 that a branch points to"""
        return self.get_ref(f"refs/heads/{branch_name}")
    
    def delete_branch(self, branch_name):
        """Delete a branch"""
        return self.delete_ref(f"refs/heads/{branch_name}")
    
    def list_branches(self):
        """List all branches and their target commits"""
        branches = {}
        refs = self.list_refs("refs/heads/")
        for ref_path, sha1 in refs.items():
            branch_name = ref_path.replace("refs/heads/", "")
            branches[branch_name] = sha1
        return branches
    
    def update_HEAD(self, target):
        """
        Update HEAD to point to the given target
        If target is a branch name, points HEAD to that branch
        If target is a SHA-1, puts HEAD in detached state
        """
        if target.startswith("refs/heads/") or os.path.exists(os.path.join(self.repo.git_dir, f"refs/heads/{target}")):
            # Point to a branch
            if not target.startswith("refs/heads/"):
                target = f"refs/heads/{target}"
            content = f"ref: {target}"
        else:
            # Detached HEAD state (points directly to a commit)
            content = target
        
        safe_write(self.repo.HEAD_file, content)
        return True
    
    def get_HEAD(self):
        """
        Get the current HEAD target
        Returns a tuple (is_detached, target) where:
        - is_detached is a boolean indicating if HEAD is detached
        - if is_detached is False, target is the branch name
        - if is_detached is True, target is the commit SHA-1
        """
        if not os.path.exists(self.repo.HEAD_file):
            return False, None
        
        with open(self.repo.HEAD_file, "r") as f:
            content = f.read().strip()
        
        if content.startswith("ref: "):
            # HEAD points to a branch
            ref = content[5:]  # Remove "ref: "
            if ref.startswith("refs/heads/"):
                branch = ref[11:]  # Remove "refs/heads/"
            else:
                branch = ref
            return False, branch
        else:
            # Detached HEAD
            return True, content
    
    def resolve_HEAD(self):
        """
        Resolve HEAD to a commit SHA-1
        Returns the SHA-1 of the commit that HEAD points to
        """
        is_detached, target = self.get_HEAD()
        
        if is_detached:
            # HEAD already points to a commit
            return target
        else:
            # HEAD points to a branch, resolve the branch
            return self.get_branch(target)