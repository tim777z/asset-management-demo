import json
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


class TestCLIValidation:
    """Argparse-level validation of untrusted command-line input."""

    def _portfolio_file(self, tmp_path):
        csv_file = tmp_path / "portfolio.csv"
        csv_file.write_text(
            "symbol,shares,avg_cost,current_price,asset_class\nAAPL,100,150,175,equity\n"
        )
        return csv_file

    @pytest.mark.parametrize(
        "flag,value",
        [
            ("--shares", "-5"),
            ("--cost", "-1"),
            ("--price", "-10"),
            ("--shares", "nan"),
            ("--cost", "inf"),
        ],
    )
    def test_add_rejects_invalid_numbers(self, tmp_path, flag, value):
        csv_file = self._portfolio_file(tmp_path)
        sys.argv = [
            "asset-manager",
            "add",
            str(csv_file),
            "GOOGL",
            "--shares",
            "1",
            "--cost",
            "1",
            flag,
            value,
        ]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0

    def test_add_rejects_invalid_symbol(self, tmp_path):
        csv_file = self._portfolio_file(tmp_path)
        sys.argv = [
            "asset-manager",
            "add",
            str(csv_file),
            "=SUM(A1)",
            "--shares",
            "1",
            "--cost",
            "1",
        ]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0

    @pytest.mark.parametrize(
        "asset_class",
        ['=HYPERLINK("http://evil","click")', "@SUM(A1)", "a\nb", "a\x00b", "a\u2028b"],
    )
    def test_add_rejects_unsafe_asset_class(self, tmp_path, asset_class):
        csv_file = self._portfolio_file(tmp_path)
        sys.argv = [
            "asset-manager",
            "add",
            str(csv_file),
            "GOOGL",
            "--shares",
            "1",
            "--cost",
            "1",
            "--class",
            asset_class,
        ]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0

    def test_add_normalises_empty_asset_class(self, tmp_path, capsys):
        csv_file = self._portfolio_file(tmp_path)
        sys.argv = [
            "asset-manager",
            "add",
            str(csv_file),
            "GOOGL",
            "--shares",
            "1",
            "--cost",
            "1",
            "--class",
            "   ",
        ]
        main()
        assert "Added GOOGL" in capsys.readouterr().out


