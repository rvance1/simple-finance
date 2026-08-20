import pandas as pd
from pandas_datareader import data as web


_DECILE_DATASETS = {
    "accruals": {
        "dataset": "Portfolios_Formed_on_AC",
        "title": "Accruals",
        "table": 0,
    },
    "beta": {
        "dataset": "Portfolios_Formed_on_BETA",
        "title": "Beta",
        "table": 0,
    },
    "booktomarket": {
        "dataset": "Portfolios_Formed_on_BE-ME",
        "title": "Book-to-Market",
        "table": 0,
    },
    "dividendyield": {
        "dataset": "Portfolios_Formed_on_D-P",
        "title": "Dividend Yield",
        "table": 0,
    },
    "earningsprice": {
        "dataset": "Portfolios_Formed_on_E-P",
        "title": "Earnings-to-Price",
        "table": 0,
    },
    "idiosyncraticvariance": {
        "dataset": "Portfolios_Formed_on_RESVAR",
        "title": "Idiosyncratic Variance",
        "table": 0,
    },
    "investment": {
        "dataset": "Portfolios_Formed_on_INV",
        "title": "Investment",
        "table": 0,
    },
    "momentum": {
        "dataset": "10_Portfolios_Prior_12_2",
        "title": "Momentum",
        "table": 0,
    },
    "netissuances": {
        "dataset": "Portfolios_Formed_on_NI",
        "title": "Net Share Issuances",
        "table": 0,
    },
    "profitability": {
        "dataset": "Portfolios_Formed_on_OP",
        "title": "Profitability",
        "table": 0,
    },
    "shorttermreversal": {
        "dataset": "10_Portfolios_Prior_1_0",
        "title": "Short-Term Reversal",
        "table": 0,
    },
    "size": {
        "dataset": "Portfolios_Formed_on_ME",
        "title": "Size",
        "table": 0,
    },
    "variance": {
        "dataset": "Portfolios_Formed_on_VAR",
        "title": "Variance",
        "table": 0,
    },
}

_DECILE_COLUMNS = [
    "Lo 10",
    *[f"Dec {number}" for number in range(2, 10)],
    "Hi 10",
]


def _load_french_dataset(dataset, start_date=None, end_date=None):
    """Load a dataset from the Kenneth French Data Library."""
    # pandas-datareader otherwise defaults to only five years of history.
    # The original farms loaders returned the complete French time series.
    reader_start = "1900-01-01" if start_date is None else start_date
    return web.DataReader(
        dataset,
        "famafrench",
        start=reader_start,
        end=end_date,
    )


def _inspect_french_dataset(dataset, start_date=None, end_date=None):
    """Return table metadata for a pandas-datareader French dataset."""
    result = _load_french_dataset(dataset, start_date, end_date)
    tables = {}

    for key, value in result.items():
        if isinstance(key, int) and isinstance(value, pd.DataFrame):
            tables[key] = {
                "rows": len(value),
                "columns": list(value.columns),
                "index_type": type(value.index).__name__,
                "index_frequency": getattr(value.index, "freqstr", None),
            }

    return {
        "dataset": dataset,
        "description": result.get("DESCR", ""),
        "tables": tables,
    }


def _load_decile_returns(strategy, start_date=None, end_date=None):
    """Return monthly value-weighted decile returns for a strategy."""
    try:
        config = _DECILE_DATASETS[strategy]
    except KeyError as exc:
        choices = ", ".join(sorted(_DECILE_DATASETS))
        raise ValueError(
            f"Unknown decile strategy {strategy!r}. Choose one of: {choices}."
        ) from exc

    result = _load_french_dataset(
        config["dataset"],
        start_date,
        end_date,
    )
    table = result[config["table"]].copy()

    missing_columns = [column for column in _DECILE_COLUMNS if column not in table]
    if missing_columns:
        raise ValueError(
            f"{config['dataset']} table {config['table']} is missing expected "
            f"decile columns: {', '.join(missing_columns)}."
        )

    deciles = table.loc[:, _DECILE_COLUMNS].copy()
    deciles.columns = [f"Dec {number}" for number in range(1, 11)]
    deciles = deciles.apply(pd.to_numeric, errors="coerce") / 100
    deciles.index.name = "date"
    return deciles


