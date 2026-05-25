"""Tests for the agentwork CLI."""

import sys
from io import StringIO
from unittest.mock import patch

import pytest

from agentwork.cli import main


class TestCLIParsing:
    """Test argparse parsing for CLI subcommands."""

    def test_no_command_prints_help(self, capsys):
        """With no args, prints help without error."""
        main([])
        captured = capsys.readouterr()
        assert "agentwork" in captured.out or "usage" in captured.out.lower()

    def test_list_companies_command(self, capsys):
        """list-companies prints available company types."""
        main(["list-companies"])
        captured = capsys.readouterr()
        assert "data_solutions" in captured.out
        assert "product_sales" in captured.out
        assert "marketing_agency" in captured.out
        assert "digital_agency" in captured.out
        assert "entertainment" in captured.out

    def test_list_companies_sorted(self, capsys):
        """list-companies output is sorted."""
        main(["list-companies"])
        captured = capsys.readouterr()
        lines = [l.strip() for l in captured.out.strip().split("\n") if l.strip()]
        assert lines == sorted(lines)

    def test_list_tools_valid_company(self, capsys):
        """list-tools with a valid company type prints tool names."""
        main(["list-tools", "data_solutions"])
        captured = capsys.readouterr()
        # Should have at least one tool printed
        assert captured.out.strip() != ""
        lines = [l.strip() for l in captured.out.strip().split("\n") if l.strip()]
        assert len(lines) >= 1

    def test_list_tools_invalid_company(self):
        """list-tools with invalid company type exits with error."""
        with pytest.raises(SystemExit) as exc_info:
            main(["list-tools", "nonexistent_company"])
        assert exc_info.value.code == 1

    def test_run_command_valid_company(self, capsys):
        """run command with valid company type produces output."""
        main(["run", "data_solutions", "analyze some data"])
        captured = capsys.readouterr()
        assert "Task ID:" in captured.out
        assert "Status:" in captured.out

    def test_run_command_invalid_company(self):
        """run command with invalid company type exits with error."""
        with pytest.raises(SystemExit) as exc_info:
            main(["run", "nonexistent_company", "do something"])
        assert exc_info.value.code == 1

    def test_serve_invalid_company(self):
        """serve command with invalid company type exits with error."""
        with pytest.raises(SystemExit) as exc_info:
            main(["serve", "nonexistent_company"])
        assert exc_info.value.code == 1

    def test_list_tools_output_sorted(self, capsys):
        """list-tools output is sorted."""
        main(["list-tools", "product_sales"])
        captured = capsys.readouterr()
        lines = [l.strip() for l in captured.out.strip().split("\n") if l.strip()]
        assert lines == sorted(lines)
