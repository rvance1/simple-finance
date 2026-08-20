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

## Fama-French factors

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
