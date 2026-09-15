from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal, ROUND_HALF_UP

from financed_emissions.models import (
    AssetClass,
    PortfolioResult,
    Position,
    PositionResult,
    SegmentTotal,
)

_FACTOR_QUANT = Decimal("0.0000001")  # 7 d.p. — PCAF attribution is a ratio
_MILLION = Decimal("1000000")


def attribution_factor(position: Position) -> Decimal:
    """Outstanding amount ÷ PCAF attribution denominator.

    PCAF does not cap the factor at 1. A result above 1 usually means
    the denominator is stale or incomplete and should be reviewed.
    """
    factor = position.outstanding / position.attribution_value
    return factor.quantize(_FACTOR_QUANT, rounding=ROUND_HALF_UP)


def _weighted_data_quality(results: Sequence[PositionResult]) -> float:
    """Outstanding-weighted average PCAF data-quality score (1 = best, 5 = worst)."""
    total = sum((r.outstanding for r in results), Decimal("0"))
    if total == 0:
        return 0.0
    weighted = sum(
        (r.outstanding * Decimal(r.position.data_quality) for r in results),
        Decimal("0"),
    )
    return float(weighted / total)


def _segment(label: str, results: Sequence[PositionResult]) -> SegmentTotal:
    outstanding = sum((r.outstanding for r in results), Decimal("0"))
    emissions = sum(r.financed_emissions_tco2e for r in results)
    return SegmentTotal(
        label=label,
        outstanding=outstanding,
        financed_emissions_tco2e=emissions,
        weighted_data_quality=_weighted_data_quality(results),
        position_count=len(results),
    )


class FinancedEmissionsCalculator:
    """Calculate financed emissions for a position or a portfolio.

    Default scopes are 1 and 2, matching PCAF's required reporting
    boundary. Scope 3 can be included when counterparty data exists.
    """

    def __init__(self, scopes: Sequence[int] = (1, 2)) -> None:
        scopes_tuple = tuple(scopes)
        if not scopes_tuple:
            raise ValueError("at least one GHG scope is required")
        unknown = [s for s in scopes_tuple if s not in (1, 2, 3)]
        if unknown:
            raise ValueError(f"unsupported scopes: {unknown}; use 1, 2, and/or 3")
        self.scopes = scopes_tuple

    def calculate_position(self, position: Position) -> PositionResult:
        factor = attribution_factor(position)
        company = position.emissions_for(self.scopes)
        financed = float(factor) * company
        return PositionResult(
            position=position,
            attribution_factor=float(factor),
            company_emissions_tco2e=company,
            financed_emissions_tco2e=financed,
            scopes=self.scopes,
        )

    def calculate_portfolio(self, positions: Sequence[Position]) -> PortfolioResult:
        if not positions:
            raise ValueError("portfolio is empty")
        currencies = {p.currency for p in positions}
        if len(currencies) > 1:
            raise ValueError(
                f"mixed currencies {sorted(currencies)}; convert to one currency first"
            )
        currency = next(iter(currencies))

        results = tuple(self.calculate_position(p) for p in positions)
        total_outstanding = sum((r.outstanding for r in results), Decimal("0"))
        total_emissions = sum(r.financed_emissions_tco2e for r in results)
        intensity = (
            float(Decimal(str(total_emissions)) / (total_outstanding / _MILLION))
            if total_outstanding
            else 0.0
        )

        by_class = self._group(results, key=lambda r: r.position.asset_class)
        by_sector = self._group(results, key=lambda r: r.position.sector)

        return PortfolioResult(
            positions=results,
            scopes=self.scopes,
            currency=currency,
            total_outstanding=total_outstanding,
            total_financed_emissions_tco2e=total_emissions,
            intensity_tco2e_per_million=intensity,
            weighted_data_quality=_weighted_data_quality(results),
            by_asset_class=by_class,
            by_sector=by_sector,
        )

    def _group(self, results: Sequence[PositionResult], key) -> tuple[SegmentTotal, ...]:
        buckets: dict[str, list[PositionResult]] = {}
        for result in results:
            label = key(result)
            label_str = label.value if isinstance(label, AssetClass) else str(label)
            buckets.setdefault(label_str, []).append(result)
        segments = [_segment(label, items) for label, items in buckets.items()]
        segments.sort(key=lambda s: s.financed_emissions_tco2e, reverse=True)
        return tuple(segments)