class TestCLILogging:
    def test_verbose_emits_debug_output(self, tmp_path, capsys):
        csv_file = tmp_path / "portfolio.csv"
        csv_file.write_text(
            "symbol,shares,avg_cost,current_price,asset_class\nAAPL,100,150,175,equity\n"
        )
        sys.argv = ["asset-manager", "--verbose", "report", str(csv_file)]
        main()
        captured = capsys.readouterr()
        assert "DEBUG" in captured.err
        assert "Loaded portfolio" in captured.err

    def test_quiet_still_reports_errors(self, tmp_path, capsys):
        sys.argv = ["asset-manager", "--quiet", "report", "nonexistent.csv"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "Error loading portfolio" in captured.err

    def test_log_level_env_var(self, tmp_path, capsys, monkeypatch):
        """LOG_LEVEL env var is respected when neither --verbose nor --quiet is passed."""
        csv_file = tmp_path / "portfolio.csv"
        csv_file.write_text(
            "symbol,shares,avg_cost,current_price,asset_class\nAAPL,100,150,175,equity\n"
        )
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        sys.argv = ["asset-manager", "report", str(csv_file)]
        main()
        captured = capsys.readouterr()
        assert "DEBUG" in captured.err
        assert "Loaded portfolio" in captured.err


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


class TestCLILoggingJson:
    """Structured (JSON) logging contract for the CLI."""

    def _portfolio_file(self, tmp_path):
        csv_file = tmp_path / "portfolio.csv"
        csv_file.write_text(
            "symbol,shares,avg_cost,current_price,asset_class\nAAPL,100,150,175,equity\n"
        )
        return csv_file

    def test_verbose_log_records_are_valid_json(self, tmp_path, capsys):
        csv_file = self._portfolio_file(tmp_path)
        sys.argv = ["asset-manager", "--verbose", "report", str(csv_file)]
        main()
        captured = capsys.readouterr()
        records = []
        for line in captured.err.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:  # pragma: no cover - failure path
                pytest.fail(f"non-JSON log line: {line!r} ({exc})")
        assert records, "expected at least one structured log record under --verbose"
        for record in records:
            assert "level" in record
            assert "message" in record
        assert any(
            record.get("level") == "DEBUG" and "Loaded portfolio" in str(record.get("message", ""))
            for record in records
        )

    def test_quiet_error_record_is_valid_json(self, tmp_path, capsys):
        sys.argv = ["asset-manager", "--quiet", "report", "nonexistent.csv"]
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        records = [json.loads(line) for line in captured.err.splitlines() if line.strip()]
        assert records, "expected an error record under --quiet"
        assert any(
            record.get("level") in {"ERROR", "CRITICAL"}
            and "Error loading portfolio" in str(record.get("message", ""))
            for record in records
        )

    def test_unexpected_exception_is_structured_and_exits_nonzero(self, monkeypatch, capsys):
        def boom(*args, **kwargs):
            raise RuntimeError("internal detail")

        monkeypatch.setattr("asset_manager.cli.Portfolio.from_csv", boom)
        sys.argv = ["asset-manager", "report", "anything.csv"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == "", "unexpected errors must not be printed to stdout"
        records = [json.loads(line) for line in captured.err.splitlines() if line.strip()]
        assert any(
            record.get("level") == "ERROR"
            and "Unexpected error in asset-manager" in str(record.get("message", ""))
            and "RuntimeError: internal detail" in str(record.get("exception", ""))
            for record in records
        )


class TestCLIHistory:
    """Risk metrics computed from a validated date,value history CSV."""

    def _history_file(self, tmp_path, content=None, encoding="utf-8"):
        csv_file = tmp_path / "history.csv"
        csv_file.write_text(
            content
            if content is not None
            else "date,value\n2026-01-01,100\n2026-01-02,110\n2026-01-03,99\n",
            encoding=encoding,
        )
        return csv_file

    def test_history_metrics(self, tmp_path, capsys):
        csv_file = self._history_file(tmp_path)
        sys.argv = ["asset-manager", "history", str(csv_file)]
        main()
        captured = capsys.readouterr()
        assert "Observations: 3" in captured.out
        assert "Mean daily return:" in captured.out
        assert "Sharpe ratio:" in captured.out
        assert "Sortino ratio:" in captured.out
        assert "Volatility (annualized):" in captured.out
        assert "Max drawdown:" in captured.out
        assert "Value at Risk (95%):" in captured.out

    def test_history_tolerates_bom(self, tmp_path, capsys):
        csv_file = self._history_file(
            tmp_path, "date,value\n2026-01-01,100\n2026-01-02,105\n", encoding="utf-8-sig"
        )
        sys.argv = ["asset-manager", "history", str(csv_file)]
        main()
        captured = capsys.readouterr()
        assert "Observations: 2" in captured.out

    def test_history_help_lists_subcommand(self, capsys):
        sys.argv = ["asset-manager", "--help"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        assert "history" in capsys.readouterr().out

    @pytest.mark.parametrize(
        "content,expected_error",
        [
            ("date\n2026-01-01\n", "missing required columns"),
            ("date,value\nnot-a-date,100\n", "invalid isoformat"),
            ("date,value\n2026-01-01,nan\n", "not finite"),
            ("date,value\n2026-01-01,-100\n", "cannot be negative"),
            ("date,value\n", "no valid history rows"),
            ("", "empty or has no header"),
        ],
    )
    def test_history_rejects_invalid_input(self, tmp_path, capsys, content, expected_error):
        csv_file = self._history_file(tmp_path, content)
        sys.argv = ["asset-manager", "history", str(csv_file)]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert expected_error in captured.err.lower()
        assert "Error loading history" in captured.err

    def test_history_missing_file(self, capsys):
        sys.argv = ["asset-manager", "history", "missing-history.csv"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0
        assert "not found" in capsys.readouterr().err.lower()

    def test_history_enforces_row_cap(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setattr("asset_manager.cli.MAX_CSV_ROWS", 1)
        csv_file = self._history_file(tmp_path)
        sys.argv = ["asset-manager", "history", str(csv_file)]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0
        assert "maximum" in capsys.readouterr().err.lower()

    def test_history_error_is_structured_json(self, tmp_path, capsys):
        csv_file = self._history_file(tmp_path, "date,value\n")
        sys.argv = ["asset-manager", "history", str(csv_file)]
        with pytest.raises(SystemExit):
            main()
        lines = [line for line in capsys.readouterr().err.splitlines() if line.strip()]
        records = [json.loads(line) for line in lines]
        assert any(record.get("level") == "ERROR" for record in records)
