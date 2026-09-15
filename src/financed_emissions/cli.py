from __future__ import annotations

import argparse
import sys
from pathlib import Path

from financed_emissions.calculator import FinancedEmissionsCalculator
from financed_emissions.io import load_portfolio_csv
from financed_emissions.reporting import dumps_json, format_report


def _parse_scopes(raw: str) -> tuple[int, ...]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("scopes cannot be empty")
    try:
        scopes = tuple(int(p) for p in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("scopes must be integers, e.g. 1,2 or 1,2,3") from exc
    return scopes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="financed-emissions",
        description="Calculate PCAF-style financed emissions for a loan/investment book.",
    )
    parser.add_argument(
        "portfolio",
        nargs="?",
        default=str(Path("data") / "sample_portfolio.csv"),
        help="CSV of positions (default: data/sample_portfolio.csv)",
    )
    parser.add_argument(
        "--scopes",
        default="1,2",
        type=_parse_scopes,
        help="GHG scopes to include, comma-separated (default: 1,2)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="write machine-readable JSON instead of a text report",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        positions = load_portfolio_csv(args.portfolio)
        result = FinancedEmissionsCalculator(scopes=args.scopes).calculate_portfolio(positions)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = dumps_json(result) if args.json else format_report(result)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
