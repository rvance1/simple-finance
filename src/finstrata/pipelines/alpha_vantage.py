import pandas as pd

def format_alpha_vantage(r, start_date=None, end_date=None):
    """
    Convert an Alpha Vantage monthly adjusted time series API response
    into a clean Pandas DataFrame.

    Parameters
    ----------
    r : requests.Response
        The HTTP response object returned by requests.get(url).

    Returns
    -------
    df : pandas.DataFrame
        A DataFrame with datetime index (month-end dates) and
        columns: Open, High, Low, Close, Adjusted Close, Volume, Dividend Amount.
    """

    # Step 1: Convert the JSON response body into a Python dictionary.
    # At this point, 'data' will be a nested dictionary containing
    # both metadata and the monthly adjusted time series.
    data = r.json()

    # Step 2: Access the part of the API response corresponding
    # specifically to the monthly adjusted stock data.
    # This section uses dates as keys and stores open, high, low, close,
    # adjusted close, volume, and dividend info for each month.
    ts_data = data["Monthly Adjusted Time Series"]

    # Step 3: Convert the time series dictionary into a Pandas DataFrame.
    # Using orient="index" tells Pandas to use the dictionary keys (dates)
    # as the DataFrame index, so each row corresponds to one month.
    df = pd.DataFrame.from_dict(ts_data, orient="index")

    # Step 4: Rename columns to something cleaner and easier to read.
    df.columns = [
        "Open", "High", "Low", "Close",
        "Adjusted Close", "Volume", "Dividend Amount"
    ]

    # Step 5: Convert string values into numeric floats.
    # JSON encodes all numbers as strings, so they must be converted
    # for analysis, plotting, and calculations.
    df = df.astype(float)

    # Step 6: Convert the index to datetime and sort chronologically.
    df.index = pd.to_datetime(df.index)
    df.index = df.index.to_period("M")
    df = df.sort_index()

    # Step 7: Apply optional date filtering.
    if start_date is not None:
        df = df[df.index >= pd.Period(start_date, freq="M")]
    if end_date is not None:
        df = df[df.index <= pd.Period(end_date, freq="M")]

    df.index.name = "date"

    return df
