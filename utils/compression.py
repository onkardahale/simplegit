"""
Compression utilities for SimpleGit
"""

import zlib

def compress(data):
    """Compress data using zlib"""
    return zlib.compress(data)

def decompress(data):
    """Decompress data using zlib"""
    return zlib.decompress(data)