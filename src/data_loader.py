from __future__ import annotations

import pandas as pd


def load_industry_sample() -> pd.DataFrame:
    """Return a tiny deterministic dataset for the first runnable MVP."""
    return pd.DataFrame(
        [
            {
                "industry": "Semiconductors",
                "return_20d": 0.082,
                "return_60d": 0.151,
                "volatility_20d": 0.031,
                "max_drawdown_60d": -0.074,
                "turnover_change": 0.126,
            },
            {
                "industry": "Software",
                "return_20d": 0.054,
                "return_60d": 0.118,
                "volatility_20d": 0.027,
                "max_drawdown_60d": -0.061,
                "turnover_change": 0.083,
            },
            {
                "industry": "Banks",
                "return_20d": 0.018,
                "return_60d": 0.046,
                "volatility_20d": 0.012,
                "max_drawdown_60d": -0.025,
                "turnover_change": -0.014,
            },
            {
                "industry": "Consumer Electronics",
                "return_20d": 0.063,
                "return_60d": 0.096,
                "volatility_20d": 0.035,
                "max_drawdown_60d": -0.092,
                "turnover_change": 0.104,
            },
            {
                "industry": "Pharmaceuticals",
                "return_20d": 0.027,
                "return_60d": 0.062,
                "volatility_20d": 0.021,
                "max_drawdown_60d": -0.049,
                "turnover_change": 0.035,
            },
        ]
    )
