import pandas as pd
import io
import zipfile
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_ff5(start_date=None, end_date=None):
    """
    This functions downloads and processes the Fama-French 
    5-Factor data from the Dartmouth website using the 'requests' library. 
    """

    url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip"

    session = requests.Session()

    retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    r = session.get(url, timeout=60)
    r.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        with zf.open("F-F_Research_Data_5_Factors_2x3.csv") as f:
            raw = pd.read_csv(f, skiprows=3)

    # find where monthly section ends (right before the "Annual Factors..." line)
    stop = raw[raw.iloc[:, 0].astype(str).str.contains("Annual Factors: January-December", na=False)].index[0]
    df = raw.iloc[:stop].copy()

    # normalize first column name and convert to monthly PeriodIndex
    first_col = df.columns[0]
    df.rename(columns={first_col: "date"}, inplace=True)
    df["date"] = pd.PeriodIndex(df["date"].astype(str), freq="M")

    # convert remaining columns to numeric and scale from % to decimal
    for c in df.columns[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df.iloc[:, 1:] = df.iloc[:, 1:] * 0.01

    # set index, drop any non-date rows, sort
    df.set_index("date", inplace=True)
    df = df.dropna(how="all")  # drop any junk rows if present
    df = df.sort_index()

    # helper: coerce any input to a monthly Period
    def _to_period_m(x):
        if x is None:
            return None
        if isinstance(x, pd.Period):
            return x.asfreq("M")
        # accept 'YYYY-MM', 'YYYYMM', datetime, etc.
        return pd.Period(pd.to_datetime(str(x)).strftime("%Y-%m"), freq="M")

    start_p = _to_period_m(start_date)
    end_p   = _to_period_m(end_date)

    # clean slicing by Period
    if start_p or end_p:
        df = df.loc[start_p:end_p]

    return df

def get_ff3(start_date=None, end_date=None):
    """
    This functions downloads and processes the Fama-French 3-Factor 
    data from the Dartmouth website using the 'requests' library. 
    """

    url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip"
    session = requests.Session()

    retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    r = session.get(url, timeout=60)
    r.raise_for_status()

    # Open the zip file from the content
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        with zf.open('F-F_Research_Data_Factors.csv') as f:
            # Read the CSV file content (you can load it into pandas or process as needed)
            ff_three_factors = pd.read_csv(f, skiprows=3)

    start_index = ff_three_factors[ff_three_factors.iloc[:, 0].str.contains("Annual Factors: January-December", na=False)].index[0]
    ff3_1 = ff_three_factors.iloc[:start_index]

    ff3_2=ff3_1.copy()
    ff3_2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

    # Convert first column to Period
    ff3_2['date'] = pd.to_datetime(ff3_2['date'].astype(str), format='%Y%m').dt.to_period()
    # Convert all columns except 'date' to numeric types
    for col in ff3_2.columns[1:]:  # Skip the 'date' column
        ff3_2[col] = pd.to_numeric(ff3_2[col], errors='coerce')

    ff3_2.iloc[:, 1:] = ff3_2.iloc[:, 1:] * 0.01

    # reset the index
    ff3_2.set_index('date', inplace=True)

    # Apply date range filtering if provided
    if start_date is not None:
        ff3_2 = ff3_2[ff3_2.index >= pd.Period(start_date, freq='M')]
    if end_date is not None:
        ff3_2 = ff3_2[ff3_2.index <= pd.Period(end_date, freq='M')]

    return ff3_2

def get_ken_french_deciles(stype, start_date=None, end_date=None, details=None, factors=None):

    if stype == 'list':
        strategies = ['accruals', 'beta', 'booktomarket', 'dividendyield', 'earningsprice', 'idiosyncraticvariance', 'investment',
            'momentum', 'netissuances', 'profitability', 'shorttermreversal', 'size', 'variance']

        for s in strategies:
            print(s)
        return

    elif stype == 'beta':

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_BETA_csv.zip"
        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('Portfolios_Formed_on_BETA.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=15, header=0, encoding='utf-8', skipfooter=5, engine='python')

        start_index = dat[dat.iloc[:, 0].str.contains("Equal Weighted Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()

        # Convert all columns except 'date' to numeric types
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)
        dat2.rename(columns={'Lo 10': 'Dec 1', 'Hi 10': 'Dec 10'}, inplace=True)
        cols = ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5',
                'Dec 6', 'Dec 7', 'Dec 8', 'Dec 9', 'Dec 10']

        dat3 = dat2[cols].copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("----------------")
            print("Beta Strategy")
            print("----------------")
            print("Basic Strategy: stocks are sorted into deciles based on their historical betas.")
            print()
            print("Construction: The portfolios are formed on univariate market beta at the end of each June using NYSE breakpoints.")
            print("Beta for June of year t is estimated using the preceding five years (two minimum) of past monthly returns.")
            print()

            print("Stocks: All NYSE, AMEX, and NASDAQ stocks for which we have market equity data for June of t and good returns for the preceding 60 months (24 months minimum)."
                  )
            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")


    #-------------------------------------------
    elif stype == "momentum":


        # Continue the momentum strategy implementation below

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Portfolios_Prior_12_2_csv.zip"

        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('10_Portfolios_Prior_12_2.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=10, header=0)



        start_index = dat[dat.iloc[:, 0].str.contains("Average Equal Weighted Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)
        dat2.rename(columns={'Lo PRIOR': 'Dec 1', 'PRIOR 2': 'Dec 2', 'PRIOR 3': 'Dec 3', 'PRIOR 4': 'Dec 4'}, inplace=True)
        dat2.rename(columns={'PRIOR 5': 'Dec 5', 'PRIOR 6': 'Dec 6', 'PRIOR 7': 'Dec 7', 'PRIOR 8': 'Dec 8'}, inplace=True)
        dat2.rename(columns={'PRIOR 9': 'Dec 9', 'Hi PRIOR': 'Dec 10'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)
        dat3=dat2.copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("----------------")
            print("Momentum Strategy")
            print("----------------")
            print("Basic Strategy: stocks are sorted into deciles based on their prior 12-month returns, excluding the most recent month.")
            print()
            print("Construction: The portfolios are constructed monthly using NYSE prior (2-12) return decile breakpoints.")
            print()
            print("Stocks: The portfolios constructed each month include NYSE, AMEX, and NASDAQ stocks with prior return data.")
            print("To be included in a portfolio for month t (formed at the end of month t-1), a stock must have a price for the")
            print("end of month t-13 and a good return for t-2. In addition, any missing returns from t-12 to t-3 must be -99.0,")
            print("CRSP's code for a missing price. Each included stock also must have ME for the end of month t-1.")
            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")


    #------------------------------------------
    elif stype == 'shorttermreversal':

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Portfolios_Prior_1_0_csv.zip"

        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('10_Portfolios_Prior_1_0.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=10, header=0, encoding='utf-8', skipfooter=5, engine='python')

        start_index = dat[dat.iloc[:, 0].str.contains("Equal Weighted Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()

        # Convert all columns except 'date' to numeric types
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)
        dat2.rename(columns={'Lo PRIOR': 'Dec 1', 'PRIOR 2': 'Dec 2', 'PRIOR 3': 'Dec 3', 'PRIOR 4': 'Dec 4', 'PRIOR 5': 'Dec 5',
                             'PRIOR 6': 'Dec 6', 'PRIOR 7': 'Dec 7', 'PRIOR 8': 'Dec 8', 'PRIOR 9': 'Dec 9', 'Hi PRIOR': 'Dec 10'}, inplace=True)
        cols = ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5',
                'Dec 6', 'Dec 7', 'Dec 8', 'Dec 9', 'Dec 10']

        dat3 = dat2[cols].copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("----------------")
            print("Short Term Reversal Strategy")
            print("----------------")
            print("Basic Strategy: stocks are sorted into deciles based on their prior 1-month return.")
            print("Construction: The portfolios are formed on the prior one-month return at the end of each month.")
            print("Each portfolio is value-weighted.")

            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")

    #------------------------------------------
    elif stype == 'accruals':

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_AC_csv.zip"
        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('Portfolios_Formed_on_AC.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=17, header=0, encoding='utf-8', skipfooter=5, engine='python')

        start_index = dat[dat.iloc[:, 0].str.contains("Equal Weighted Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()

        # Convert all columns except 'date' to numeric types
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)
        dat2.rename(columns={'Lo 10': 'Dec 1', 'Hi 10': 'Dec 10'}, inplace=True)
        cols = ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5',
                'Dec 6', 'Dec 7', 'Dec 8', 'Dec 9', 'Dec 10']

        dat3 = dat2[cols].copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("----------------")
            print("Accruals Strategy")
            print("----------------")
            print("The portfolios are formed on Accruals at the end of each June using NYSE breakpoints.")
            print("Accruals for June of year t is the change in operating working capital per split-adjusted share from")
            print("the fiscal year end t-2 to t-1 divided by book equity per share in t-1.")
            print("Stocks are ranked and sorted into deciles. Each decile portfolio is value-weighted.")

            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")


    #------------------------------------------
    elif stype == 'profitability':

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_OP_csv.zip"

        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('Portfolios_Formed_on_OP.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=24, header=0, encoding='utf-8', skipfooter=5, engine='python')

        start_index = dat[dat.iloc[:, 0].str.contains("Equal Weighted Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()

        # Convert all columns except 'date' to numeric types
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)

        dat2.rename(columns={'Lo 10': 'Dec 1', 'Hi 10': 'Dec 10'}, inplace=True)
        dat2.rename(columns={'2-Dec': 'Dec 2', '3-Dec': 'Dec 3', '4-Dec': 'Dec 4', '5-Dec': 'Dec 5', '6-Dec': 'Dec 6', '7-Dec': 'Dec 7', '8-Dec': 'Dec 8', '9-Dec': 'Dec 9'}, inplace=True)

        cols = ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5',
                'Dec 6', 'Dec 7', 'Dec 8', 'Dec 9', 'Dec 10']

        dat3 = dat2[cols].copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("--------------------------------")
            print("Operating Profitability Strategy")
            print("--------------------------------")
            print("The portfolios are formed on profitability (OP) at the end of each June using NYSE breakpoints.")
            print("OP for June of year t is annual revenues minus cost of goods sold, interest expense, and selling,")
            print("general, and administrative expenses divided by book equity for the last fiscal year end in t-1.")


            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")

    #------------------------------------------
    elif stype == 'investment':

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_INV_csv.zip"

        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('Portfolios_Formed_on_INV.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=17, header=0, encoding='utf-8', skipfooter=5, engine='python')

        start_index = dat[dat.iloc[:, 0].str.contains("Equal Weighted Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()

        # Convert all columns except 'date' to numeric types
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)


        dat2.rename(columns={'Lo 10': 'Dec 1', 'Hi 10': 'Dec 10'}, inplace=True)
        dat2.rename(columns={'2-Dec': 'Dec 2', '3-Dec': 'Dec 3', '4-Dec': 'Dec 4', '5-Dec': 'Dec 5', '6-Dec': 'Dec 6', '7-Dec': 'Dec 7', '8-Dec': 'Dec 8', '9-Dec': 'Dec 9'}, inplace=True)

        cols = ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5',
                'Dec 6', 'Dec 7', 'Dec 8', 'Dec 9', 'Dec 10']

        dat3 = dat2[cols].copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("--------------------------------")
            print("Firm Investment")
            print("--------------------------------")

            print("Investment is the change in total assets from the fiscal year ending in year t-2 to the fiscal year")
            print("ending in t-1, divided by t-2 total assets. Deciles are formed using NYSE breakpoints.")

            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")

    #------------------------------------------
    elif stype == 'netissuances':

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_NI_csv.zip"

        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('Portfolios_Formed_on_NI.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=16, header=0, encoding='utf-8', skipfooter=5, engine='python')

        start_index = dat[dat.iloc[:, 0].str.contains("Equal Weighted Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()

        # Convert all columns except 'date' to numeric types
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)


        dat2.rename(columns={'Lo 10': 'Dec 1', 'Hi 10': 'Dec 10'}, inplace=True)
        dat2.rename(columns={'2-Dec': 'Dec 2', '3-Dec': 'Dec 3', '4-Dec': 'Dec 4', '5-Dec': 'Dec 5', '6-Dec': 'Dec 6', '7-Dec': 'Dec 7', '8-Dec': 'Dec 8', '9-Dec': 'Dec 9'}, inplace=True)

        cols = ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5',
                'Dec 6', 'Dec 7', 'Dec 8', 'Dec 9', 'Dec 10']

        dat3 = dat2[cols].copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("--------------------------------")
            print("Net Share Issuances")
            print("--------------------------------")

            print("Decile ortfolios are formed on Net Share Issues (NI) at the end of each June using NYSE breakpoints.")
            print("NI for June of year t is the change in the natural log of split-adjusted shares outstanding from the")
            print("fiscal yearend in t-2 to the fiscal yearend in t-1.")

            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")

    #------------------------------------------
    elif stype == 'booktomarket':

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_BE-ME_csv.zip"

        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('Portfolios_Formed_on_BE-ME.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=23, header=0, encoding='utf-8', skipfooter=5, engine='python')

        start_index = dat[dat.iloc[:, 0].str.contains("Equal Weight Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()

        # Convert all columns except 'date' to numeric types
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)


        dat2.rename(columns={'Lo 10': 'Dec 1', 'Hi 10': 'Dec 10'}, inplace=True)
        dat2.rename(columns={'2-Dec': 'Dec 2', '3-Dec': 'Dec 3', '4-Dec': 'Dec 4', '5-Dec': 'Dec 5', '6-Dec': 'Dec 6', '7-Dec': 'Dec 7', '8-Dec': 'Dec 8', '9-Dec': 'Dec 9'}, inplace=True)

        cols = ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5',
                'Dec 6', 'Dec 7', 'Dec 8', 'Dec 9', 'Dec 10']

        dat3 = dat2[cols].copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("--------------------------------")
            print("Book-to-Market Deciles")
            print("--------------------------------")

            print("Decile portfolios are formed on BE/ME at the end of each June using NYSE breakpoints. The BE used in")
            print("June of year t is the book equity for the last fiscal year end in t-1. ME is price times shares")
            print("outstanding at the end of December of t-1.")

            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")

    #------------------------------------------
    elif stype == 'size':

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_ME_csv.zip"

        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('Portfolios_Formed_on_ME.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=12, header=0, encoding='utf-8', skipfooter=5, engine='python')

        start_index = dat[dat.iloc[:, 0].str.contains("Equal Weighted Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()

        # Convert all columns except 'date' to numeric types
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)


        dat2.rename(columns={'Lo 10': 'Dec 1', 'Hi 10': 'Dec 10'}, inplace=True)
        dat2.rename(columns={'2-Dec': 'Dec 2', '3-Dec': 'Dec 3', '4-Dec': 'Dec 4', '5-Dec': 'Dec 5', '6-Dec': 'Dec 6', '7-Dec': 'Dec 7', '8-Dec': 'Dec 8', '9-Dec': 'Dec 9'}, inplace=True)

        cols = ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5',
                'Dec 6', 'Dec 7', 'Dec 8', 'Dec 9', 'Dec 10']

        dat3 = dat2[cols].copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("--------------------------------")
            print("Size Deciles")
            print("--------------------------------")
            print("Decile portfolios are constructed at the end of each June using the June market equity and ")
            print("NYSE breakpoints.")

            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")
 #-----------------------------------------
    elif stype == 'earningsprice':

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_E-P_csv.zip"

        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('Portfolios_Formed_on_E-P.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=17, header=0, encoding='utf-8', skipfooter=5, engine='python')

        start_index = dat[dat.iloc[:, 0].str.contains("Equal Weight Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()

        # Convert all columns except 'date' to numeric types
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)


        dat2.rename(columns={'Lo 10': 'Dec 1', 'Hi 10': 'Dec 10'}, inplace=True)
        dat2.rename(columns={'2-Dec': 'Dec 2', '3-Dec': 'Dec 3', '4-Dec': 'Dec 4', '5-Dec': 'Dec 5', '6-Dec': 'Dec 6', '7-Dec': 'Dec 7', '8-Dec': 'Dec 8', '9-Dec': 'Dec 9'}, inplace=True)

        cols = ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5',
                'Dec 6', 'Dec 7', 'Dec 8', 'Dec 9', 'Dec 10']

        dat3 = dat2[cols].copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("--------------------------------")
            print("Earnings-Price Deciles")
            print("--------------------------------")

            print("Decile portfolios are formed on E/P at the end of each June using NYSE breakpoints. The")
            print("earnings used in June of year t are total earnings before extraordinary items for the last")
            print("fiscal year end in t-1. P (actually ME) is price times shares outstanding at the end of")
            print("December of t-1.")

            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")
#---------------------------------
    elif stype == 'dividendyield':

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_D-P_csv.zip"

        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('Portfolios_Formed_on_D-P.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=19, header=0, encoding='utf-8', skipfooter=5, engine='python')

        start_index = dat[dat.iloc[:, 0].str.contains("Equal Weight Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()

        # Convert all columns except 'date' to numeric types
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)


        dat2.rename(columns={'Lo 10': 'Dec 1', 'Hi 10': 'Dec 10'}, inplace=True)
        dat2.rename(columns={'2-Dec': 'Dec 2', '3-Dec': 'Dec 3', '4-Dec': 'Dec 4', '5-Dec': 'Dec 5', '6-Dec': 'Dec 6', '7-Dec': 'Dec 7', '8-Dec': 'Dec 8', '9-Dec': 'Dec 9'}, inplace=True)

        cols = ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5',
                'Dec 6', 'Dec 7', 'Dec 8', 'Dec 9', 'Dec 10']

        dat3 = dat2[cols].copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("--------------------------------")
            print("Dividend-Yield Deciles")
            print("--------------------------------")

            print("Portfolios are formed on D/P at the end of each June using NYSE breakpoints. The dividend")
            print("yield used to form portfolios in June of year t is the total dividends paid from July of")
            print("year t-1 to June of year t per dollar of equity in June of t.")

            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")

#-----------------------------------
    elif stype == 'variance':

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_VAR_csv.zip"

        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('Portfolios_Formed_on_VAR.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=16, header=0, encoding='utf-8', skipfooter=5, engine='python')

        start_index = dat[dat.iloc[:, 0].str.contains("Equal Weighted Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()

        # Convert all columns except 'date' to numeric types
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)


        dat2.rename(columns={'Lo 10': 'Dec 1', 'Hi 10': 'Dec 10'}, inplace=True)
        dat2.rename(columns={'2-Dec': 'Dec 2', '3-Dec': 'Dec 3', '4-Dec': 'Dec 4', '5-Dec': 'Dec 5', '6-Dec': 'Dec 6', '7-Dec': 'Dec 7', '8-Dec': 'Dec 8', '9-Dec': 'Dec 9'}, inplace=True)

        cols = ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5',
                'Dec 6', 'Dec 7', 'Dec 8', 'Dec 9', 'Dec 10']

        dat3 = dat2[cols].copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("--------------------------------")
            print("Variance Deciles")
            print("--------------------------------")

            print("Decile portfolios are formed monthly on the variance of daily returns (Var) using NYSE ")
            print("breakpoints. Var is estimated using 60 days (minimum 20) of lagged returns.")

            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")

#-------------------------------------------
    elif stype == 'idiosyncraticvariance':

        # Make the request using the session
        url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_RESVAR_csv.zip"

        session = requests.Session()

        retry = Retry(total=5, connect=5, read=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        r = session.get(url, timeout=60)
        r.raise_for_status()

        # Open the zip file from the content
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open('Portfolios_Formed_on_RESVAR.csv') as f:
                # Read the CSV file content (you can load it into pandas or process as needed)
                dat = pd.read_csv(f, skiprows=16, header=0, encoding='utf-8', skipfooter=5, engine='python')

        start_index = dat[dat.iloc[:, 0].str.contains("Equal Weighted Returns -- Monthly", na=False)].index[0]
        dat1 = dat.iloc[:start_index]
        dat2 = dat1.copy()
        dat2.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

        # Convert first column to Period
        dat2['date'] = pd.to_datetime(dat2['date'].astype(str), format='%Y%m').dt.to_period()

        # Convert all columns except 'date' to numeric types
        for col in dat2.columns[1:]:  # Skip the 'date' column
            dat2[col] = pd.to_numeric(dat2[col], errors='coerce')

        dat2.iloc[:, 1:] = dat2.iloc[:, 1:] * 0.01

        # reset the index
        dat2.set_index('date', inplace=True)


        dat2.rename(columns={'Lo 10': 'Dec 1', 'Hi 10': 'Dec 10'}, inplace=True)
        dat2.rename(columns={'2-Dec': 'Dec 2', '3-Dec': 'Dec 3', '4-Dec': 'Dec 4', '5-Dec': 'Dec 5', '6-Dec': 'Dec 6', '7-Dec': 'Dec 7', '8-Dec': 'Dec 8', '9-Dec': 'Dec 9'}, inplace=True)

        cols = ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5',
                'Dec 6', 'Dec 7', 'Dec 8', 'Dec 9', 'Dec 10']

        dat3 = dat2[cols].copy()  # Select relevant columns
        dat3.index = dat2.index  # Keep the index (assumed to be a PeriodIndex)
        if details is True:
            print("--------------------------------")
            print("Idiosyncratic Variance Deciles")
            print("--------------------------------")

            print("The portfolios are formed monthly on the variance of the residuals from the FF ")
            print("three-factor model (RVar) using NYSE breakpoints. RVar is estimated using 60 days")
            print("(minimum 20) of lagged returns.")

            min_date = dat3.index.min()
            max_date = dat3.index.max()
            print()
            print(f"Min Date: {min_date}, Max Date: {max_date}")



    else:
        raise ValueError("Invalid strategy type. Choose 'accruals', 'beta', 'booktomarket', 'dividendyield',"
                         "'earningsprice','idiosyncraticvariance', 'investment', 'momentum', 'netissuances', "
                         "profitability, 'shorttermreversal', 'size', or 'variance'.")

    #------------------------------------------
    # Apply date range filtering if provided
    if start_date is not None:
        dat3 = dat3[dat3.index >= pd.Period(start_date, freq='M')]
    if end_date is not None:
        dat3 = dat3[dat3.index <= pd.Period(end_date, freq='M')]

    # merge in either FF3 or FF5
    if factors=='FF5':
        ff5=get_ff5()
        ff5.rename(columns={'Mkt-RF':'mkt-rf', 'SMB':'smb', 'HML':'hml', 'RMW': 'rmw', 'CMA': 'cma', 'RF':'rf'}, inplace=True)
        dat_final = pd.merge(dat3, ff5[['mkt-rf', 'smb', 'hml', 'rmw', 'cma', 'rf']], left_index=True, right_index=True, how='inner')
    elif factors=='FF3':
        ff3 = get_ff3()
        ff3.rename(columns={'Mkt-RF': 'mkt-rf', 'SMB': 'smb', 'HML': 'hml', 'RF': 'rf'}, inplace=True)
        dat_final = pd.merge(dat3, ff3[['mkt-rf', 'smb', 'hml', 'rf']], left_index=True, right_index=True, how='inner')
    else:
        ff3=get_ff3()
        ff3.rename(columns={'Mkt-RF':'mkt-rf', 'SMB':'smb', 'HML':'hml', 'RF':'rf'},inplace=True)
        dat_final=pd.merge(dat3,ff3[['mkt-rf','rf']],left_index=True,right_index=True,how='inner')

    return dat_final

