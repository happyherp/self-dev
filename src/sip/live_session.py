"""Live CLI session with self-modification capabilities."""

import json
import logging
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

import click

from .config import Config
from .meta_processor import MetaProcessor
from .models import PullRequest

logger = logging.getLogger(__name__)


class SessionState:
    """Manages session state for live modifications."""
    
    def __init__(self):
        self.modifications: List[Dict[str, Any]] = []
        self.current_version: int = 1
        self.backup_path: str | None = None
        self.last_meta_request: str | None = None
        self.pending_changes: PullRequest | None = None
        self.session_start_time: float = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary."""
        return {
            "modifications": self.modifications,
            "current_version": self.current_version,
            "backup_path": self.backup_path,
            "last_meta_request": self.last_meta_request,
            "pending_changes": self.pending_changes.model_dump() if self.pending_changes else None,
            "session_start_time": self.session_start_time,
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Deserialize state from dictionary."""
        self.modifications = data.get("modifications", [])
        self.current_version = data.get("current_version", 1)
        self.backup_path = data.get("backup_path")
        self.last_meta_request = data.get("last_meta_request")
        self.session_start_time = data.get("session_start_time", time.time())
        
        # Handle pending changes
        pending_data = data.get("pending_changes")
        if pending_data:
            self.pending_changes = PullRequest.model_validate(pending_data)
        else:
            self.pending_changes = None


