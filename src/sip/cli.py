"""Console script for SIP."""

import logging
import sys

import click

from .config import Config
from .issue_processor import IssueProcessor
from .llm_client import LLMClient
from .local_file_processor import LocalFileProcessor


@click.group()
def main() -> None:
    """SIP - Self-Improving Program."""
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@main.command()
@click.argument("issue_number", type=int)
@click.option("--repo", help="Repository in format owner/repo (defaults to happyherp/self-dev)")
@click.option("--branch", help="Branch to analyze and create PR from (defaults to current git branch)")
def process_issue(issue_number: int, repo: str | None = None, branch: str | None = None) -> None:
    """Process a GitHub issue with AI."""
    try:
        # Load configuration
        config = Config.from_env()

        # Use provided repo or default
        target_repo = repo or config.default_repository

        # Default to current git branch if no branch specified
        if not branch:
            import subprocess

            try:
                git_result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
                )
                target_branch = git_result.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                target_branch = "main"  # Fallback if git command fails
        else:
            target_branch = branch

        click.echo(f"🤖 SIP: Processing issue #{issue_number} in {target_repo}")
        click.echo(f"🌿 Analyzing branch: {target_branch}")

        # Process the issue
        processor = IssueProcessor(config)
        processing_result = processor.process_issue(target_repo, issue_number, target_branch)

        if processing_result.success:
            click.echo(f"✅ Successfully processed issue #{issue_number}")
            if processing_result.pull_request:
                click.echo(f"📝 Created pull request: {processing_result.pull_request.title}")
                click.echo(f"🌿 Branch: {processing_result.pull_request.branch_name}")
        else:
            click.echo(f"❌ Failed to process issue #{issue_number}")
            if processing_result.error_message:
                click.echo(f"Error: {processing_result.error_message}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"💥 Fatal error: {str(e)}")
        logging.exception("Fatal error in process_issue")
        sys.exit(1)


@main.command()
@click.argument("goal_file", type=click.Path(exists=True))
@click.argument("repo_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--apply", is_flag=True, help="Apply changes to local files (default: just show changes)")
def process_local(goal_file: str, repo_dir: str, apply: bool = False) -> None:
    """Process a local goal file against a local repository."""
    try:
        # Load configuration (only need LLM config for local processing)
        config = Config.from_env()

        click.echo(f"🤖 SIP: Processing local goal from {goal_file}")
        click.echo(f"📁 Repository: {repo_dir}")

        # Create LLM client and local processor
        llm_client = LLMClient(config)
        processor = LocalFileProcessor(llm_client)

        # Process the goal
        changeset = processor.process_goal_file(goal_file, repo_dir)

        click.echo(f"✅ Generated changeset: {changeset.summary}")
        click.echo(f"📝 Description: {changeset.description}")
        click.echo(f"📄 Files to change: {len(changeset.files)}")

        for file_change in changeset.files:
            click.echo(f"  - {file_change.path}")

        if apply:
            processor.apply_changeset_locally(repo_dir, changeset)
            click.echo("✅ Changes applied to local files!")
        else:
            click.echo("💡 Use --apply to apply changes to local files")

    except Exception as e:
        click.echo(f"💥 Fatal error: {str(e)}")
        logging.exception("Fatal error in process_local")
        sys.exit(1)


if __name__ == "__main__":
    main()
