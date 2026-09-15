from __future__ import annotations

from pathlib import Path

import pytest

from financed_emissions.io import load_portfolio_csv, row_to_position
from financed_emissions.models import AssetClass

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample_portfolio.csv"


def test_sample_portfolio_loads() -> None:
    positions = load_portfolio_csv(SAMPLE)
    assert len(positions) == 10
    assert {p.asset_class for p in positions} >= {
        AssetClass.BUSINESS_LOANS,
        AssetClass.LISTED_EQUITY,
        AssetClass.MORTGAGES,
        AssetClass.SOVEREIGN_BONDS,
    }
    assert all(p.currency == "HKD" for p in positions)


def test_unknown_asset_class_is_rejected() -> None:
    row = {
        "id": "X-1",
        "borrower": "Bad Row Ltd",
        "asset_class": "crypto_lending",
        "sector": "other",
        "outstanding": "1",
        "attribution_value": "2",
        "scope1_tco2e": "0",
        "scope2_tco2e": "0",
        "scope3_tco2e": "0",
        "data_quality": "5",
    }
    with pytest.raises(ValueError, match="unknown asset_class"):
        row_to_position(row, line_number=2)


def test_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_portfolio_csv("/tmp/does-not-exist-financed-emissions.csv")
