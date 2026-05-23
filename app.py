from __future__ import annotations

import streamlit as st

from src.data_loader import load_industry_sample
from src.metrics import calculate_industry_scores


st.set_page_config(
    page_title="A-share Industry Rotation Dashboard",
    page_icon="📈",
    layout="wide",
)


def main() -> None:
    st.title("A-share Industry Rotation Dashboard")
    st.caption("Research demo only. Not investment advice.")

    st.sidebar.header("Parameters")
    top_n = st.sidebar.slider("Top N industries", min_value=3, max_value=10, value=5)

    data = load_industry_sample()
    scores = calculate_industry_scores(data)

    st.subheader("Industry Score Ranking")
    st.dataframe(scores.head(top_n), use_container_width=True, hide_index=True)

    st.subheader("Prototype Notes")
    st.markdown(
        """
        - Current version uses sample data to verify project structure and deployment.
        - Next step: replace `load_industry_sample()` with AKShare industry-board data.
        - All outputs are for learning and research, not trading recommendations.
        """
    )


if __name__ == "__main__":
    main()
