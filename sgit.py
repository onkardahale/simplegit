#!/usr/bin/env python3
"""
SimpleGit: CLI

This script implements:
- Initializing a repository (init)
"""

import os
import sys
import argparse

from core.repository import Repository
from core.ref import Reference

def cmd_init(args):
    """Initialize a new repository"""
    repo = Repository(args.path)
    success = repo.init()
    return 0 if success else 1

def cmd_status(args):
    repo = Repository.find_repository()
    if not repo:
        print("Not a SimpleGit repository")
        return 1
    
    branch = repo.get_current_branch()
    
    if branch:
        print(f"On branch {branch}")
    else:
        print("Not currently on any branch")
    
    modified, untracked = repo.index.get_status()
    
    if not modified and not untracked:
        print("nothing to commit, working tree clean")
    else:
        if modified:
            print("\nChanges not staged for commit:")
            print("  (use \"simplegit add <file>...\" to update what will be committed)")
            for file in modified:
                print(f"\tmodified:   {file}")
        
        if untracked:
            print("\nUntracked files:")
            print("  (use \"simplegit add <file>...\" to include in what will be committed)")
            for file in untracked:
                print(f"\t{file}")
        
        print("\nno changes added to commit")
    
    return 0

def cmd_add(args):
    """Add file contents to the index"""
    repo = Repository.find_repository()
    if not repo:
        print("Not a SimpleGit repository")
        return 1
    
    for path in args.paths:
        repo.index.add(path)
    
    repo.index.save()
    return 0

def cmd_log(args):
    """Show commit logs"""
    repo = Repository.find_repository()
    if not repo:
        print("Not a SimpleGit repository")
        return 1
    
    commits = repo.log(args.max_count)
    
    for commit in commits:
        sha1 = commit.get("parent", "")  # This is actually the current commit's SHA-1
        date = commit.get("author_date", "Unknown date")
        author = commit.get("author_name", "Unknown author")
        message = commit.get("message", "")
        branch_display = commit.get("branch_display", "")
        
        print(f"commit {sha1} {branch_display}")
        print(f"Author: {author}")
        print(f"Date:   {date}")
        print()
        print(f"    {message}")
        print()
    
    return 0

def cmd_commit(args):
    """Record changes to the repository"""
    repo = Repository.find_repository()
    if not repo:
        print("Not a SimpleGit repository")
        return 1
    
    if not args.message:
        print("Aborting commit due to empty commit message")
        return 1
    
    commit_sha = repo.commit(args.message)
    if commit_sha:
        return 0
    return 1

def cmd_config(args):
    """Get and set repository options"""
    repo = Repository.find_repository()
    if not repo:
        print("Not a SimpleGit repository")
        return 1
    
    from core.config import Config
    config = Config(repo)
    
    if args.get:
        # Get config value
        section, key = args.get.split(".", 1)
        value = config.get(section, key)
        if value is not None:
            print(value)
            return 0
        else:
            print(f"Config value '{args.get}' not found")
            return 1
    
    if args.name:
        # Set user.name
        config.set("user", "name", args.name)
        print(f"Set user.name to '{args.name}'")
        return 0
    
    if args.email:
        # Set user.email
        config.set("user", "email", args.email)
        print(f"Set user.email to '{args.email}'")
        return 0
    
    if args.section and args.key and args.value:
        # Set arbitrary config value
        config.set(args.section, args.key, args.value)
        print(f"Set {args.section}.{args.key} to '{args.value}'")
        return 0
    
    # No action specified, show usage
    print("Usage: simplegit config --get <section.key>")
    print("   or: simplegit config --name <username>")
    print("   or: simplegit config --email <email>")
    print("   or: simplegit config <section> <key> <value>")
    return 1

def cmd_branch(args):
    """List, create, or delete branches"""
    repo = Repository.find_repository()
    if not repo:
        print("Not a SimpleGit repository")
        return 1
    
    refs = Reference(repo)
    
    if args.delete:
        # Delete branch
        if refs.delete_branch(args.delete):
            print(f"Deleted branch {args.delete}")
            return 0
        else:
            print(f"Branch {args.delete} not found")
            return 1
    
    if args.name:
        # Create branch
        head_sha1 = refs.resolve_HEAD()
        if not head_sha1:
            print("Cannot create branch: no commits yet")
            return 1
        
        if refs.get_branch(args.name):
            print(f"Branch {args.name} already exists")
            return 1
        
        refs.create_branch(args.name, head_sha1)
        print(f"Created branch {args.name}")
        return 0
    
    # List branches
    branches = refs.list_branches()
    is_detached, current = refs.get_HEAD()
    
    if not branches:
        print("No branches yet")
    else:
        for name, sha1 in branches.items():
            prefix = "* " if name == current and not is_detached else "  "
            print(f"{prefix}{name}")
    
    return 0

## def cmd_checkout 

def main():
    parser = argparse.ArgumentParser(description="SimpleGit: A minimal Git implementation for testing")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # init command
    parser_init = subparsers.add_parser("init", help="Create an empty SimpleGit repository")
    parser_init.add_argument("path", nargs="?", default=".", help="Where to create the repository")
    
    # status command
    parser_status = subparsers.add_parser("status", help="Show the working tree status")

    # add command
    parser_add = subparsers.add_parser("add", help="Add file contents to the index")
    parser_add.add_argument("paths", nargs="+", help="Files to add")

    # log command
    parser_log = subparsers.add_parser("log", help="Show commit logs")
    parser_log.add_argument("-n", "--max-count", type=int, help="Limit number of commits")

    # commit command
    parser_commit = subparsers.add_parser("commit", help="Record changes to the repository")
    parser_commit.add_argument("-m", "--message", required=True, help="Commit message")

    # config command
    parser_config = subparsers.add_parser("config", help="Get and set repository options")
    parser_config.add_argument("--get", help="Get a config value (format: section.key)")
    parser_config.add_argument("--name", help="Set user name")
    parser_config.add_argument("--email", help="Set user email")
    parser_config.add_argument("section", nargs="?", help="Config section")
    parser_config.add_argument("key", nargs="?", help="Config key")
    parser_config.add_argument("value", nargs="?", help="Config value")
    
    args = parser.parse_args()
    
    if args.command == "init":
        return cmd_init(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "add":
        return cmd_add(args)
    elif args.command == "log":
        return cmd_log(args)
    elif args.command == "commit":
        return cmd_commit(args)
    elif args.command == "config":
        return cmd_config(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())