def get_ff5(start_date=None, end_date=None):
    """Return monthly Fama-French five-factor data as decimal returns."""
    result = _load_french_dataset(
        "F-F_Research_Data_5_Factors_2x3",
        start_date,
        end_date,
    )

    df = result[0].copy()
    df = df.apply(pd.to_numeric, errors="coerce") / 100
    df.index.name = "date"
    return df

def get_ff3(start_date=None, end_date=None):
    """Return monthly Fama-French three-factor data as decimal returns."""
    result = _load_french_dataset(
        "F-F_Research_Data_Factors",
        start_date,
        end_date,
    )

    df = result[0].copy()
    df = df.apply(pd.to_numeric, errors="coerce") / 100
    df.index.name = "date"
    return df


def get_ff3d(start_date=None, end_date=None):
    """Return daily Fama-French three-factor data as decimal returns."""
    result = _load_french_dataset(
        "F-F_Research_Data_Factors_daily",
        start_date,
        end_date,
    )

    df = result[0].copy()
    df = df.apply(pd.to_numeric, errors="coerce") / 100
    if isinstance(df.index, pd.PeriodIndex):
        df.index = df.index.to_timestamp()
    df.index.freq = None
    df.index.name = "date"
    return df


def get_ff5d(start_date=None, end_date=None):
    """Return daily Fama-French five-factor data as decimal returns."""
    result = _load_french_dataset(
        "F-F_Research_Data_5_Factors_2x3_daily",
        start_date,
        end_date,
    )

    df = result[0].copy()
    df = df.apply(pd.to_numeric, errors="coerce") / 100
    if isinstance(df.index, pd.PeriodIndex):
        df.index = df.index.to_timestamp()
    df.index.freq = None
    df.index.name = "date"
    return df

_DECILE_DETAILS = {
    "accruals": (
        "The portfolios are formed on accruals at the end of each June using NYSE breakpoints.",
        "Accruals measure the change in operating working capital per split-adjusted share, "
        "scaled by book equity per share.",
        "Stocks are sorted into deciles, and each portfolio is value-weighted.",
    ),
    "beta": (
        "Stocks are sorted into deciles based on historical market betas.",
        "Portfolios are formed at the end of each June using NYSE breakpoints.",
        "Beta uses the preceding five years of monthly returns, with a two-year minimum.",
    ),
    "booktomarket": (
        "Portfolios are formed on book equity to market equity (BE/ME) at the end of "
        "each June using NYSE breakpoints.",
        "Book equity comes from the prior fiscal year; market equity is measured at "
        "the end of the prior December.",
    ),
    "dividendyield": (
        "Portfolios are formed on dividend yield (D/P) at the end of each June using "
        "NYSE breakpoints.",
        "Dividend yield is dividends paid from July through June per dollar of June "
        "market equity.",
    ),
    "earningsprice": (
        "Portfolios are formed on earnings-to-price (E/P) at the end of each June "
        "using NYSE breakpoints.",
        "Earnings come from the prior fiscal year, and price is represented by market equity.",
    ),
    "idiosyncraticvariance": (
        "Portfolios are formed monthly on residual-return variance using NYSE breakpoints.",
        "Residual variance is estimated from the Fama-French three-factor model using "
        "60 lagged trading days, with a 20-day minimum.",
    ),
    "investment": (
        "Investment is the change in total assets from fiscal year t-2 to t-1, "
        "divided by total assets in t-2.",
        "Deciles are formed using NYSE breakpoints.",
    ),
    "momentum": (
        "Stocks are sorted into deciles on prior returns from months t-12 through t-2.",
        "Portfolios are formed monthly using NYSE breakpoints and are value-weighted.",
    ),
    "netissuances": (
        "Portfolios are formed on net share issuance at the end of each June using "
        "NYSE breakpoints.",
        "Net issuance is the change in log split-adjusted shares outstanding between "
        "the prior two fiscal year ends.",
    ),
    "profitability": (
        "Portfolios are formed on operating profitability at the end of each June "
        "using NYSE breakpoints.",
        "Operating profitability is revenues less cost of goods sold, interest, and "
        "selling, general, and administrative expenses, divided by book equity.",
    ),
    "shorttermreversal": (
        "Stocks are sorted into deciles based on their prior one-month return.",
        "Portfolios are formed monthly using NYSE breakpoints and are value-weighted.",
    ),
    "size": (
        "Size deciles are formed at the end of each June using June market equity "
        "and NYSE breakpoints.",
    ),
    "variance": (
        "Portfolios are formed monthly on daily-return variance using NYSE breakpoints.",
        "Variance is estimated using 60 lagged trading days, with a 20-day minimum.",
    ),
}


