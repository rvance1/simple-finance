import re
from collections.abc import Mapping

import pandas as pd


_MONTHLY_ADJUSTED_FIELDS = {
    "1. open": "Open",
    "2. high": "High",
    "3. low": "Low",
    "4. close": "Close",
    "5. adjusted close": "Adjusted Close",
    "6. volume": "Volume",
    "7. dividend amount": "Dividend Amount",
}


def format_alpha_vantage(r, start_date=None, end_date=None):
    """Format an Alpha Vantage monthly adjusted response as a DataFrame.

    Parameters
    ----------
    r : requests.Response
        Response from an Alpha Vantage ``TIME_SERIES_MONTHLY_ADJUSTED`` request.
    start_date, end_date : str, optional
        Inclusive monthly filters in ``YYYY-MM`` format. ``None`` leaves that
        side of the date range unbounded.

    Returns
    -------
    pandas.DataFrame
        Numeric Open, High, Low, Close, Adjusted Close, Volume, and Dividend
        Amount columns with a monthly ``PeriodIndex`` named ``date``.

    Raises
    ------
    ValueError
        If dates are invalid, the response is malformed, or Alpha Vantage
        returns an API, information, or rate-limit message.
    """

    for value in (start_date, end_date):
        if value is not None and (
            not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}", value)
        ):
            raise ValueError("start_date and end_date must use the 'YYYY-MM' format.")

    start_period = pd.Period(start_date, freq="M") if start_date is not None else None
    end_period = pd.Period(end_date, freq="M") if end_date is not None else None
    if start_period is not None and end_period is not None and start_period > end_period:
        raise ValueError("start_date must not be after end_date.")

    r.raise_for_status()

    try:
        data = r.json()
    except ValueError as error:
        raise ValueError("Alpha Vantage response did not contain valid JSON.") from error

    if not isinstance(data, Mapping):
        raise ValueError("Alpha Vantage response must be a JSON object.")

    if "Note" in data:
        raise ValueError(f"Alpha Vantage rate limit: {data['Note']}")
    if "Error Message" in data:
        raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
    if "Information" in data:
        raise ValueError(f"Alpha Vantage information: {data['Information']}")

    ts_data = data.get("Monthly Adjusted Time Series")
    if not isinstance(ts_data, Mapping) or not ts_data:
        raise ValueError(
            "Alpha Vantage response did not contain a nonempty "
            "'Monthly Adjusted Time Series'."
        )

    for date, observation in ts_data.items():
        if not isinstance(observation, Mapping):
            raise ValueError(
                f"Alpha Vantage observation for {date!r} must be a JSON object."
            )
        missing_fields = [
            field for field in _MONTHLY_ADJUSTED_FIELDS if field not in observation
        ]
        if missing_fields:
            raise ValueError(
                f"Alpha Vantage observation for {date!r} is missing expected fields: "
                f"{', '.join(missing_fields)}."
            )

    # Step 3: Convert the time series dictionary into a Pandas DataFrame.
    # Using orient="index" tells Pandas to use the dictionary keys (dates)
    # as the DataFrame index, so each row corresponds to one month.
    df = pd.DataFrame.from_dict(ts_data, orient="index")

    # Select source fields by name so JSON key order cannot affect the result.
    df = df.loc[:, list(_MONTHLY_ADJUSTED_FIELDS)].rename(
        columns=_MONTHLY_ADJUSTED_FIELDS
    )

    # Step 5: Convert string values into numeric floats.
    # JSON encodes all numbers as strings, so they must be converted
    # for analysis, plotting, and calculations.
    df = df.apply(pd.to_numeric, errors="raise")

    # Step 6: Convert the index to datetime and sort chronologically.
    df.index = pd.to_datetime(df.index)
    df.index = df.index.to_period("M")
    df = df.sort_index()

    # Step 7: Apply optional date filtering.
    if start_period is not None:
        df = df[df.index >= start_period]
    if end_period is not None:
        df = df[df.index <= end_period]

    df.index.name = "date"

    return df
