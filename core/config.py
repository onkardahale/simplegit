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

    def load(self):
        """Load config from file"""
        if not os.path.exists(self.config_file):
            return
        
        with open(self.config_file, "r") as f:
            section = None
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Check for section header
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1]  # Remove brackets
                    self.config.setdefault(section, {})
                # Check for key-value pair
                elif "=" in line and section:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    self.config[section][key] = value
                    
    def get(self, section, key, default=None):
        """Get a config value"""
        return self.config.get(section, {}).get(key, default)
    
    def get_user_name(self):
        """Get the user's name"""
        return self.get("user", "name", "SimpleGit User")
    
    def get_user_email(self):
        """Get the user's email"""
        return self.get("user", "email", "user@example.com")
    
    def get_user_info(self):
        """Get formatted user info (for commit author/committer)"""
        name = self.get_user_name()
        email = self.get_user_email()
        return f"{name} <{email}>"
    
    def save(self):
        """Save config to file"""
        with open(self.config_file, "w") as f:
            for section, kvs in self.config.items():
                f.write(f"[{section}]\n")
                for key, value in kvs.items():
                    f.write(f"\t{key} = {value}\n")
                f.write("\n")
    
    def set(self, section, key, value):
        """Set a config value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        
        ## must save config