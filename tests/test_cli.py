from __future__ import annotations

from financed_emissions.cli import main


def test_cli_prints_report_for_sample(capsys) -> None:
    assert main(["data/sample_portfolio.csv"]) == 0
    out = capsys.readouterr().out
    assert "Financed emissions" in out
    assert "tCO2e" in out


def test_cli_json_flag(capsys) -> None:
    assert main(["data/sample_portfolio.csv", "--json"]) == 0
    out = capsys.readouterr().out
    assert '"total_financed_emissions_tco2e"' in out


def test_cli_missing_file_returns_error(capsys) -> None:
    assert main(["/tmp/missing-portfolio.csv"]) == 1
    err = capsys.readouterr().err
    assert "error:" in err
