"""Week 1: line the two series up week by week and measure the baseline to beat.

Freddie Mac's weekly rate is built from lender quotes collected in the days before it's published.
So for each release, the fair input is the 10-year yield averaged over the 3 trading days
just before the release date: information you'd actually have the night before.

Why "3 trading days before" instead of "Monday-Wednesday": the release day isn't always Thursday.
From 2000 to 2003 Freddie Mac published on Fridays, and holiday weeks often publish on Wednesday.
Anchoring to each release's own date lines every week up correctly.

Baseline ("naive") forecast: this week's rate = last week's rate.
Any model we build in week 3 has to beat this number to be worth anything.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # save charts to files instead of opening windows
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    mortgage = pd.read_csv(RAW / "MORTGAGE30US.csv", parse_dates=["date"])
    treasury = pd.read_csv(RAW / "DGS10.csv", parse_dates=["date"])
    return mortgage, treasury


def weekly_table(mortgage: pd.DataFrame, treasury: pd.DataFrame) -> pd.DataFrame:
    """One row per release: the mortgage rate, last week's rate, and the 10-year yield averaged
    over the 3 trading days before the release."""
    yields = treasury.set_index("date")["DGS10"].sort_index()
    rows = []
    for release_date, rate in zip(mortgage["date"], mortgage["MORTGAGE30US"]):
        # The last 3 trading days strictly before the release date, whatever weekday it falls on.
        window = yields[yields.index < release_date].tail(3)
        # Skip if the data has a gap (e.g., the 3 days reach back more than a week).
        if len(window) < 3 or window.index.min() < release_date - pd.Timedelta(days=7):
            continue
        rows.append({"date": release_date, "mortgage_rate": rate, "tsy10_3day": window.mean()})

    weekly = pd.DataFrame(rows)
    weekly["last_week_rate"] = weekly["mortgage_rate"].shift(1)
    weekly["spread"] = weekly["mortgage_rate"] - weekly["tsy10_3day"]
    weekly["rate_change"] = weekly["mortgage_rate"].diff()
    weekly["tsy10_change"] = weekly["tsy10_3day"].diff()
    return weekly.dropna().reset_index(drop=True)


def baseline_error(weekly: pd.DataFrame) -> float:
    """Average miss (in percentage points) of guessing 'same as last week'."""
    return (weekly["mortgage_rate"] - weekly["last_week_rate"]).abs().mean()


def charts(weekly: pd.DataFrame) -> None:
    OUT.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(weekly["date"], weekly["mortgage_rate"], label="30-year mortgage rate (Freddie Mac)")
    ax.plot(weekly["date"], weekly["tsy10_3day"], label="10-year Treasury yield (3 trading days before release)")
    ax.set_ylabel("Percent")
    ax.set_title("Mortgage rates follow the 10-year Treasury yield")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "week1_rates.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(weekly["date"], weekly["spread"], color="tab:purple")
    ax.set_ylabel("Percentage points")
    ax.set_title("Spread: mortgage rate minus 10-year yield")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "week1_spread.png", dpi=120)
    plt.close(fig)


def main() -> None:
    mortgage, treasury = load()
    weekly = weekly_table(mortgage, treasury)
    recent = weekly[weekly["date"] >= weekly["date"].max() - pd.DateOffset(years=2)]

    lines = [
        f"Weeks lined up: {len(weekly):,} ({weekly['date'].min().date()} to {weekly['date'].max().date()})",
        f"Baseline miss, all history: {baseline_error(weekly):.3f} percentage points per week",
        f"Baseline miss, last 2 years: {baseline_error(recent):.3f} percentage points per week",
        f"Correlation of weekly changes (mortgage rate vs 10-year yield): {weekly['rate_change'].corr(weekly['tsy10_change']):.2f}",
        f"Average spread (mortgage minus 10-year): {weekly['spread'].mean():.2f} pts, last 2 years: {recent['spread'].mean():.2f} pts",
    ]
    OUT.mkdir(exist_ok=True)
    (OUT / "week1_summary.txt").write_text("\n".join(lines) + "\n")
    weekly.to_csv(ROOT / "data" / "weekly.csv", index=False)
    charts(weekly)
    print("\n".join(lines))
    print("Charts saved to outputs/")


if __name__ == "__main__":
    main()
