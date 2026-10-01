"""Download the two FRED series this project uses and save them to data/raw/.

MORTGAGE30US: Freddie Mac's 30-year fixed mortgage rate (weekly, published Thursdays).
DGS10: 10-year U.S. Treasury yield (daily, business days only).

No API key needed here: FRED serves these as public CSV downloads.
(Week 2 switches to the FRED API with a free key so the pull can run automatically.)
"""
from pathlib import Path

import pandas as pd

SERIES = ["MORTGAGE30US", "DGS10"]
START = "2000-01-01"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def fetch(series_id: str) -> pd.DataFrame:
    """Download one FRED series as a two-column table: date, value."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={START}"
    # FRED marks missing days (like bond-market holidays) with "." so treat that as empty.
    df = pd.read_csv(url, na_values=".")
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"])
    return df.dropna()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for series_id in SERIES:
        df = fetch(series_id)
        out = RAW_DIR / f"{series_id}.csv"
        df.to_csv(out, index=False)
        print(f"{series_id}: {len(df):,} rows, {df['date'].min().date()} to {df['date'].max().date()} -> data/raw/{out.name}")


if __name__ == "__main__":
    main()
