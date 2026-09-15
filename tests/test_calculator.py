from __future__ import annotations

from decimal import Decimal

import pytest

from financed_emissions.calculator import FinancedEmissionsCalculator, attribution_factor
from financed_emissions.models import AssetClass, Position


def _position(**overrides) -> Position:
    values = dict(
        id="T-1",
        borrower="Test Co",
        asset_class=AssetClass.BUSINESS_LOANS,
        sector="industrials",
        outstanding=Decimal("100"),
        attribution_value=Decimal("1000"),
        scope1_tco2e=80.0,
        scope2_tco2e=20.0,
        scope3_tco2e=400.0,
        data_quality=2,
    )
    values.update(overrides)
    return Position(**values)


def test_attribution_factor_is_outstanding_over_denominator() -> None:
    factor = attribution_factor(_position())
    assert factor == Decimal("0.1000000")


def test_listed_equity_uses_evic_as_denominator() -> None:
    position = _position(
        asset_class=AssetClass.LISTED_EQUITY,
        outstanding=Decimal("250000000"),
        attribution_value=Decimal("10000000000"),
    )
    assert attribution_factor(position) == Decimal("0.0250000")


def test_financed_emissions_scopes_1_and_2_by_default() -> None:
    result = FinancedEmissionsCalculator().calculate_position(_position())
    assert result.company_emissions_tco2e == 100.0
    assert result.financed_emissions_tco2e == pytest.approx(10.0)


def test_scope_3_can_be_included() -> None:
    result = FinancedEmissionsCalculator(scopes=(1, 2, 3)).calculate_position(_position())
    assert result.company_emissions_tco2e == 500.0
    assert result.financed_emissions_tco2e == pytest.approx(50.0)


def test_rejects_empty_scopes() -> None:
    with pytest.raises(ValueError, match="at least one"):
        FinancedEmissionsCalculator(scopes=())


def test_rejects_zero_attribution_value() -> None:
    with pytest.raises(ValueError, match="attribution_value"):
        _position(attribution_value=Decimal("0"))


def test_rejects_invalid_data_quality() -> None:
    with pytest.raises(ValueError, match="data_quality"):
        _position(data_quality=6)


def test_portfolio_aggregates_and_weights_data_quality() -> None:
    cheap_hq = _position(
        id="A",
        outstanding=Decimal("100"),
        attribution_value=Decimal("1000"),
        scope1_tco2e=100.0,
        scope2_tco2e=0.0,
        scope3_tco2e=0.0,
        data_quality=1,
        sector="utilities",
    )
    large_lq = _position(
        id="B",
        outstanding=Decimal("300"),
        attribution_value=Decimal("1000"),
        scope1_tco2e=100.0,
        scope2_tco2e=0.0,
        scope3_tco2e=0.0,
        data_quality=5,
        sector="transport",
        asset_class=AssetClass.CORPORATE_BONDS,
    )
    portfolio = FinancedEmissionsCalculator().calculate_portfolio([cheap_hq, large_lq])

    assert portfolio.total_outstanding == Decimal("400")
    assert portfolio.total_financed_emissions_tco2e == pytest.approx(40.0)
    # outstanding-weighted DQ: (100*1 + 300*5) / 400 = 4.0
    assert portfolio.weighted_data_quality == pytest.approx(4.0)
    assert portfolio.by_sector[0].label in {"utilities", "transport"}
    assert len(portfolio.by_asset_class) == 2


def test_mixed_currencies_are_rejected() -> None:
    hkd = _position(id="HK", currency="HKD")
    usd = _position(id="US", currency="USD")
    with pytest.raises(ValueError, match="mixed currencies"):
        FinancedEmissionsCalculator().calculate_portfolio([hkd, usd])


def test_empty_portfolio_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        FinancedEmissionsCalculator().calculate_portfolio([])
