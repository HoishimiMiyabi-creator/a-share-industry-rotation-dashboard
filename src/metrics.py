from __future__ import annotations

import math

import pandas as pd


TRADING_DAYS_PER_YEAR = 252
SCORE_WEIGHTS = {
    "return_20d_z": 0.30,
    "return_60d_z": 0.25,
    "turnover_change_z": 0.20,
    "max_drawdown_60d_z": 0.15,
    "volatility_20d_z": -0.10,
}


def calculate_industry_scores(history: pd.DataFrame) -> pd.DataFrame:
    """Calculate real industry metrics and a cross-sectional composite ranking.

    The raw metrics are calculated from each industry's historical close and
    amount series. The composite score is based on cross-sectional z-scores so
    indicators with different units can be combined more defensibly.
    """
    if history.empty:
        return _empty_score_frame()

    required_columns = {"industry", "date", "close"}
    missing = required_columns.difference(history.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    metrics = _calculate_raw_metrics(history)
    if metrics.empty:
        return _empty_score_frame()

    scored = _add_standardized_scores(metrics)
    scored["rank"] = scored["score"].rank(ascending=False, method="first").astype(int)

    columns = [
        "rank",
        "industry",
        "score",
        "raw_score",
        "latest_date",
        "latest_close",
        "return_20d",
        "return_60d",
        "volatility_20d",
        "max_drawdown_60d",
        "turnover_change",
        "history_days",
    ]
    return scored.sort_values("rank")[columns].reset_index(drop=True)


def _calculate_raw_metrics(history: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    normalized = history.copy()
    normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")
    normalized["close"] = pd.to_numeric(normalized["close"], errors="coerce")
    if "amount" in normalized.columns:
        normalized["amount"] = pd.to_numeric(normalized["amount"], errors="coerce")

    for industry, group in normalized.groupby("industry", sort=False):
        frame = group.sort_values("date").dropna(subset=["date", "close"]).copy()
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
                "volatility_20d": _annualized_volatility(returns, 20),
                "max_drawdown_60d": _max_drawdown(close.tail(60)),
                "turnover_change": _amount_change(amount),
                "history_days": len(frame),
            }
        )

    return pd.DataFrame(rows)


def _add_standardized_scores(metrics: pd.DataFrame) -> pd.DataFrame:
    scored = metrics.copy()
    for metric in [
        "return_20d",
        "return_60d",
        "volatility_20d",
        "max_drawdown_60d",
        "turnover_change",
    ]:
        scored[f"{metric}_z"] = _zscore(scored[metric])

    scored["raw_score"] = 0.0
    for column, weight in SCORE_WEIGHTS.items():
        scored["raw_score"] += scored[column].fillna(0.0) * weight

    scored["score"] = _scale_to_100(scored["raw_score"])
    return scored


def _period_return(close: pd.Series, window: int) -> float:
    if close.empty:
        return 0.0
    if len(close) <= window:
        first = close.iloc[0]
    else:
        first = close.iloc[-window - 1]
    if first == 0 or pd.isna(first):
        return 0.0
    return float(close.iloc[-1] / first - 1)


def _annualized_volatility(returns: pd.Series, window: int) -> float:
    returns = returns.dropna().tail(window)
    if len(returns) < 2:
        return 0.0
    volatility = returns.std(ddof=1) * math.sqrt(TRADING_DAYS_PER_YEAR)
    return float(volatility) if pd.notna(volatility) else 0.0


def _max_drawdown(close: pd.Series) -> float:
    close = close.dropna()
    if close.empty:
        return 0.0
    running_max = close.cummax()
    drawdown = close / running_max - 1
    return float(drawdown.min())


def _amount_change(amount: pd.Series) -> float:
    amount = amount.dropna()
    if len(amount) < 6:
        return 0.0

    recent = amount.tail(5).mean()
    baseline_window = amount.iloc[:-5].tail(20)
    if baseline_window.empty:
        baseline_window = amount.iloc[:-5]

    baseline = baseline_window.mean()
    if baseline == 0 or pd.isna(baseline):
        return 0.0
    return float(recent / baseline - 1)


def _zscore(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0.0)
    std = values.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=series.index)
    return (values - values.mean()) / std


def _scale_to_100(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0.0)
    minimum = values.min()
    maximum = values.max()
    if maximum == minimum:
        return pd.Series(50.0, index=series.index)
    return (values - minimum) / (maximum - minimum) * 100


def _empty_score_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "rank",
            "industry",
            "score",
            "raw_score",
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
