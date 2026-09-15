from __future__ import annotations

import csv
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
from pathlib import Path

from financed_emissions.models import AssetClass, Position

_REQUIRED = (
    "id",
    "borrower",
    "asset_class",
    "sector",
    "outstanding",
    "attribution_value",
    "scope1_tco2e",
    "scope2_tco2e",
    "scope3_tco2e",
    "data_quality",
)


def _decimal(row_id: str, field: str, raw: str) -> Decimal:
    try:
        return Decimal(raw.strip().replace(",", ""))
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"{row_id}: invalid {field}={raw!r}") from exc


def _float(row_id: str, field: str, raw: str) -> float:
    try:
        return float(raw.strip().replace(",", ""))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{row_id}: invalid {field}={raw!r}") from exc


def row_to_position(row: dict[str, str], line_number: int) -> Position:
    missing = [c for c in _REQUIRED if not (row.get(c) or "").strip()]
    if missing:
        raise ValueError(f"line {line_number}: missing columns {missing}")

    row_id = row["id"].strip()
    try:
        asset_class = AssetClass(row["asset_class"].strip())
    except ValueError as exc:
        allowed = ", ".join(a.value for a in AssetClass)
        raise ValueError(
            f"{row_id}: unknown asset_class={row['asset_class']!r}; expected one of: {allowed}"
        ) from exc

    return Position(
        id=row_id,
        borrower=row["borrower"].strip(),
        asset_class=asset_class,
        sector=row["sector"].strip(),
        outstanding=_decimal(row_id, "outstanding", row["outstanding"]),
        attribution_value=_decimal(row_id, "attribution_value", row["attribution_value"]),
        scope1_tco2e=_float(row_id, "scope1_tco2e", row["scope1_tco2e"]),
        scope2_tco2e=_float(row_id, "scope2_tco2e", row["scope2_tco2e"]),
        scope3_tco2e=_float(row_id, "scope3_tco2e", row["scope3_tco2e"]),
        data_quality=int(row["data_quality"].strip()),
        currency=(row.get("currency") or "HKD").strip() or "HKD",
        notes=(row.get("notes") or "").strip(),
    )


def load_portfolio_csv(path: str | Path) -> list[Position]:
    """Load positions from a CSV file. See ``data/sample_portfolio.csv`` for columns."""
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"portfolio file not found: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path}: CSV has no header row")
        positions = [
            row_to_position(row, line_number=index)
            for index, row in enumerate(reader, start=2)
        ]

    if not positions:
        raise ValueError(f"{csv_path}: no data rows")
    return positions


def iter_asset_classes() -> Iterable[str]:
    return (item.value for item in AssetClass)
