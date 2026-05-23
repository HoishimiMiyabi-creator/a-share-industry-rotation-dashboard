from __future__ import annotations

import pandas as pd


def calculate_industry_scores(history: pd.DataFrame) -> pd.DataFrame:
    """Calculate momentum, risk, drawdown, turnover, and composite scores."""
    required_columns = {
        "industry",
        "date",
        "close",
    }
    missing = required_columns.difference(history.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    rows: list[dict[str, object]] = []
    for industry, group in history.groupby("industry", sort=False):
        frame = group.sort_values("date").dropna(subset=["close"]).copy()
        if len(frame) < 2:
            continue

        close = frame["close"].astype(float)
        returns = close.pct_change().dropna()
        amount = (
            frame["amount"].astype(float)
            if "amount" in frame.columns
            else pd.Series(dtype="float64")
        )

        rows.append(
            {
                "industry": industry,
                "latest_date": frame["date"].max().date().isoformat(),
                "latest_close": close.iloc[-1],
                "return_20d": _period_return(close, 20),
                "return_60d": _period_return(close, 60),
                "volatility_20d": returns.tail(20).std() if not returns.empty else 0.0,
                "max_drawdown_60d": _max_drawdown(close.tail(60)),
                "turnover_change": _amount_change(amount),
                "history_days": len(frame),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "rank",
                "industry",
                "score",
                "latest_date",
                "latest_close",
                "return_20d",
                "return_60d",
                "volatility_20d",
                "max_drawdown_60d",
                "turnover_change",
                "history_days",
            ]
        )

    scores = pd.DataFrame(rows)
    scores["score"] = (
        scores["return_20d"] * 0.35
        + scores["return_60d"] * 0.35
        + scores["turnover_change"] * 0.20
        - scores["volatility_20d"].fillna(0) * 0.05
        + scores["max_drawdown_60d"] * 0.05
    )
    scores["rank"] = scores["score"].rank(ascending=False, method="first").astype(int)

    columns = [
        "rank",
        "industry",
        "score",
        "latest_date",
        "latest_close",
        "return_20d",
        "return_60d",
        "volatility_20d",
        "max_drawdown_60d",
        "turnover_change",
        "history_days",
    ]
    return scores.sort_values("rank")[columns]


def _period_return(close: pd.Series, window: int) -> float:
    if len(close) <= window:
        first = close.iloc[0]
    else:
        first = close.iloc[-window - 1]
    if first == 0:
        return 0.0
    return float(close.iloc[-1] / first - 1)


def _max_drawdown(close: pd.Series) -> float:
    if close.empty:
        return 0.0
    running_max = close.cummax()
    drawdown = close / running_max - 1
    return float(drawdown.min())


def _amount_change(amount: pd.Series) -> float:
    amount = amount.dropna()
    if len(amount) < 10:
        return 0.0
    recent = amount.tail(5).mean()
    baseline = amount.tail(20).mean() if len(amount) >= 20 else amount.mean()
    if baseline == 0:
        return 0.0
    return float(recent / baseline - 1)
