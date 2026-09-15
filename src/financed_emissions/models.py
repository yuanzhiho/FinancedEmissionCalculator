from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class AssetClass(str, Enum):
    """PCAF asset classes covered by this prototype."""

    LISTED_EQUITY = "listed_equity"
    CORPORATE_BONDS = "corporate_bonds"
    BUSINESS_LOANS = "business_loans"
    UNLISTED_EQUITY = "unlisted_equity"
    PROJECT_FINANCE = "project_finance"
    COMMERCIAL_REAL_ESTATE = "commercial_real_estate"
    MORTGAGES = "mortgages"
    MOTOR_VEHICLE_LOANS = "motor_vehicle_loans"
    SOVEREIGN_BONDS = "sovereign_bonds"

    @property
    def attribution_label(self) -> str:
        """Human-readable name of the PCAF attribution denominator."""
        labels = {
            AssetClass.LISTED_EQUITY: "EVIC",
            AssetClass.CORPORATE_BONDS: "EVIC",
            AssetClass.BUSINESS_LOANS: "EVIC or total equity + debt",
            AssetClass.UNLISTED_EQUITY: "total equity + debt",
            AssetClass.PROJECT_FINANCE: "total project equity + debt",
            AssetClass.COMMERCIAL_REAL_ESTATE: "property value at origination",
            AssetClass.MORTGAGES: "property value at origination",
            AssetClass.MOTOR_VEHICLE_LOANS: "vehicle value at origination",
            AssetClass.SOVEREIGN_BONDS: "PPP-adjusted GDP",
        }
        return labels[self]


@dataclass(frozen=True)
class Position:
    """A single loan or investment in the financed-emissions book.

    ``attribution_value`` is the PCAF denominator for the asset class
    (EVIC, total capital, property value, PPP-adjusted GDP, etc.).
    Emissions are the *counterparty or asset* totals in tCO2e, not the
    financed share.
    """

    id: str
    borrower: str
    asset_class: AssetClass
    sector: str
    outstanding: Decimal
    attribution_value: Decimal
    scope1_tco2e: float
    scope2_tco2e: float
    scope3_tco2e: float
    data_quality: int
    currency: str = "HKD"
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("position id is required")
        if self.outstanding < 0:
            raise ValueError(f"{self.id}: outstanding cannot be negative")
        if self.attribution_value <= 0:
            raise ValueError(f"{self.id}: attribution_value must be positive")
        if self.data_quality not in (1, 2, 3, 4, 5):
            raise ValueError(f"{self.id}: data_quality must be an integer 1-5")
        for label, value in (
            ("scope1", self.scope1_tco2e),
            ("scope2", self.scope2_tco2e),
            ("scope3", self.scope3_tco2e),
        ):
            if value < 0:
                raise ValueError(f"{self.id}: {label} emissions cannot be negative")

    def emissions_for(self, scopes: tuple[int, ...]) -> float:
        mapping = {1: self.scope1_tco2e, 2: self.scope2_tco2e, 3: self.scope3_tco2e}
        unknown = [s for s in scopes if s not in mapping]
        if unknown:
            raise ValueError(f"unsupported scopes: {unknown}; use 1, 2, and/or 3")
        return sum(mapping[s] for s in scopes)


@dataclass(frozen=True)
class PositionResult:
    position: Position
    attribution_factor: float
    company_emissions_tco2e: float
    financed_emissions_tco2e: float
    scopes: tuple[int, ...]

    @property
    def outstanding(self) -> Decimal:
        return self.position.outstanding


@dataclass(frozen=True)
class SegmentTotal:
    label: str
    outstanding: Decimal
    financed_emissions_tco2e: float
    weighted_data_quality: float
    position_count: int


@dataclass(frozen=True)
class PortfolioResult:
    positions: tuple[PositionResult, ...]
    scopes: tuple[int, ...]
    currency: str
    total_outstanding: Decimal
    total_financed_emissions_tco2e: float
    intensity_tco2e_per_million: float
    weighted_data_quality: float
    by_asset_class: tuple[SegmentTotal, ...]
    by_sector: tuple[SegmentTotal, ...]
