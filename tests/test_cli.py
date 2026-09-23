import subprocess
import sys

import pytest

from asset_manager.cli import main


class TestCLICreate:
    def test_create_portfolio(self, capsys):
        sys.argv = ["asset-manager", "create", "TestPortfolio"]
        main()
        captured = capsys.readouterr()
        assert "Created portfolio: TestPortfolio" in captured.out

    def test_create_portfolio_with_spaces(self, capsys):
        sys.argv = ["asset-manager", "create", "My Portfolio"]
        main()
        captured = capsys.readouterr()
        assert "Created portfolio: My Portfolio" in captured.out


class TestCLIAdd:
    def test_add_asset_to_csv(self, tmp_path, capsys):
        # Create a CSV portfolio file
        csv_file = tmp_path / "portfolio.csv"
        csv_file.write_text(
            "symbol,shares,avg_cost,current_price,asset_class\nAAPL,100,150,175,equity\n"
        )

        sys.argv = [
            "asset-manager",
            "add",
            str(csv_file),
            "GOOGL",
            "--shares",
            "50",
            "--cost",
            "2800",
            "--price",
            "2900",
            "--class",
            "equity",
        ]
        main()
        captured = capsys.readouterr()
        assert "Added GOOGL to Portfolio" in captured.out

        # Verify the asset was added by reading the CSV
        # Note: The current CLI doesn't save back to CSV, it just prints
        # This test verifies the command runs without error

    def test_add_asset_missing_required_args(self, tmp_path, capsys):
        csv_file = tmp_path / "portfolio.csv"
        csv_file.write_text(
            "symbol,shares,avg_cost,current_price,asset_class\nAAPL,100,150,175,equity\n"
        )

        sys.argv = [
            "asset-manager",
            "add",
            str(csv_file),
            "GOOGL",
            # Missing --shares and --cost
        ]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0


class TestCLIReport:
    def test_report_portfolio(self, tmp_path, capsys):
        csv_file = tmp_path / "portfolio.csv"
        csv_file.write_text(
            "symbol,shares,avg_cost,current_price,asset_class\nAAPL,100,150,175,equity\nGOOGL,50,2800,2900,equity\n"
        )

        sys.argv = ["asset-manager", "report", str(csv_file)]
        main()
        captured = capsys.readouterr()
        assert "Portfolio: Portfolio" in captured.out
        assert "Total Value:" in captured.out
        assert "AAPL" in captured.out
        assert "GOOGL" in captured.out
        assert "Asset Allocation:" in captured.out

    def test_report_nonexistent_file(self, capsys):
        sys.argv = ["asset-manager", "report", "nonexistent.csv"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        # The current implementation will raise FileNotFoundError which becomes SystemExit
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "Error loading portfolio" in captured.err
        assert "not found" in captured.err.lower()

    def test_report_malformed_csv(self, tmp_path, capsys):
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text("symbol,shares\nAAPL,100\n")  # missing avg_cost
        sys.argv = ["asset-manager", "report", str(csv_file)]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "Error loading portfolio" in captured.err
        assert "avg_cost" in captured.err

    def test_add_malformed_csv(self, tmp_path, capsys):
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text("symbol,shares\nAAPL,100\n")  # missing avg_cost
        sys.argv = [
            "asset-manager",
            "add",
            str(csv_file),
            "GOOGL",
            "--shares",
            "50",
            "--cost",
            "2800",
        ]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "Error loading portfolio" in captured.err
        assert "avg_cost" in captured.err


class TestCLIHelp:
    def test_help_no_args(self, capsys):
        sys.argv = ["asset-manager"]
        main()
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()
        assert "create" in captured.out
        assert "add" in captured.out
        assert "report" in captured.out

    def test_help_create(self, capsys):
        sys.argv = ["asset-manager", "create", "--help"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "portfolio name" in captured.out.lower()

    def test_help_add(self, capsys):
        sys.argv = ["asset-manager", "add", "--help"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "shares" in captured.out
        assert "cost" in captured.out

    def test_help_report(self, capsys):
        sys.argv = ["asset-manager", "report", "--help"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "portfolio file" in captured.out.lower()


class TestCLIIntegration:
    def test_full_workflow_create_add_report(self, tmp_path, capsys):
        csv_file = tmp_path / "workflow.csv"

        # Create portfolio (just prints, doesn't create file)
        sys.argv = ["asset-manager", "create", "WorkflowTest"]
        main()
        captured = capsys.readouterr()
        assert "Created portfolio: WorkflowTest" in captured.out

        # Create initial CSV manually (since create doesn't write file)
        csv_file.write_text(
            "symbol,shares,avg_cost,current_price,asset_class\nAAPL,100,150,175,equity\n"
        )

        # Add asset
        sys.argv = [
            "asset-manager",
            "add",
            str(csv_file),
            "MSFT",
            "--shares",
            "75",
            "--cost",
            "300",
            "--price",
            "320",
            "--class",
            "equity",
        ]
        main()
        captured = capsys.readouterr()
        assert "Added MSFT to Portfolio" in captured.out

        # Report - note: add doesn't persist to CSV in current impl, so only AAPL shows
        sys.argv = ["asset-manager", "report", str(csv_file)]
        main()
        captured = capsys.readouterr()
        assert "AAPL" in captured.out
        # MSFT is not in CSV since add doesn't persist, so we don't assert it

    def test_invalid_command(self, capsys):
        sys.argv = ["asset-manager", "invalid_command"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "usage:" in captured.err.lower()
        assert "invalid choice" in captured.err.lower()


class TestCLISubprocess:
    """Test CLI via subprocess to verify entry point works."""

    def test_subprocess_create(self):
        result = subprocess.run(
            [sys.executable, "-m", "asset_manager.cli", "create", "SubprocessTest"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Created portfolio: SubprocessTest" in result.stdout

    def test_subprocess_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "asset_manager.cli", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Asset Management Toolkit" in result.stdout

    def test_subprocess_report(self, tmp_path):
        csv_file = tmp_path / "subprocess.csv"
        csv_file.write_text(
            "symbol,shares,avg_cost,current_price,asset_class\nTSLA,10,200,250,equity\n"
        )

        result = subprocess.run(
            [sys.executable, "-m", "asset_manager.cli", "report", str(csv_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "TSLA" in result.stdout
        assert "Total Value:" in result.stdout
