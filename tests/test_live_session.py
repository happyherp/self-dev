"""Tests for live session functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from sip.config import Config
from sip.live_session import LiveSession, SessionState
from sip.models import PullRequest, CodeChange


class TestSessionState:
    """Test SessionState class."""
    
    def test_serialization(self):
        """Test state serialization and deserialization."""
        state = SessionState()
        state.current_version = 2
        state.last_meta_request = "test request"
        
        # Serialize
        data = state.to_dict()
        
        # Verify serialization
        assert data["current_version"] == 2
        assert data["last_meta_request"] == "test request"
        assert "modifications" in data
        assert "session_start_time" in data
        
        # Deserialize to new state
        new_state = SessionState()
        new_state.from_dict(data)
        
        assert new_state.current_version == 2
        assert new_state.last_meta_request == "test request"
    
    def test_serialization_with_pending_changes(self):
        """Test serialization with pending changes."""
        state = SessionState()
        
        # Add pending changes
        change = CodeChange(
            file_path="test.py",
            change_type="create",
            content="print('test')",
            description="Test change"
        )
        state.pending_changes = PullRequest(
            title="Test PR",
            body="Test body",
            branch_name="test-branch",
            changes=[change]
        )
        
        # Serialize and deserialize
        data = state.to_dict()
        new_state = SessionState()
        new_state.from_dict(data)
        
        assert new_state.pending_changes is not None
        assert new_state.pending_changes.title == "Test PR"
        assert len(new_state.pending_changes.changes) == 1
        assert new_state.pending_changes.changes[0].file_path == "test.py"


class TestLiveSession:
    """Test LiveSession class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config with all required attributes."""
        config = Mock(spec=Config)
        config.github_token = "test_token"
        config.openrouter_api_key = "test_key"
        config.model_name = "test_model"
        config.default_repository = "test/repo"
        config.max_retries = 3
        config.retry_delay = 1.0
        return config
    
    @pytest.fixture
    def session(self, mock_config):
        """Create a session with mocked dependencies."""
        with patch('sip.live_session.MetaProcessor'):
            session = LiveSession(mock_config, "test/repo")
            return session
    
    def test_save_and_restore_state(self, session):
        """Test saving and restoring session state."""
        # Modify session state
        session.state.current_version = 3
        session.state.last_meta_request = "test modification"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            # Save state
            session.save_state(temp_path)
            
            # Create new session and restore
            with patch('sip.live_session.MetaProcessor'):
                new_session = LiveSession(session.config)
            new_session.restore_state(temp_path)
            
            # Verify restoration
            assert new_session.state.current_version == 3
            assert new_session.state.last_meta_request == "test modification"
        
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_apply_changes(self, session):
        """Test applying code changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test change
            change = CodeChange(
                file_path=str(temp_path / "test.py"),
                change_type="create",
                content="print('hello world')",
                description="Create test file"
            )
            
            pr = PullRequest(
                title="Test PR",
                body="Test body",
                branch_name="test",
                changes=[change]
            )
            
            # Apply changes
            result = session.apply_changes(pr)
            
            assert result is True
            assert (temp_path / "test.py").exists()
            assert (temp_path / "test.py").read_text() == "print('hello world')"
            assert session.state.current_version == 2  # Started at 1
            assert len(session.state.modifications) == 1
    
    def test_create_backup(self, session):
        """Test creating backup."""
        # Create some test directories
        Path("src").mkdir(exist_ok=True)
        Path("tests").mkdir(exist_ok=True)
        
        try:
            backup_path = session.create_backup()
            
            assert backup_path is not None
            assert Path(backup_path).exists()
            assert session.state.backup_path == backup_path
            
            # Cleanup
            import shutil
            shutil.rmtree(backup_path)
        
        finally:
            # Cleanup test dirs
            import shutil
            shutil.rmtree("src", ignore_errors=True)
            shutil.rmtree("tests", ignore_errors=True)
    
    def test_hot_swap_success(self, session):
        """Test successful hot-swap."""
        result = session.hot_swap(timeout=1)
        assert result is True
    
    def test_rollback(self, session):
        """Test rollback functionality."""
        # Test rollback without backup
        result = session.rollback()
        assert result is False
        
        # Create backup and test rollback
        import tempfile
        backup_dir = tempfile.mkdtemp()
        session.state.backup_path = backup_dir
        
        # Create backup structure
        Path(backup_dir, "src").mkdir()
        Path(backup_dir, "tests").mkdir()
        
        # Create target directories
        Path("src").mkdir(exist_ok=True)
        Path("tests").mkdir(exist_ok=True)
        
        try:
            result = session.rollback()
            assert result is True
        
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(backup_dir, ignore_errors=True)
            shutil.rmtree("src", ignore_errors=True)
            shutil.rmtree("tests", ignore_errors=True)
    
    def test_rollback_no_backup(self, session):
        """Test rollback when no backup exists."""
        result = session.rollback()
        assert result is False
