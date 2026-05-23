# A-share Industry Rotation Dashboard

This is a resume-oriented data project for monitoring A-share industry rotation.

## Goal

Build a small Streamlit dashboard that ranks industries by momentum, risk,
drawdown, and turnover activity. The project is for learning and research only.

## Current Status

- Python environment: `.venv-win313`
- Python version: 3.13.13
- App framework: Streamlit
- Data stack: pandas, AKShare, Plotly, PyArrow
- Current app: AKShare-powered industry-board dashboard

## Data Source

- Industry snapshot: `akshare.stock_board_industry_name_em()`
- Industry history: `akshare.stock_board_industry_hist_em()`
- Cache policy: Streamlit `st.cache_data(ttl=3600)`

The dashboard keeps the first version responsive by fetching historical data
only for a configurable subset of industries.

## Metrics

The industry ranking currently uses:

- 20-day return
- 60-day return
- Annualized 20-day volatility
- 60-day maximum drawdown
- Recent amount change, measured as recent 5-day average amount versus the
  previous available baseline window
- Composite score, built from cross-sectional z-scores and scaled to 0-100
- Industry rank, sorted by composite score in descending order

The composite score weights are:

| Factor | Weight | Direction |
|---|---:|---|
| 20-day return z-score | 30% | Higher is better |
| 60-day return z-score | 25% | Higher is better |
| Amount-change z-score | 20% | Higher is better |
| 60-day max-drawdown z-score | 15% | Higher is better, meaning less negative drawdown |
| 20-day volatility z-score | -10% | Lower is better |

## Run Locally

```powershell
cd <project-path>
.\.venv-win313\Scripts\Activate.ps1
python -m streamlit run app.py
```

## Project Structure

```text
.
|-- app.py
|-- requirements.txt
|-- src
|   |-- __init__.py
|   |-- backtest.py
|   |-- data_loader.py
|   |-- metrics.py
|   `-- report.py
`-- README.md
```

## Disclaimer

This project is only for learning, research, and portfolio demonstration. It does
not provide investment advice, trading signals, or securities consulting services.
