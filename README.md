# Financed emissions calculator

Created this program with the help of AI, just for my own interest in learning how FE is calculated in real-job setting within a bank.

## Quick start

Requires Python 3.11+.

```bash
git clone https://github.com/<your-github-username>/financed-emissions.git
cd financed-emissions
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
python -m financed_emissions data/sample_portfolio.csv
```

Include Scope 3, or emit JSON:

```bash
python -m financed_emissions data/sample_portfolio.csv --scopes 1,2,3
python -m financed_emissions data/sample_portfolio.csv --json
```

## Sample book

`data/sample_portfolio.csv` is a 10-row, HKD-denominated book that looks like a simplified Hong Kong wholesale + retail mix: listed utilities and shipping, an unlisted developer, CRE, a mortgage pool, a sovereign bond, project finance, and vehicle loans. Run it to get totals, intensity (tCO2e per HKD million outstanding), data-quality, and breakdowns by asset class and sector.

## Code map

```
src/financed_emissions/
  models.py        Position / result dataclasses and PCAF asset classes
  calculator.py    Attribution factor and portfolio roll-up
  io.py            CSV load and validation
  reporting.py     Text report and JSON
  cli.py           Command line
data/sample_portfolio.csv
tests/
```

Use it as a library:

```python
from decimal import Decimal
from financed_emissions import AssetClass, FinancedEmissionsCalculator, Position

loan = Position(
    id="BL-99",
    borrower="Example Borrower Ltd",
    asset_class=AssetClass.BUSINESS_LOANS,
    sector="industrials",
    outstanding=Decimal("2000000000"),
    attribution_value=Decimal("80000000000"),  # total equity + debt
    scope1_tco2e=950_000,
    scope2_tco2e=180_000,
    scope3_tco2e=4_200_000,
    data_quality=2,
)
print(FinancedEmissionsCalculator().calculate_position(loan))
```

## Design choices worth skimming

- **Domain objects first.** Asset class, data-quality score, and attribution denominator are explicit — the formula is not buried in a spreadsheet script.
- **Fail closed.** Missing columns, unknown asset class, zero denominator, mixed currencies, and invalid PCAF scores raise errors instead of silently computing.
- **Stdlib in production code.** `decimal` for money ratios; no pandas required to run the calculator.
- **Tests around the identity.** Attribution math, scope selection, outstanding-weighted data quality, CSV validation, and CLI exit codes.

## Out of scope (on purpose)

Physical-activity emission factors, PCAF database look-ups, FX conversion, double-counting removal across asset classes, and official HKMA templates. Those are the natural next slices if this were taken into a bank book.

## Disclaimer

Personal educational prototype. Not affiliated with PCAF, the Hong Kong Monetary Authority, HKEX, or any bank. Sample counterparties and figures are fictional.