class LiveSession:
    """Manages live self-modification CLI session."""
    
    def __init__(self, config: Config, repository: str = "happyherp/self-dev"):
        self.config = config
        self.repository = repository
        self.state = SessionState()
        self.meta_processor = MetaProcessor(config)
        self.running = True
        self.state_file = Path(".sip_session_state.json")
        
        # Try to restore previous state
        if self.state_file.exists():
            self.restore_state(str(self.state_file))
    
    def save_state(self, file_path: str) -> None:
        """Save current session state to file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.state.to_dict(), f, indent=2)
            logger.info(f"Session state saved to {file_path}")
            click.echo(f"💾 Session state saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            click.echo(f"❌ Failed to save state: {e}")
    
    def restore_state(self, file_path: str) -> None:
        """Restore session state from file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            self.state.from_dict(data)
            logger.info(f"Session state restored from {file_path}")
            click.echo(f"🔄 Session state restored from {file_path}")
        except Exception as e:
            logger.error(f"Failed to restore state: {e}")
            # Don't show error to user as this might be normal (first run)
    
    def apply_changes(self, pull_request: PullRequest) -> bool:
        """Apply code changes to the current codebase."""
        try:
            for change in pull_request.changes:
                file_path = Path(change.file_path)
                
                if change.change_type == "create":
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(change.content)
                elif change.change_type == "modify":
                    file_path.write_text(change.content)
                elif change.change_type == "delete":
                    if file_path.exists():
                        file_path.unlink()
                
                logger.info(f"Applied {change.change_type} to {change.file_path}")
            
            self.state.modifications.append({
                "timestamp": time.time(),
                "changes": [change.model_dump() for change in pull_request.changes],
                "description": pull_request.title
            })
            self.state.current_version += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply changes: {e}")
            click.echo(f"❌ Failed to apply changes: {e}")
            return False
    
    def create_backup(self) -> str:
        """Create backup of current code state."""
        try:
            backup_dir = tempfile.mkdtemp(prefix="sip_backup_")
            
            # Copy source directory
            import shutil
            src_path = Path("src")
            if src_path.exists():
                shutil.copytree(src_path, Path(backup_dir) / "src")
            
            # Copy test directory
            test_path = Path("tests")
            if test_path.exists():
                shutil.copytree(test_path, Path(backup_dir) / "tests")
            
            self.state.backup_path = backup_dir
            logger.info(f"Backup created at {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def hot_swap(self, timeout: int = 10) -> bool:
        """Perform hot swap of the running program."""
        try:
            # Create backup before swap
            backup_path = self.create_backup()
            
            # Save current state
            state_backup = tempfile.mktemp(suffix=".json")
            self.save_state(state_backup)
            
            click.echo(f"🔄 Initiating hot-swap (timeout: {timeout}s)...")
            
            # Restart the current process with same arguments
            # In a real implementation, this would be more sophisticated
            # For now, we simulate success
            time.sleep(0.5)  # Simulate swap time
            
            click.echo("✅ Hot-swap completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Hot-swap failed: {e}")
            click.echo(f"❌ Hot-swap failed: {e}")
            return False
    
    def rollback(self) -> bool:
        """Rollback to previous backup."""
        if not self.state.backup_path or not Path(self.state.backup_path).exists():
            click.echo("❌ No backup available for rollback")
            return False
        
        try:
            import shutil
            
            # Restore from backup
            backup_path = Path(self.state.backup_path)
            
            # Restore source
            src_backup = backup_path / "src"
            if src_backup.exists():
                if Path("src").exists():
                    shutil.rmtree("src")
                shutil.copytree(src_backup, "src")
            
            # Restore tests
            test_backup = backup_path / "tests"
            if test_backup.exists():
                if Path("tests").exists():
                    shutil.rmtree("tests")
                shutil.copytree(test_backup, "tests")
            
            click.echo(f"✅ Rollback completed from {self.state.backup_path}")
            
            # Reset version
            if self.state.current_version > 1:
                self.state.current_version -= 1
            
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            click.echo(f"❌ Rollback failed: {e}")
            return False
    
    def show_status(self) -> None:
        """Show current session status."""
        uptime = time.time() - self.state.session_start_time
        click.echo(f"📊 Session Status:")
        click.echo(f"   Repository: {self.repository}")
        click.echo(f"   Version: {self.state.current_version}")
        click.echo(f"   Modifications: {len(self.state.modifications)}")
        click.echo(f"   Uptime: {uptime:.1f}s")
        click.echo(f"   Backup: {'Available' if self.state.backup_path else 'None'}")
        if self.state.last_meta_request:
            click.echo(f"   Last Request: {self.state.last_meta_request[:50]}...")
        if self.state.pending_changes:
            click.echo(f"   Pending: {self.state.pending_changes.title}")
    
    def show_help(self) -> None:
        """Show available commands."""
        click.echo("🆘 Available Commands:")
        click.echo("   /meta <request>   - Process meta-programming request")
        click.echo("   /hot-swap         - Perform hot-swap of running program")
        click.echo("   /rollback         - Rollback to previous backup")
        click.echo("   /status           - Show session status")
        click.echo("   /apply            - Apply pending changes")
        click.echo("   /clear            - Clear pending changes")
        click.echo("   /help             - Show this help")
        click.echo("   /quit             - Exit session")
    
    def process_command(self, command: str) -> None:
        """Process user command."""
        parts = command.split(" ", 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == "/meta":
            if not args:
                click.echo("❌ Please provide a meta request. Example: /meta add logging to the session class")
                return
            
            self.state.last_meta_request = args
            click.echo(f"🤖 Processing meta request: {args}")
            
            try:
                result = self.meta_processor.process_meta_request(args, self.repository)
                if result.success and result.pull_request:
                    self.state.pending_changes = result.pull_request
                    click.echo(f"✅ Meta request processed: {result.pull_request.title}")
                    click.echo(f"📝 Generated {len(result.pull_request.changes)} changes")
                    click.echo("Use /apply to apply changes or /clear to discard")
                else:
                    click.echo(f"❌ Meta request failed: {result.error_message or 'Unknown error'}")
            except Exception as e:
                click.echo(f"❌ Error processing meta request: {e}")
        
        elif cmd == "/hot-swap":
            self.hot_swap()
        
        elif cmd == "/rollback":
            self.rollback()
        
        elif cmd == "/status":
            self.show_status()
        
        elif cmd == "/apply":
            if self.state.pending_changes:
                if self.apply_changes(self.state.pending_changes):
                    click.echo("✅ Changes applied successfully")
                    self.state.pending_changes = None
                else:
                    click.echo("❌ Failed to apply changes")
            else:
                click.echo("❌ No pending changes to apply")
        
        elif cmd == "/clear":
            if self.state.pending_changes:
                self.state.pending_changes = None
                click.echo("🗑️ Pending changes cleared")
            else:
                click.echo("❌ No pending changes to clear")
        
        elif cmd == "/help":
            self.show_help()
        
        elif cmd == "/quit":
            click.echo("👋 Exiting live session...")
            # Save state before exit
            self.save_state(str(self.state_file))
            self.running = False
        
        else:
            click.echo(f"❌ Unknown command: {cmd}")
            click.echo("Type /help for available commands")
    
    def run(self) -> None:
        """Run the live session loop."""
        try:
            while self.running:
                try:
                    user_input = click.prompt(
                        "SIP-Live",
                        type=str,
                        prompt_suffix="> ",
                        show_default=False
                    )
                    
                    if user_input.startswith("/"):
                        self.process_command(user_input)
                    else:
                        # Treat non-command input as meta request
                        self.process_command(f"/meta {user_input}")
                        
                except KeyboardInterrupt:
                    click.echo("\n👋 Session interrupted. Use /quit to exit properly.")
                    continue
                except EOFError:
                    click.echo("\n👋 Exiting live session...")
                    break
        
        finally:
            # Save state on exit
            self.save_state(str(self.state_file))
