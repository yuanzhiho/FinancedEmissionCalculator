"""PCAF-style financed emissions calculator.

Educational prototype implementing the core PCAF attribution formula:

    financed emissions = (outstanding / attribution value) × company emissions

Not affiliated with PCAF, HKMA, or any bank. Not for regulatory reporting.
"""

from financed_emissions.calculator import FinancedEmissionsCalculator
from financed_emissions.models import AssetClass, Position, PositionResult, PortfolioResult

__all__ = [
    "AssetClass",
    "FinancedEmissionsCalculator",
    "Position",
    "PositionResult",
    "PortfolioResult",
]
__version__ = "0.1.0"
