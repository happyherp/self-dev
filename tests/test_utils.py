import pytest
from src.sip.utils import validate_repo_name


class TestValidateRepoName:
    """Test cases for the validate_repo_name function."""
    
    def test_valid_repo_names(self):
        """Test that valid repo names return True."""
        valid_names = [
            "happyherp/self-dev",
            "owner/repo",
            "user123/my-project",
            "org/repo-name",
            "github/docs",
            "a/b",  # Minimal valid case
            "user/repo123",
            "123user/456repo",
            "owner-name/repo-name",
            "owner_name/repo_name",
            "owner.name/repo.name"
        ]
        
        for repo_name in valid_names:
            assert validate_repo_name(repo_name) is True, f"Expected {repo_name} to be valid"
    
    def test_invalid_no_slash(self):
        """Test that repo names without slash return False."""
        invalid_names = [
            "invalid",
            "justarepo",
            "owner-repo",
            "owner_repo",
            "owner.repo"
        ]
        
        for repo_name in invalid_names:
            assert validate_repo_name(repo_name) is False, f"Expected {repo_name} to be invalid"
    
    def test_invalid_multiple_slashes(self):
        """Test that repo names with multiple slashes return False."""
        invalid_names = [
            "owner/repo/extra",
            "owner/repo/sub/path",
            "//repo",
            "owner//repo",
            "owner/repo/",
            "/owner/repo"
        ]
        
        for repo_name in invalid_names:
            assert validate_repo_name(repo_name) is False, f"Expected {repo_name} to be invalid"
    
    def test_invalid_empty_parts(self):
        """Test that repo names with empty owner or repo parts return False."""
        invalid_names = [
            "/repo",    # Empty owner
            "owner/",   # Empty repo
            "/",        # Both empty
            "//",       # Multiple slashes with empty parts
        ]
        
        for repo_name in invalid_names:
            assert validate_repo_name(repo_name) is False, f"Expected {repo_name} to be invalid"
    
    def test_invalid_with_spaces(self):
        """Test that repo names with spaces return False."""
        invalid_names = [
            "owner with spaces/repo",
            "owner/repo with spaces",
            "owner with spaces/repo with spaces",
            " owner/repo",
            "owner/repo ",
            " owner/repo ",
            "owner /repo",
            "owner/ repo"
        ]
        
        for repo_name in invalid_names:
            assert validate_repo_name(repo_name) is False, f"Expected {repo_name} to be invalid"
    
    def test_edge_cases(self):
        """Test edge cases and unexpected inputs."""
        # Empty string
        assert validate_repo_name("") is False
        
        # Only slash
        assert validate_repo_name("/") is False
        
        # Only slashes
        assert validate_repo_name("//") is False
        assert validate_repo_name("///") is False
    
    def test_type_safety(self):
        """Test that non-string inputs return False."""
        invalid_inputs = [
            None,
            123,
            [],
            {},
            True,
            False
        ]
        
        for invalid_input in invalid_inputs:
            assert validate_repo_name(invalid_input) is False, f"Expected {invalid_input} to be invalid"
    
    def test_acceptance_criteria_examples(self):
        """Test the specific examples from the acceptance criteria."""
        # Valid example
        assert validate_repo_name("happyherp/self-dev") is True
        
        # Invalid examples
        assert validate_repo_name("invalid") is False
        assert validate_repo_name("owner/") is False
        assert validate_repo_name("/repo") is False
        assert validate_repo_name("owner with spaces/repo") is False