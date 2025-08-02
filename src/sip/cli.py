"""Console script for SIP."""

import click


@click.group()
def main() -> None:
    """SIP - Self-Improving Program."""
    pass


@main.command()
@click.argument("issue_number", type=int)
@click.option("--repo", help="Repository in format owner/repo (defaults to happyherp/self-dev)")
def process_issue(issue_number: int, repo: str | None = None) -> None:
    """Process a GitHub issue with AI."""
    click.echo(f"Processing issue #{issue_number}")
    if repo:
        click.echo(f"Repository: {repo}")
    # Implementation will be added later
    click.echo("🚧 Implementation coming soon...")


if __name__ == "__main__":
    main()
