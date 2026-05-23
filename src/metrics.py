from __future__ import annotations

import pandas as pd


def calculate_industry_scores(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate a simple composite score for ranking industries."""
    required_columns = {
        "industry",
        "return_20d",
        "return_60d",
        "volatility_20d",
        "max_drawdown_60d",
        "turnover_change",
    }
    missing = required_columns.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    scores = data.copy()
    scores["score"] = (
        scores["return_20d"] * 0.35
        + scores["return_60d"] * 0.35
        + scores["turnover_change"] * 0.20
        - scores["volatility_20d"] * 0.05
        + scores["max_drawdown_60d"] * 0.05
    )
    scores["rank"] = scores["score"].rank(ascending=False, method="first").astype(int)

    columns = [
        "rank",
        "industry",
        "score",
        "return_20d",
        "return_60d",
        "volatility_20d",
        "max_drawdown_60d",
        "turnover_change",
    ]
    return scores.sort_values("rank")[columns]
