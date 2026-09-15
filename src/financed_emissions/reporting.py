from __future__ import annotations

import json
from decimal import Decimal

from financed_emissions.models import PortfolioResult, PositionResult, SegmentTotal


def _money(value: Decimal) -> str:
    quantized = value.quantize(Decimal("0.01"))
    return f"{quantized:,.2f}"


def _tco2e(value: float) -> str:
    return f"{value:,.1f}"


def _scopes_label(scopes: tuple[int, ...]) -> str:
    return "+".join(str(s) for s in scopes)


def format_report(result: PortfolioResult) -> str:
    """Plain-text portfolio report suitable for a terminal or README."""
    lines = [
        "Financed emissions (PCAF-style prototype)",
        "=" * 48,
        f"Scopes included          : {_scopes_label(result.scopes)}",
        f"Positions                : {len(result.positions)}",
        f"Total outstanding        : {result.currency} {_money(result.total_outstanding)}",
        f"Financed emissions       : {_tco2e(result.total_financed_emissions_tco2e)} tCO2e",
        f"Intensity                : {result.intensity_tco2e_per_million:,.2f} tCO2e / {result.currency} million",
        f"Weighted data quality    : {result.weighted_data_quality:.2f}  (1=verified reported, 5=estimated)",
        "",
        "By asset class",
        "-" * 48,
        _segment_table(result.by_asset_class, result.currency),
        "",
        "By sector",
        "-" * 48,
        _segment_table(result.by_sector, result.currency),
        "",
        "Positions",
        "-" * 48,
    ]
    for item in result.positions:
        lines.append(_position_line(item, result.currency))
    lines.append("")
    lines.append(
        "Disclaimer: illustrative calculation only. Not PCAF-assured, "
        "not for regulatory reporting."
    )
    return "\n".join(lines)


def _segment_table(segments: tuple[SegmentTotal, ...], currency: str) -> str:
    header = f"{'segment':<28} {'n':>3} {'outstanding':>18} {'tCO2e':>14} {'DQ':>6}"
    rows = [header]
    for seg in segments:
        rows.append(
            f"{seg.label:<28} {seg.position_count:>3} "
            f"{currency + ' ' + _money(seg.outstanding):>18} "
            f"{_tco2e(seg.financed_emissions_tco2e):>14} "
            f"{seg.weighted_data_quality:>6.2f}"
        )
    return "\n".join(rows)


def _position_line(item: PositionResult, currency: str) -> str:
    p = item.position
    return (
        f"- {p.id}: {p.borrower} [{p.asset_class.value}] "
        f"AF={item.attribution_factor:.6f}  "
        f"financed={_tco2e(item.financed_emissions_tco2e)} tCO2e  "
        f"DQ={p.data_quality}  "
        f"({currency} {_money(p.outstanding)} outstanding)"
    )


def result_to_dict(result: PortfolioResult) -> dict:
    return {
        "scopes": list(result.scopes),
        "currency": result.currency,
        "position_count": len(result.positions),
        "total_outstanding": str(result.total_outstanding),
        "total_financed_emissions_tco2e": result.total_financed_emissions_tco2e,
        "intensity_tco2e_per_million": result.intensity_tco2e_per_million,
        "weighted_data_quality": result.weighted_data_quality,
        "by_asset_class": [_segment_dict(s) for s in result.by_asset_class],
        "by_sector": [_segment_dict(s) for s in result.by_sector],
        "positions": [_position_dict(p) for p in result.positions],
    }


def _segment_dict(seg: SegmentTotal) -> dict:
    return {
        "label": seg.label,
        "position_count": seg.position_count,
        "outstanding": str(seg.outstanding),
        "financed_emissions_tco2e": seg.financed_emissions_tco2e,
        "weighted_data_quality": seg.weighted_data_quality,
    }


def _position_dict(item: PositionResult) -> dict:
    p = item.position
    return {
        "id": p.id,
        "borrower": p.borrower,
        "asset_class": p.asset_class.value,
        "sector": p.sector,
        "outstanding": str(p.outstanding),
        "attribution_value": str(p.attribution_value),
        "attribution_factor": item.attribution_factor,
        "company_emissions_tco2e": item.company_emissions_tco2e,
        "financed_emissions_tco2e": item.financed_emissions_tco2e,
        "data_quality": p.data_quality,
        "currency": p.currency,
        "notes": p.notes,
    }


def dumps_json(result: PortfolioResult) -> str:
    return json.dumps(result_to_dict(result), indent=2)
