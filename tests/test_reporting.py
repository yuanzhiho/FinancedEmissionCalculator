from __future__ import annotations

from decimal import Decimal

import pytest

from financed_emissions.calculator import FinancedEmissionsCalculator
from financed_emissions.models import AssetClass, Position
from financed_emissions.reporting import dumps_json, format_report, result_to_dict


def test_report_contains_headline_totals() -> None:
    position = Position(
        id="R-1",
        borrower="Report Co",
        asset_class=AssetClass.BUSINESS_LOANS,
        sector="industrials",
        outstanding=Decimal("1000000"),
        attribution_value=Decimal("10000000"),
        scope1_tco2e=1000.0,
        scope2_tco2e=0.0,
        scope3_tco2e=0.0,
        data_quality=2,
    )
    result = FinancedEmissionsCalculator().calculate_portfolio([position])
    text = format_report(result)
    assert "Financed emissions" in text
    assert "100.0 tCO2e" in text
    assert "industrials" in text

    payload = result_to_dict(result)
    assert payload["position_count"] == 1
    assert payload["positions"][0]["attribution_factor"] == pytest.approx(0.1)

    json_text = dumps_json(result)
    assert '"weighted_data_quality"' in json_text
