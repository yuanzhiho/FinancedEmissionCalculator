#!/usr/bin/env python3
"""Run the sample Hong Kong-style book and print a portfolio report."""

from pathlib import Path

from financed_emissions.calculator import FinancedEmissionsCalculator
from financed_emissions.io import load_portfolio_csv
from financed_emissions.reporting import format_report

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "sample_portfolio.csv"


def main() -> None:
    positions = load_portfolio_csv(CSV_PATH)
    result = FinancedEmissionsCalculator(scopes=(1, 2)).calculate_portfolio(positions)
    print(format_report(result))


if __name__ == "__main__":
    main()
