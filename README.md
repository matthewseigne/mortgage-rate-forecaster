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
| 1 | Pull the data, line it up week by week, measure the baseline to beat | In progress |
| 2 | Automate the weekly data pull in the cloud (AWS Lambda) | |
| 3 | Build and honestly test a model against the baseline | |
| 4 | Power BI dashboard + write-up | |
| 5 | Polish, results, lessons learned | |

## How to run
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/fetch_data.py
python src/explore.py
```