def _get_decile_metadata(strategy, deciles):
    """Return structured teaching metadata for a decile strategy."""
    config = _DECILE_DATASETS[strategy]
    return {
        "strategy": strategy,
        "title": config["title"],
        "dataset": config["dataset"],
        "table": config["table"],
        "description": list(_DECILE_DETAILS[strategy]),
        "min_date": deciles.index.min(),
        "max_date": deciles.index.max(),
    }


def _print_decile_details(metadata):
    """Print structured decile metadata in a student-friendly format."""
    separator = "-" * max(16, len(metadata["title"]))
    print(separator)
    print(metadata["title"])
    print(separator)
    for line in metadata["description"]:
        print(line)
    print()
    print(
        f"Min Date: {metadata['min_date']}, "
        f"Max Date: {metadata['max_date']}"
    )


def _merge_decile_factors(deciles, factors=None, start_date=None, end_date=None):
    """Merge requested Fama-French factors into monthly decile returns."""
    if factors not in {None, "FF3", "FF5"}:
        raise ValueError("factors must be None, 'FF3', or 'FF5'.")

    if factors == "FF5":
        factor_data = get_ff5(start_date, end_date).rename(
            columns={
                "Mkt-RF": "mkt-rf",
                "SMB": "smb",
                "HML": "hml",
                "RMW": "rmw",
                "CMA": "cma",
                "RF": "rf",
            }
        )
        factor_columns = ["mkt-rf", "smb", "hml", "rmw", "cma", "rf"]
    elif factors == "FF3":
        factor_data = get_ff3(start_date, end_date).rename(
            columns={
                "Mkt-RF": "mkt-rf",
                "SMB": "smb",
                "HML": "hml",
                "RF": "rf",
            }
        )
        factor_columns = ["mkt-rf", "smb", "hml", "rf"]
    else:
        factor_data = get_ff3(start_date, end_date).rename(
            columns={"Mkt-RF": "mkt-rf", "RF": "rf"}
        )
        factor_columns = ["mkt-rf", "rf"]

    return deciles.merge(
        factor_data[factor_columns],
        left_index=True,
        right_index=True,
        how="inner",
    )


def get_ken_french_deciles(
    stype,
    start_date=None,
    end_date=None,
    details=None,
    factors=None,
):
    """Return monthly value-weighted Kenneth French decile portfolios."""
    if stype == "list":
        for strategy in _DECILE_DATASETS:
            print(strategy)
        return None

    deciles = _load_decile_returns(stype, start_date, end_date)

    if details is True:
        metadata = _get_decile_metadata(stype, deciles)
        _print_decile_details(metadata)

    return _merge_decile_factors(deciles, factors, start_date, end_date)
