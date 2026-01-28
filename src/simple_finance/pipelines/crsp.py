import pandas as pd
from typing import Iterable, List, Union


def get_crsp_msf_by_ids(
    db,
    identifiers: Iterable[Union[str, int]],
    start_date: str,
    end_date: str,
    chunk_size: int = 500
) -> pd.DataFrame:

    """
    Pull CRSP Monthly Stock File (msf) data for either a list of TICKERS or PERMNOs.

    Parameters
    ----------
    identifiers : iterable of str|int
        Either all tickers (e.g., ['AAPL','MSFT']) or all PERMNOs (e.g., [14593, 12079]).
        Mixed types are not allowed.
    start_date, end_date : 'YYYY-MM-DD'
        Inclusive date range to filter `a.date`.
    chunk_size : int
        Max identifiers per SQL IN() chunk to avoid overly long queries.

    Returns
    -------
    pandas.DataFrame
        Columns: date, permno, ticker, comnam, shrcd, exchcd, siccd, prc, ret, retx, vol, shrout
    """
    # --- Normalize date inputs ---
    
    con = db.connection
    # unwrap SQLAlchemy Connection -> ConnectionFairy (has cursor)
    if hasattr(con, "connection"):
        con = con.connection
    
    try:
        start = pd.Period(start_date, freq="M").to_timestamp(how="start")
        end = pd.Period(end_date, freq="M").to_timestamp(how="end")
    except Exception:
        raise ValueError("start_date and end_date must be in 'YYYY-MM' format.")

    # Normalize identifiers and auto-detect type
    ids_list: List[Union[str, int]] = list(identifiers)
    if not ids_list:
        raise ValueError("identifiers list is empty.")

    # If everything looks numeric (ints or numeric strings), treat as PERMNOs; else, tickers.
    def is_numeric_like(x):
        if isinstance(x, int):
            return True
        if isinstance(x, str):
            return x.strip().isdigit()
        return False

    all_numeric_like = all(is_numeric_like(x) for x in ids_list)
    if all_numeric_like:
        id_type = "permno"
        # Cast all to int
        ids_list = [int(x) for x in ids_list]
    else:
        id_type = "ticker"
        # Upper-case tickers and strip spaces
        ids_list = [str(x).strip().upper() for x in ids_list]
        # Basic sanity: forbid quotes to keep the simple IN (...) builder safe
        if any("'" in t or '"' in t for t in ids_list):
            raise ValueError("Tickers must not contain quotes.")

    # Base SELECT/JOIN and date validity join to msenames
    base_sql = f"""
        SELECT 
            a.date, 
            a.permno,
            a.permco, 
            b.ticker, 
            b.comnam, 
            b.shrcd, 
            b.exchcd, 
            b.siccd, 
            a.prc, 
            a.ret, 
            a.retx, 
            a.vol, 
            a.shrout
        FROM crspm.msf a
        INNER JOIN crspm.msenames b
            ON a.permno = b.permno
        WHERE a.date >= b.namedt 
          AND a.date <= b.nameendt
          AND a.date BETWEEN '{start:%Y-%m-%d}' AND '{end:%Y-%m-%d}'
    """

    # Build WHERE clause chunks
    def chunk(seq, n):
        for i in range(0, len(seq), n):
            yield seq[i:i+n]

    dfs = []

    for sub in chunk(ids_list, chunk_size):
        if id_type == "permno":
            # numeric IN list
            id_str = ",".join(str(x) for x in sub)
            where_ids = f" AND a.permno IN ({id_str})"
        else:
            # quoted text IN list
            id_str = ",".join(f"'{x}'" for x in sub)
            where_ids = f" AND b.ticker IN ({id_str})"

        sql = base_sql + where_ids
        dfs.append(pd.read_sql_query(sql, con))

    out = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    # Optional: sort the result
    if not out.empty:
        out = out.sort_values(["permno", "date"]).reset_index(drop=True)
        out['date'] = pd.to_datetime(out['date'])  # ensure that date is a datetime object
        out['date'] = out['date'].dt.to_period("M")
        out = out.set_index('date')
    return out