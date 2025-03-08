import os
import shutil
import pytest
from unittest.mock import MagicMock, patch
import hashlib
import zlib

# Import the modules to test
from core.object import GitObject, Blob, Tree
from utils.compression import compress, decompress
from utils.file_operations import ensure_dir, safe_write, list_files

class TestGitObject:
    @pytest.fixture
    def repo(self):
        """Create a mock repository object with temporary paths"""
        repo = MagicMock()
        # Create a temporary directory for objects
        repo.objects_dir = os.path.join(os.getcwd(), "test_objects")
        ensure_dir(repo.objects_dir)
        yield repo
        # Clean up after tests
        shutil.rmtree(repo.objects_dir)
    
    def test_hash_object(self, repo):
        """Test that hashing an object works correctly"""
        git_obj = GitObject(repo)
        test_data = "test content"
        obj_type = "blob"
        
        # Calculate expected SHA-1
        header = f"{obj_type} {len(test_data)}\0"
        store = header.encode() + test_data.encode()
        expected_sha1 = hashlib.sha1(store).hexdigest()
        
        # Hash the object
        sha1 = git_obj.hash_object(test_data, obj_type)
        
        # Verify hash matches expected
        assert sha1 == expected_sha1
        
        # Verify file exists in correct location
        object_path = os.path.join(repo.objects_dir, sha1[:2], sha1[2:])
        assert os.path.exists(object_path)
        
        # Verify file contents are correct
        with open(object_path, "rb") as f:
            stored_data = decompress(f.read())
        assert stored_data == store
    
    def test_read_object(self, repo):
        """Test that reading an object works correctly"""
        git_obj = GitObject(repo)
        test_data = "test content"
        obj_type = "blob"
        
        # Create and hash object
        sha1 = git_obj.hash_object(test_data, obj_type)
        
        # Read object
        read_type, read_content = git_obj.read_object(sha1)
        
        # Verify type and content
        assert read_type == obj_type
        assert read_content.decode() == test_data
    
    def test_read_nonexistent_object(self, repo):
        """Test reading an object that doesn't exist"""
        git_obj = GitObject(repo)
        fake_sha1 = "0123456789abcdef0123456789abcdef01234567"
        
        # Attempt to read nonexistent object
        obj_type, content = git_obj.read_object(fake_sha1)
        
        # Expect a None
        assert obj_type is None
        assert content is None


class TestBlob:
    @pytest.fixture
    def repo(self):
        """Create a mock repository object with temporary paths"""
        repo = MagicMock()
        repo.objects_dir = os.path.join(os.getcwd(), "test_objects")
        ensure_dir(repo.objects_dir)
        yield repo
        shutil.rmtree(repo.objects_dir)
    
    def test_create_blob(self, repo):
        """Test creating a blob from content"""
        blob = Blob(repo)
        test_content = "This is a test file content"
        
        # Create blob
        sha1 = blob.create(test_content)
        
        # Verify blob exists
        object_path = os.path.join(repo.objects_dir, sha1[:2], sha1[2:])
        assert os.path.exists(object_path)
        
        # Verify blob type and content
        git_obj = GitObject(repo)
        obj_type, content = git_obj.read_object(sha1)
        assert obj_type == "blob"
        assert content.decode() == test_content
    
    def test_create_blob_bytes(self, repo):
        """Test creating a blob from binary content"""
        blob = Blob(repo)
        test_content = b"Binary content \x00\x01\x02"
        
        # Create blob
        sha1 = blob.create(test_content)
        
        # Read and verify
        read_content = blob.read(sha1)
        assert read_content == test_content
    
    def test_read_blob(self, repo):
        """Test reading a blob"""
        blob = Blob(repo)
        test_content = "Blob content for reading test"
        
        # Create blob
        sha1 = blob.create(test_content)
        
        # Read blob
        content = blob.read(sha1)
        
        # Verify content
        assert content.decode() == test_content
    
    def test_read_invalid_blob(self, repo):
        """Test reading an object that isn't a blob"""
        # Create a tree instead of a blob
        git_obj = GitObject(repo)
        tree_content = b"tree content"
        sha1 = git_obj.hash_object(tree_content, "tree")
        
        # Try to read it as a blob
        blob = Blob(repo)
        with pytest.raises(ValueError) as e:
            blob.read(sha1)
        assert "Expected blob" in str(e.value)


