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

def main():
    parser = argparse.ArgumentParser(description="SimpleGit: A minimal Git implementation for testing")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # init command
    parser_init = subparsers.add_parser("init", help="Create an empty SimpleGit repository")
    parser_init.add_argument("path", nargs="?", default=".", help="Where to create the repository")
    
    args = parser.parse_args()
    
    if args.command == "init":
        return cmd_init(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())