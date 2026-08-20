import re
from numbers import Integral
from typing import Iterable, List, Literal, Union

import pandas as pd


_RESULT_COLUMNS = [
    "permno",
    "permco",
    "ticker",
    "comnam",
    "shrcd",
    "exchcd",
    "siccd",
    "prc",
    "ret",
    "retx",
    "vol",
    "shrout",
]


def get_crsp_msf_by_ids(
    db,
    identifiers: Iterable[Union[str, int]],
    start_date: str,
    end_date: str,
    chunk_size: int = 500,
    identifier_type: Literal["permno", "ticker"] | None = None,
) -> pd.DataFrame:

    """
    Pull CRSP Monthly Stock File (msf) data for either a list of TICKERS or PERMNOs.

    Parameters
    ----------
    identifiers : iterable of str|int
        Either all tickers (e.g., ['AAPL','MSFT']) or all PERMNOs (e.g., [14593, 12079]).
        Mixed types are not allowed when ``identifier_type`` is omitted.
    identifier_type : {'permno', 'ticker'}, optional
        Explicitly select how to interpret ``identifiers``. When omitted, the
        type is inferred only from a homogeneous list of integers or strings.
    start_date, end_date : 'YYYY-MM-DD'
        Inclusive date range to filter `a.date`.
    chunk_size : int
        Max identifiers per SQL IN() chunk to avoid overly long queries.

    Returns
    -------
    pandas.DataFrame
        Columns: date, permno, ticker, comnam, shrcd, exchcd, siccd, prc, ret, retx, vol, shrout
    """
    
    # Establish the connection object
    con = db.connection
    if hasattr(con, "connection"):
        con = con.connection
    
    if (
        not isinstance(chunk_size, Integral)
        or isinstance(chunk_size, bool)
        or chunk_size <= 0
    ):
        raise ValueError("chunk_size must be a positive integer.")

    # CRSP msf is monthly data, so use an unambiguous month-only API.
    if not all(
        isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}", value)
        for value in (start_date, end_date)
    ):
        raise ValueError("start_date and end_date must be in 'YYYY-MM' format.")

    try:
        start = pd.Period(start_date, freq="M").to_timestamp(how="start")
        end = pd.Period(end_date, freq="M").to_timestamp(how="end")
    except ValueError as error:
        raise ValueError("start_date and end_date must be in 'YYYY-MM' format.") from error

    if start > end:
        raise ValueError("start_date must not be after end_date.")

    # Normalize identifiers and auto-detect type
    ids_list: List[Union[str, int]] = list(identifiers)
    if not ids_list:
        raise ValueError("identifiers list is empty.")

    def is_permno_value(value: object) -> bool:
        return (
            isinstance(value, Integral)
            and not isinstance(value, bool)
        ) or (isinstance(value, str) and value.strip().isdigit())

    if identifier_type is not None and identifier_type not in {"permno", "ticker"}:
        raise ValueError("identifier_type must be either 'permno' or 'ticker'.")

    if identifier_type is None:
        all_integers = all(
            isinstance(value, Integral) and not isinstance(value, bool)
            for value in ids_list
        )
        all_strings = all(isinstance(value, str) for value in ids_list)

        if all_integers:
            id_type = "permno"
        elif all_strings:
            id_type = "permno" if all(is_permno_value(value) for value in ids_list) else "ticker"
        else:
            raise ValueError(
                "Mixed identifier types are ambiguous; pass identifier_type explicitly."
            )
    else:
        id_type = identifier_type

    if id_type == "permno":
        if not all(is_permno_value(value) for value in ids_list):
            raise ValueError("PERMNO identifiers must be integers or digit-only strings.")
        ids_list = [int(value) for value in ids_list]
        if any(value <= 0 for value in ids_list):
            raise ValueError("PERMNO identifiers must be positive integers.")
    else:
        if not all(isinstance(value, str) for value in ids_list):
            raise ValueError("Ticker identifiers must be strings.")
        ids_list = [value.strip().upper() for value in ids_list]
        if any(not value for value in ids_list):
            raise ValueError("Ticker identifiers must not be empty.")
        # Basic sanity: forbid quotes to keep the simple IN (...) builder safe
        if any("'" in value or '"' in value for value in ids_list):
            raise ValueError("Tickers must not contain quotes.")

    # Base SELECT/JOIN and date validity join to msenames
    base_sql = """
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
          AND a.date BETWEEN %s AND %s
    """

    # Build WHERE clause chunks
    def chunk(seq, n):
        for i in range(0, len(seq), n):
            yield seq[i:i+n]

    dfs = []

    for sub in chunk(ids_list, chunk_size):
        placeholders = ", ".join(["%s"] * len(sub))
        if id_type == "permno":
            where_ids = f" AND a.permno IN ({placeholders})"
        else:
            where_ids = f" AND b.ticker IN ({placeholders})"

        sql = base_sql + where_ids
        params = [start, end, *sub]
        dfs.append(pd.read_sql_query(sql, con, params=params))

    out = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    if out.empty:
        out = pd.DataFrame(columns=_RESULT_COLUMNS)
        out.index = pd.PeriodIndex([], freq="M", name="date")
        return out

    out = out.sort_values(["date", "permno"]).reset_index(drop=True).copy()
    out.loc[:, "date"] = pd.to_datetime(out["date"]).dt.to_period("M")
    out.index = pd.PeriodIndex(out["date"], freq="M", name="date")
    return out.drop(columns=["date"])
