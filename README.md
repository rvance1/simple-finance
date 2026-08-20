# farms

Financial Analysis & Risk Management (`farms`) is a Python toolkit for
teaching and research. It provides a simple interface for downloading
Fama-French factors and portfolio returns from the
[Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html).

## Installation

`farms` requires Python 3.11 or newer.

```bash
python -m pip install farms
```

To work on a local checkout, install it in editable mode:

```bash
python -m pip install -e .
```

The data-loading functions require an internet connection when called.

## CRSP monthly stock data (WRDS)

`get_crsp_msf_by_ids` loads CRSP Monthly Stock File observations through a
caller-provided [WRDS](https://wrds-www.wharton.upenn.edu/) connection. You
need a WRDS account with access to the CRSP data set. `wrds` is intentionally
not installed as a required `farms` dependency, so install it separately:

```bash
python -m pip install wrds
```

Query by PERMNO:

```python
import farms
import wrds

db = wrds.Connection()
monthly = farms.get_crsp_msf_by_ids(
    db,
    identifiers=[14593, 12079],
    start_date="2020-01",
    end_date="2020-12",
    identifier_type="permno",
)
```

Or query by ticker:

```python
monthly = farms.get_crsp_msf_by_ids(
    db,
    identifiers=["AAPL", "MSFT"],
    start_date="2020-01",
    end_date="2020-12",
    identifier_type="ticker",
)
db.close()
```

Dates must use `YYYY-MM` and are inclusive. `identifier_type` may be omitted
for a homogeneous list, but providing it is recommended to avoid ambiguity.
The result has a monthly `PeriodIndex` named `date`; columns include PERMNO,
PERMCO, ticker, company/name-history fields, and CRSP price, return, volume,
and shares-outstanding fields.

### Date range requirements

`start_date` and `end_date` are required for CRSP queries and must both use
the `YYYY-MM` format. `None` is not supported.

The date range is inclusive and refers to complete calendar months. For
example, `start_date="2020-01"` and `end_date="2020-03"` returns observations
from January through March 2020. To request all available history for an
identifier, provide the earliest and latest months appropriate for your
research.

## Fama-French factors

### Date ranges for Fama–French factors and decile portfolios

For Fama–French factor loaders and Kenneth French decile portfolios,
`start_date` and `end_date` are optional.

- When `start_date=None`, the loader requests the full available history,
  beginning from `1900-01-01`.
- When `end_date=None`, the loader requests observations through the latest
  date available from the Kenneth French Data Library.
- You may provide either bound independently.

For example:

```python
# Full available history through the latest available observation
ff3 = farms.get_ff3()

# January 2000 through the latest available observation
ff5 = farms.get_ff5(start_date="2000-01")

# Earliest available history through December 2020
momentum = farms.get_ken_french_deciles(
    "momentum",
    end_date="2020-12",
)
```

Use month-formatted dates (`YYYY-MM`) for monthly factor and decile data.
For daily three-factor data (`get_ff3d`), use day-formatted dates
(`YYYY-MM-DD`).

Monthly three-factor data:

```python
import farms

ff3 = farms.get_ff3("2000-01", "2025-12")
print(ff3.head())
```

The result contains `Mkt-RF`, `SMB`, `HML`, and `RF`.

Monthly five-factor data:

```python
ff5 = farms.get_ff5("2000-01", "2025-12")
print(ff5.head())
```

The result contains `Mkt-RF`, `SMB`, `HML`, `RMW`, `CMA`, and `RF`.

Daily three-factor data:

```python
ff3_daily = farms.get_ff3d("2025-01-01", "2025-12-31")
print(ff3_daily.head())
```

Daily five-factor data:

```python
ff5_daily = farms.get_ff5d("2025-01-01", "2025-12-31")
print(ff5_daily.head())
```

The daily five-factor result contains `Mkt-RF`, `SMB`, `HML`, `RMW`, `CMA`,
and `RF`. Dates are optional; supplying only `start_date` retrieves observations
from that date through the latest available observation:

```python
ff5_daily = farms.get_ff5d(start_date="2025-01-01")
```

Monthly factor data use a pandas `PeriodIndex`. Daily factor data use a
pandas `DatetimeIndex`.

## Kenneth French decile portfolios

Display the available strategies:

```python
farms.get_ken_french_deciles("list")
```

Supported strategies are:

- `accruals`
- `beta`
- `booktomarket`
- `dividendyield`
- `earningsprice`
- `idiosyncraticvariance`
- `investment`
- `momentum`
- `netissuances`
- `profitability`
- `shorttermreversal`
- `size`
- `variance`

Load monthly value-weighted momentum deciles:

```python
momentum = farms.get_ken_french_deciles(
    "momentum",
    start_date="2000-01",
    end_date="2025-12",
)
print(momentum.head())
```

Portfolio columns are named `Dec 1` through `Dec 10`. By default, the result
also contains the market excess return (`mkt-rf`) and risk-free rate (`rf`).

Add all three-factor columns:

```python
momentum_ff3 = farms.get_ken_french_deciles(
    "momentum",
    start_date="2000-01",
    end_date="2025-12",
    factors="FF3",
)
```

This adds `mkt-rf`, `smb`, `hml`, and `rf`.

Add all five-factor columns:

```python
momentum_ff5 = farms.get_ken_french_deciles(
    "momentum",
    start_date="2000-01",
    end_date="2025-12",
    factors="FF5",
)
```

This adds `mkt-rf`, `smb`, `hml`, `rmw`, `cma`, and `rf`.

## Teaching details

Pass `details=True` to print a short explanation of the portfolio construction
and the available date range. The function still returns the DataFrame.

```python
momentum = farms.get_ken_french_deciles(
    "momentum",
    start_date="2000-01",
    end_date="2025-12",
    details=True,
)
```

## Return units

All factor and portfolio returns are expressed as decimals:

- `0.01` means 1%.
- `-0.025` means -2.5%.

This differs from the source files in the Kenneth French Data Library, which
report returns in percent.

## Running tests

Install pytest and run the suite from the repository root:

```bash
python -m pip install pytest
python -m pytest
```
