"""Week 2: a simple model, tested honestly on weeks it has never seen.

The model, in one line:
    this week's rate = last week's rate + slope x (how much the 10-year moved since last week) + intercept

It starts from the naive guess and adjusts it by the Treasury move. The slope answers
"when the 10-year moves 0.10 points, how much does the mortgage rate move?" Working in weekly
changes, not levels, means the model doesn't care that the spread widened after 2022.

The honest test ("walk-forward"): for every week from 2020 on, fit the model using only the
weeks before it, then predict that week. That is exactly what you could have done in real time.
No week is ever predicted by a model that saw it.

Two versions, both chosen before looking at any test results:
- Expanding: fit on all history up to that week.
- Rolling 2-year: fit on only the last 104 weeks, so it can adapt if the relationship drifts.

"Fast bond weeks" are weeks where the 10-year moved more than it did in 3 out of 4 weeks
from 2000 to 2019. The cutoff comes from the years before the test, so it isn't tuned to it.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # save charts to files instead of opening windows
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from explore import load, weekly_table

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
TEST_START = pd.Timestamp("2020-01-01")
ROLLING_WEEKS = 104


def walk_forward(weekly: pd.DataFrame, window: int | None = None) -> pd.DataFrame:
    """Predict every test week with a model fit only on the weeks before it."""
    rows = []
    for i in weekly.index[weekly["date"] >= TEST_START]:
        train = weekly.loc[: i - 1]
        if window:
            train = train.tail(window)
        slope, intercept = np.polyfit(train["tsy10_change"], train["rate_change"], 1)
        week = weekly.loc[i]
        rows.append({
            "date": week["date"],
            "prediction": week["last_week_rate"] + intercept + slope * week["tsy10_change"],
            "slope": slope,
        })
    return pd.DataFrame(rows)


def mae(actual: pd.Series, predicted: pd.Series) -> float:
    """Average miss in percentage points."""
    return (actual - predicted).abs().mean()


def build_results(weekly: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    expanding = walk_forward(weekly)
    rolling = walk_forward(weekly, ROLLING_WEEKS)

    test = weekly[weekly["date"] >= TEST_START].reset_index(drop=True)
    results = test[["date", "mortgage_rate", "last_week_rate", "tsy10_3day", "tsy10_change"]].copy()
    results["naive"] = results["last_week_rate"]
    results["model_expanding"] = expanding["prediction"].values
    results["model_rolling"] = rolling["prediction"].values
    results["slope_expanding"] = expanding["slope"].values
    results["slope_rolling"] = rolling["slope"].values

    history = weekly[weekly["date"] < TEST_START]
    cutoff = history["tsy10_change"].abs().quantile(0.75)
    results["fast_bond_week"] = results["tsy10_change"].abs() > cutoff
    return results, cutoff


def scorecard(results: pd.DataFrame, label: str) -> str:
    actual = results["mortgage_rate"]
    naive = mae(actual, results["naive"])
    exp = mae(actual, results["model_expanding"])
    roll = mae(actual, results["model_rolling"])
    beat = ((actual - results["model_rolling"]).abs() < (actual - results["naive"]).abs()).mean()
    return (
        f"{label} ({len(results)} weeks): naive {naive:.3f} | expanding {exp:.3f} "
        f"({1 - exp / naive:.0%} better) | rolling 2-yr {roll:.3f} ({1 - roll / naive:.0%} better) | "
        f"rolling beats naive in {beat:.0%} of weeks"
    )


def charts(results: pd.DataFrame) -> None:
    OUT.mkdir(exist_ok=True)
    recent = results[results["date"] >= results["date"].max() - pd.DateOffset(years=2)]

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(recent["date"], recent["mortgage_rate"], label="Actual (Freddie Mac)", color="black")
    ax.plot(recent["date"], recent["model_rolling"], label="Model forecast (made before release)", color="tab:blue", alpha=0.8)
    ax.set_ylabel("Percent")
    ax.set_title("30-year mortgage rate: model forecast vs actual, last 2 years")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "week2_forecast_vs_actual.png", dpi=120)
    plt.close(fig)

    by_year = results.groupby(results["date"].dt.year).apply(
        lambda g: pd.Series({
            "Naive (same as last week)": mae(g["mortgage_rate"], g["naive"]),
            "Model (rolling 2-year)": mae(g["mortgage_rate"], g["model_rolling"]),
        }),
        include_groups=False,
    )
    ax = by_year.plot.bar(figsize=(11, 4.5), color=["tab:gray", "tab:blue"], rot=0)
    ax.set_ylabel("Average miss (percentage points)")
    ax.set_xlabel("")
    ax.set_title("Average weekly miss by year, on weeks the model never saw")
    ax.grid(alpha=0.3, axis="y")
    ax.figure.tight_layout()
    ax.figure.savefig(OUT / "week2_error_by_year.png", dpi=120)
    plt.close(ax.figure)


def main() -> None:
    mortgage, treasury = load()
    weekly = weekly_table(mortgage, treasury)
    results, cutoff = build_results(weekly)

    last2 = results[results["date"] >= results["date"].max() - pd.DateOffset(years=2)]
    lines = [
        f"Test period: {results['date'].min().date()} to {results['date'].max().date()}, every week predicted using only earlier weeks",
        scorecard(results, "All test weeks"),
        scorecard(last2, "Last 2 years"),
        scorecard(results[results["date"].dt.year == 2022], "2022 (bond sell-off)"),
        f"Fast bond weeks = 10-year moved more than {cutoff:.3f} pts (75th percentile, 2000-2019):",
        scorecard(results[results["fast_bond_week"]], "  Fast bond weeks"),
        scorecard(results[~results["fast_bond_week"]], "  Calm weeks"),
        f"Latest slope (rolling 2-yr): a 0.10 move in the 10-year moves the mortgage rate {results['slope_rolling'].iloc[-1] * 0.10:.3f} pts",
        "",
        "Most recent weeks (actual vs forecasts):",
    ]
    for _, r in results.tail(6).iterrows():
        lines.append(
            f"  {r['date'].date()}  actual {r['mortgage_rate']:.2f} | naive {r['naive']:.2f} | "
            f"model {r['model_rolling']:.2f} | 10-yr moved {r['tsy10_change']:+.2f}"
        )

    OUT.mkdir(exist_ok=True)
    (OUT / "week2_summary.txt").write_text("\n".join(lines) + "\n")
    results.to_csv(OUT / "week2_predictions.csv", index=False)
    charts(results)
    print("\n".join(lines))
    print("Charts and predictions saved to outputs/")


if __name__ == "__main__":
    main()
