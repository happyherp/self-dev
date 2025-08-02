"""Main issue processor orchestrator."""

import logging

from .config import Config
from .github_client import GitHubClient
from .llm_client import LLMClient
from .models import ProcessingResult


class IssueProcessor:
    """Main orchestrator for processing GitHub issues."""

    def __init__(self, config: Config):
        self.config = config
        self.github = GitHubClient(config)
        self.llm = LLMClient(config)
        self.logger = logging.getLogger(__name__)

    def process_issue(self, repo: str, issue_number: int) -> ProcessingResult:
        """Process a GitHub issue end-to-end."""
        try:
            self.logger.info(f"Processing issue #{issue_number} in {repo}")

            # 1. Fetch the issue
            issue = self.github.get_issue(repo, issue_number)
            self.logger.info(f"Fetched issue: {issue.title}")

            # 2. Get repository context
            repository_context = self._get_repository_context(repo)

            # 3. Analyze the issue with AI
            self.logger.info("Analyzing issue with AI...")
            analysis = self.llm.analyze_issue(issue, repository_context)
            self.logger.info(f"Analysis complete. Confidence: {analysis.confidence}")

            # 4. Skip if confidence is too low
            if analysis.confidence < 0.3:
                self.logger.warning(f"Low confidence ({analysis.confidence}), skipping automated solution")
                return ProcessingResult(
                    issue=issue,
                    analysis=analysis,
                    pull_request=None,
                    success=False,
                    error_message=f"Confidence too low: {analysis.confidence}",
                )

            # 5. Get relevant file contents
            file_contents = self._get_relevant_files(repo, analysis.files_to_modify)

            # 6. Generate solution
            self.logger.info("Generating solution...")
            pull_request = self.llm.generate_solution(issue, analysis, file_contents)

            # 7. Create branch and commit changes
            if pull_request.changes:
                self.logger.info(f"Creating branch: {pull_request.branch_name}")
                self.github.create_branch(repo, pull_request.branch_name)

                commit_message = f"SIP: {pull_request.title}\n\nAddresses issue #{issue_number}"
                self.github.commit_changes(repo, pull_request.branch_name, pull_request.changes, commit_message)

                # 8. Create pull request
                self.logger.info("Creating pull request...")
                pr_url = self.github.create_pull_request(repo, pull_request)
                self.logger.info(f"Pull request created: {pr_url}")

                return ProcessingResult(issue=issue, analysis=analysis, pull_request=pull_request, success=True)
            else:
                return ProcessingResult(
                    issue=issue,
                    analysis=analysis,
                    pull_request=pull_request,
                    success=False,
                    error_message="No changes generated",
                )

        except Exception as e:
            self.logger.error(f"Error processing issue #{issue_number}: {str(e)}", exc_info=True)
            return ProcessingResult(
                issue=issue if "issue" in locals() else None,
                analysis=analysis if "analysis" in locals() else None,
                pull_request=None,
                success=False,
                error_message=str(e),
            )

    def _get_repository_context(self, repo: str) -> str:
        """Get context about the repository structure and purpose."""
        try:
            # Get key files for context
            context_files = ["README.md", "PROJECT.md", "pyproject.toml", "requirements.txt"]
            context = f"Repository: {repo}\n\n"

            for file_path in context_files:
                try:
                    content = self.github.get_file_content(repo, file_path)
                    if content:
                        context += f"--- {file_path} ---\n{content[:1000]}...\n\n"
                except Exception:
                    continue

            # Get directory structure
            try:
                files = self.github.list_repository_files(repo)
                # Filter to important files only
                important_extensions = [".py", ".md", ".yml", ".yaml", ".toml", ".txt"]
                important_files = [f for f in files if any(f.endswith(ext) for ext in important_extensions)]
                context += "--- File Structure ---\n"
                context += "\n".join(important_files[:50])  # Limit to first 50 files
            except Exception:
                pass

            return context

        except Exception as e:
            self.logger.warning(f"Could not get repository context: {str(e)}")
            return f"Repository: {repo}\nContext unavailable due to error: {str(e)}"

    def _get_relevant_files(self, repo: str, file_paths: list[str]) -> dict[str, str]:
        """Get content of relevant files for the issue."""
        file_contents = {}

        for file_path in file_paths:
            try:
                content = self.github.get_file_content(repo, file_path)
                if content and len(content) <= self.config.max_file_size:
                    file_contents[file_path] = content
                elif len(content) > self.config.max_file_size:
                    # Truncate large files
                    file_contents[file_path] = content[: self.config.max_file_size] + "\n... (truncated)"
                    self.logger.warning(f"File {file_path} truncated due to size")
            except Exception as e:
                self.logger.warning(f"Could not get content for {file_path}: {str(e)}")
                file_contents[file_path] = f"# Error reading file: {str(e)}"

        return file_contents