class TestTree:
    @pytest.fixture
    def repo(self):
        """Create a mock repository object with temporary paths"""
        repo = MagicMock()
        repo.objects_dir = os.path.join(os.getcwd(), "test_objects")
        ensure_dir(repo.objects_dir)
        yield repo
        shutil.rmtree(repo.objects_dir)
    
    def test_create_tree(self, repo):
        """Test creating a tree from entries"""
        tree = Tree(repo)
        
        # Create some blobs first
        blob = Blob(repo)
        file1_sha = blob.create("File 1 content")
        file2_sha = blob.create("File 2 content")
        
        # Create tree entries
        entries = [
            ("100644", "file1.txt", file1_sha),
            ("100644", "file2.txt", file2_sha)
        ]
        
        # Create tree
        tree_sha = tree.create(entries)
        
        # Verify tree exists
        object_path = os.path.join(repo.objects_dir, tree_sha[:2], tree_sha[2:])
        assert os.path.exists(object_path)
        
        # Verify tree type
        git_obj = GitObject(repo)
        obj_type, _ = git_obj.read_object(tree_sha)
        assert obj_type == "tree"
    
    def test_read_tree(self, repo):
        """Test reading a tree"""
        # Create blobs
        blob = Blob(repo)
        file1_sha = blob.create("File 1 content")
        file2_sha = blob.create("File 2 content")
        
        # Create tree
        tree = Tree(repo)
        original_entries = [
            ("100644", "file1.txt", file1_sha),
            ("100644", "file2.txt", file2_sha)
        ]
        tree_sha = tree.create(original_entries)
        
        # Read tree
        read_entries = tree.read(tree_sha)
        
        # Verify entries match (should be sorted by name)
        assert len(read_entries) == len(original_entries)
        for i, entry in enumerate(sorted(original_entries, key=lambda x: x[1])):
            assert read_entries[i][0] == entry[0]  # mode
            assert read_entries[i][1] == entry[1]  # name
            assert read_entries[i][2] == entry[2]  # sha1
    
    def test_read_invalid_tree(self, repo):
        """Test reading an object that isn't a tree"""
        # Create a blob instead of a tree
        blob = Blob(repo)
        sha1 = blob.create("Not a tree")
        
        # Try to read it as a tree
        tree = Tree(repo)
        with pytest.raises(ValueError) as e:
            tree.read(sha1)
        assert "Expected tree" in str(e.value)

    def test_nested_tree(self, repo):
        """Test a tree that contains another tree"""
        blob = Blob(repo)
        tree = Tree(repo)
        
        # Create some files
        file1_sha = blob.create("File 1 content")
        file2_sha = blob.create("File 2 content")
        
        # Create a subtree
        subtree_entries = [
            ("100644", "subfile1.txt", file1_sha)
        ]
        subtree_sha = tree.create(subtree_entries)
        
        # Create main tree with file and subtree
        main_entries = [
            ("100644", "file2.txt", file2_sha),
            ("040000", "subdir", subtree_sha)
        ]
        main_tree_sha = tree.create(main_entries)
        
        # Read and verify main tree
        read_entries = tree.read(main_tree_sha)
        assert len(read_entries) == 2
        
        # Find directory entry
        dir_entries = [e for e in read_entries if e[0] == "040000"]
        assert len(dir_entries) == 1
        assert dir_entries[0][1] == "subdir"
        assert dir_entries[0][2] == subtree_sha
        
        # Read and verify subtree
        read_subtree = tree.read(subtree_sha)
        assert len(read_subtree) == 1
        assert read_subtree[0][1] == "subfile1.txt"
        assert read_subtree[0][2] == file1_sha

# Test utility functions
class TestUtilities:
    def test_compression(self):
        """Test compression and decompression"""
        # small test strings can become larger when compressed due to compression overhead
        # use a large strings
        test_data = b"Test data " * 20 
        
        compressed = compress(test_data)
        decompressed = decompress(compressed)
        
        assert decompressed == test_data
        # Verify it's actually compressed
        assert len(compressed) < len(test_data)
    
    def test_ensure_dir(self, tmpdir):
        """Test directory creation"""
        test_dir = os.path.join(tmpdir, "test_dir", "nested")
        ensure_dir(test_dir)
        assert os.path.exists(test_dir)
    
    @pytest.mark.parametrize("mode,content", [
        ("w", "Text content"),
        ("wb", b"Binary content")
    ])
    def test_safe_write(self, tmpdir, mode, content):
        """Test safe file writing with different modes"""
        test_file = os.path.join(tmpdir, "test_file.txt")
        safe_write(test_file, content, mode)
        
        # Verify file exists
        assert os.path.exists(test_file)
        
        # Verify content
        read_mode = "r" if mode == "w" else "rb"
        with open(test_file, read_mode) as f:
            read_content = f.read()
        assert read_content == content
    
    def test_list_files(self, tmpdir):
        """Test listing files with ignore patterns"""
        # Create test directory structure
        os.makedirs(os.path.join(tmpdir, "dir1"))
        os.makedirs(os.path.join(tmpdir, ".simplegit"))
        os.makedirs(os.path.join(tmpdir, "dir_to_include"))
        
        # Create test files
        open(os.path.join(tmpdir, "file1.txt"), "w").close()
        open(os.path.join(tmpdir, "file2.txt"), "w").close()
        open(os.path.join(tmpdir, ".simplegit", "ignored.txt"), "w").close()
        open(os.path.join(tmpdir, "dir1", "nested.txt"), "w").close()
        open(os.path.join(tmpdir, "dir_to_include", "included.txt"), "w").close()
        
        # List files
        files = list_files(tmpdir)
        
        # Verify correct files are listed
        assert "dir1/nested.txt" in files
        assert "dir_to_include/included.txt" in files
        assert "file1.txt" in files
        assert "file2.txt" in files
        
        # Verify ignored files are not listed
        assert ".simplegit/ignored.txt" not in files
        
        # Test with custom ignore pattern
        files_with_custom_ignore = list_files(tmpdir, ["dir_to_include"])
        assert "dir_to_include/included.txt" not in files_with_custom_ignore

if __name__ == "__main__":
    pytest.main()