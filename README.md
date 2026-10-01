# Mortgage Rate Forecaster

**Question:** Using U.S. Treasury yields known by Wednesday, can I predict Freddie Mac's 30-year fixed mortgage rate (published every Thursday) better than the simple guess of "same as last week"?

**Why this question:** Every Thursday, Freddie Mac publishes the average 30-year mortgage rate from its Primary Mortgage Market Survey (PMMS), based on lender quotes from Monday to Wednesday of that week. Mortgage rates tend to follow the 10-year Treasury yield, which is published daily. If that relationship is strong enough, the yields from Monday to Wednesday should let me estimate Thursday's number before it comes out.

## Data (public, from FRED at the St. Louis Fed)
| Series | What it is | Frequency |
|---|---|---|
| `MORTGAGE30US` | Freddie Mac 30-year fixed mortgage rate (PMMS) | Weekly (Thursdays) |
| `DGS10` | 10-year U.S. Treasury yield | Daily (business days) |

History used: 2000 to today.

**Data note:** Freddie Mac published on Fridays from 2000 to 2003, Thursdays since 2004, and often Wednesdays in holiday weeks. So each rate is matched to the average 10-year yield over the **3 trading days before its own release date**, rather than assuming Monday to Wednesday.

## Plan
| Week | Goal | Status |
|---|---|---|
| 1 | Pull the data, line it up week by week, measure the baseline to beat | Done |
| 2 | Build a simple model and test it honestly on recent years it hasn't seen | |
| 3 | Power BI dashboard + write-up of results | |
| 4–5 | Automate the weekly update in the cloud (AWS Lambda), polish, lessons learned | |

## Week 1 results
- 1,394 weeks lined up (2000 to Sept 2026).
- **Baseline to beat:** guessing "same as last week" misses by 0.067 percentage points per week on average (0.056 over the last 2 years).
- Weekly changes in the mortgage rate and the 10-year yield have a correlation of 0.76, so there's real signal to work with.
- The spread (mortgage rate minus 10-year yield) averaged 1.89 points historically but 2.19 over the last 2 years. It widened, and the model has to handle that.

## How to run
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/fetch_data.py
python src/explore.py
```
