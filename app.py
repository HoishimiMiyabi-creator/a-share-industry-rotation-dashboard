from __future__ import annotations

from datetime import date

import plotly.express as px
import streamlit as st

from src.data_loader import (
    choose_industries_for_history,
    default_start_date,
    load_industry_histories as fetch_industry_histories,
    load_industry_snapshot as fetch_industry_snapshot,
)
from src.metrics import calculate_industry_scores


st.set_page_config(
    page_title="A-share Industry Rotation Dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)


def main() -> None:
    st.title("A-share Industry Rotation Dashboard")
    st.caption("AKShare industry-board data. Research demo only. Not investment advice.")

    st.sidebar.header("Parameters")
    top_n = st.sidebar.slider("Top N industries", min_value=3, max_value=10, value=5)
    history_limit = st.sidebar.slider(
        "Industries to fetch history for",
        min_value=5,
        max_value=30,
        value=15,
        help="More industries give broader ranking but require more upstream requests.",
    )
    start_date_value = st.sidebar.date_input("History start date", value=default_start_date())
    end_date_value = st.sidebar.date_input("History end date", value=date.today())
    if st.sidebar.button("Clear cached data"):
        st.cache_data.clear()
        st.rerun()

    start_date = _format_akshare_date(start_date_value)
    end_date = _format_akshare_date(end_date_value)

    try:
        snapshot = load_industry_snapshot()
        universe = choose_industries_for_history(snapshot, history_limit)
        industries = tuple(universe.itertuples(index=False, name=None))
        history, failures = load_industry_histories(industries, start_date, end_date)
        scores = calculate_industry_scores(history)
    except Exception as exc:
        st.error(f"Failed to load AKShare industry-board data: {exc}")
        st.stop()

    metric_left, metric_mid, metric_right = st.columns(3)
    metric_left.metric("Industry boards", len(snapshot))
    metric_mid.metric("History universe", len(universe))
    metric_right.metric("History rows", len(history))

    if not failures.empty:
        st.warning("Some industry history requests failed. Showing available data.")
        st.dataframe(failures, use_container_width=True, hide_index=True)

    st.subheader("Industry Score Ranking")
    if scores.empty:
        st.warning("No valid industry history was returned for the selected date range.")
    else:
        st.dataframe(
            _format_score_table(scores.head(top_n)),
            use_container_width=True,
            hide_index=True,
        )
        st.plotly_chart(
            px.bar(
                scores.head(top_n).sort_values("score"),
                x="score",
                y="industry",
                orientation="h",
                title=f"Top {top_n} Composite Industry Scores",
            ),
            use_container_width=True,
        )

    st.subheader("Industry Snapshot")
    snapshot_columns = [
        column
        for column in [
            "industry",
            "industry_code",
            "latest",
            "change_pct",
            "turnover_rate",
            "rising_count",
            "falling_count",
            "leading_stock",
            "leading_stock_change_pct",
        ]
        if column in snapshot.columns
    ]
    st.dataframe(
        snapshot[snapshot_columns].head(30),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Data Notes")
    st.markdown(
        """
        - Industry list: `akshare.stock_board_industry_name_em()`.
        - Industry history: `akshare.stock_board_industry_hist_em()`.
        - Metrics: 20-day return, 60-day return, annualized 20-day volatility,
          60-day max drawdown, and recent amount change.
        - Composite score: cross-sectional z-score weighted ranking, scaled to 0-100.
        - Data is cached with `st.cache_data(ttl=3600)` to reduce repeated upstream requests.
        - All outputs are for learning and research, not trading recommendations.
        """
    )


def _format_akshare_date(value: date) -> str:
    return value.strftime("%Y%m%d")


@st.cache_data(ttl=3600)
def load_industry_snapshot():
    return fetch_industry_snapshot()


@st.cache_data(ttl=3600)
def load_industry_histories(industries, start_date, end_date):
    return fetch_industry_histories(industries, start_date, end_date)


def _format_score_table(scores):
    display = scores.copy()
    percent_columns = [
        "return_20d",
        "return_60d",
        "volatility_20d",
        "max_drawdown_60d",
        "turnover_change",
    ]
    for column in percent_columns:
        display[column] = (display[column] * 100).map("{:.2f}%".format)
    display["score"] = display["score"].map("{:.2f}".format)
    display["raw_score"] = display["raw_score"].map("{:.4f}".format)
    display["latest_close"] = display["latest_close"].map("{:.2f}".format)
    return display


if __name__ == "__main__":
    main()
