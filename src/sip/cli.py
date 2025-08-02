"""Console script for SIP."""

import logging
import sys

import click

from .config import Config
from .issue_processor import IssueProcessor


@click.group()
def main() -> None:
    """SIP - Self-Improving Program."""
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@main.command()
@click.argument("issue_number", type=int)
@click.option("--repo", help="Repository in format owner/repo (defaults to happyherp/self-dev)")
def process_issue(issue_number: int, repo: str | None = None) -> None:
    """Process a GitHub issue with AI."""
    try:
        # Load configuration
        config = Config.from_env()

        # Use provided repo or default
        target_repo = repo or config.default_repository

        click.echo(f"🤖 SIP: Processing issue #{issue_number} in {target_repo}")

        # Process the issue
        processor = IssueProcessor(config)
        result = processor.process_issue(target_repo, issue_number)

        if result.success:
            click.echo(f"✅ Successfully processed issue #{issue_number}")
            if result.pull_request:
                click.echo(f"📝 Created pull request: {result.pull_request.title}")
                click.echo(f"🌿 Branch: {result.pull_request.branch_name}")
        else:
            click.echo(f"❌ Failed to process issue #{issue_number}")
            if result.error_message:
                click.echo(f"Error: {result.error_message}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"💥 Fatal error: {str(e)}")
        logging.exception("Fatal error in process_issue")
        sys.exit(1)


if __name__ == "__main__":
    main()
