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
    
    args = parser.parse_args()
    
    if args.command == "init":
        return cmd_init(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "add":
        return cmd_add(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())