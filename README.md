# A-share Industry Rotation Dashboard

This is a resume-oriented data project for monitoring A-share industry rotation.

## Goal

Build a small Streamlit dashboard that ranks industries by momentum, risk, drawdown,
and turnover activity. The project is for learning and research only.

## Current Status

- Python environment: `.venv-win313`
- Python version: 3.13.13
- App framework: Streamlit
- Data stack: pandas, AKShare, Plotly, PyArrow
- Current app: runnable prototype with sample data

## Run Locally

```powershell
cd D:\codex\简历\a-share-industry-rotation-dashboard
.\.venv-win313\Scripts\Activate.ps1
python -m streamlit run app.py
```

## Project Structure

```text
.
├── app.py
├── requirements.txt
├── src
│   ├── __init__.py
│   ├── backtest.py
│   ├── data_loader.py
│   ├── metrics.py
│   └── report.py
└── README.md
```

## Disclaimer

This project is only for learning, research, and portfolio demonstration. It does
not provide investment advice, trading signals, or securities consulting services.
