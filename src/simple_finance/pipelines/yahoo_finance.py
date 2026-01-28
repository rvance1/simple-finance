import pandas as pd
import yfinance as yf

from .dartmouth import get_ff3

def get_monthly_returns(tickers, start_date, end_date, tbill_return=True):
    """
    This function fetches monthly returns for a given ticker over a 
    specified date range from yahoo finance.

    Parameters:
    - ticker (str): The ticker symbol of the stock.
    - start_date (str): The start date in 'YYYY-MM-DD' format.
    - end_date (str): The end date in 'YYYY-MM-DD' format.

    Returns:
    - DataFrame: A DataFrame with monthly returns and adjusted close prices.
    """
    all_returns = pd.DataFrame()
    adjusted_start_date = pd.to_datetime(start_date) - pd.DateOffset(months=1)
    for ticker in tickers:
        # Download daily data from Yahoo Finance
        data = yf.download(ticker, start=adjusted_start_date, end=end_date, interval="1d", auto_adjust=False)
        data['date'] = data.index

        # Resample data to get the last business day of each month
        month_end_data = data.groupby([data.index.year, data.index.month]).apply(lambda x: x.loc[x.index.max()])
        month_end_data = month_end_data.set_index('date')

        # Calculate monthly returns based on month-end data
        month_end_data = month_end_data.sort_index()
        month_end_data['Monthly Return'] = month_end_data['Adj Close'].pct_change()


        # Drop any missing values (the first row will have NaN for returns)
        month_end_data.dropna(inplace=True)

        all_returns[ticker] = month_end_data['Monthly Return']

    if tbill_return:
        ff3 = get_ff3()
        all_returns['YearMonth'] = all_returns.index.to_period('M')
        all_returns = pd.merge(all_returns, ff3[['RF']], left_on='YearMonth', right_index=True, how='left')
        all_returns.drop('YearMonth', axis=1, inplace=True)

    return all_returns