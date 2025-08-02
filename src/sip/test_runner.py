"""Test runner for SIP."""

import subprocess
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class SipTestResult:
    """Result of running tests."""

    success: bool
    output: str
    error_output: str
    return_code: int


class SipTestRunner:
    """Runs tests and captures output."""

    def __init__(self, test_command: list[str] | None = None) -> None:
        """Initialize test runner.
        
        Args:
            test_command: Command to run tests. Defaults to pytest.
        """
        self.test_command = test_command or ["python", "-m", "pytest", "-v"]

    def run_tests(self, cwd: str | None = None) -> SipTestResult:
        """Run tests and return results.
        
        Args:
            cwd: Working directory to run tests in.
            
        Returns:
            TestResult with success status and output.
        """
        try:
            result = subprocess.run(
                self.test_command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            
            return SipTestResult(
                success=result.returncode == 0,
                output=result.stdout,
                error_output=result.stderr,
                return_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return SipTestResult(
                success=False,
                output="",
                error_output="Tests timed out after 5 minutes",
                return_code=-1,
            )
        except Exception as e:
            return SipTestResult(
                success=False,
                output="",
                error_output=f"Failed to run tests: {e}",
                return_code=-1,
            )

    def format_test_failure(self, test_result: SipTestResult) -> str:
        """Format test failure for AI feedback.
        
        Args:
            test_result: Failed test result.
            
        Returns:
            Formatted error message for AI.
        """
        return f"""
TESTS FAILED (return code: {test_result.return_code})

STDOUT:
{test_result.output}

STDERR:
{test_result.error_output}

Please analyze the test failures and fix the code. The tests must pass before the changes can be committed.
""".strip()