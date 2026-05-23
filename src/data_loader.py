from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

import akshare as ak
import pandas as pd
import requests


DEFAULT_LOOKBACK_DAYS = 180


def default_start_date() -> date:
    """Return a conservative default start date for daily industry history."""
    return date.today() - timedelta(days=DEFAULT_LOOKBACK_DAYS)


def load_industry_snapshot() -> pd.DataFrame:
    """Load the Eastmoney A-share industry-board snapshot through AKShare."""
    try:
        raw = ak.stock_board_industry_name_em()
    except Exception:
        raw = _fetch_industry_snapshot_direct()

    if raw.empty:
        raise RuntimeError("AKShare returned an empty industry-board snapshot.")

    snapshot = raw.rename(
        columns={
            "板块名称": "industry",
            "板块代码": "industry_code",
            "最新价": "latest",
            "涨跌额": "change_amount",
            "涨跌幅": "change_pct",
            "总市值": "market_cap",
            "换手率": "turnover_rate",
            "上涨家数": "rising_count",
            "下跌家数": "falling_count",
            "领涨股票": "leading_stock",
            "领涨股票-涨跌幅": "leading_stock_change_pct",
        }
    ).copy()

    required = {"industry"}
    missing = required.difference(snapshot.columns)
    if missing:
        raise RuntimeError(f"AKShare industry snapshot missing columns: {sorted(missing)}")

    for column in [
        "latest",
        "change_amount",
        "change_pct",
        "market_cap",
        "turnover_rate",
        "rising_count",
        "falling_count",
        "leading_stock_change_pct",
    ]:
        if column in snapshot.columns:
            snapshot[column] = pd.to_numeric(snapshot[column], errors="coerce")

    snapshot["industry"] = snapshot["industry"].astype(str)
    if "industry_code" in snapshot.columns:
        snapshot["industry_code"] = snapshot["industry_code"].astype(str)

    return snapshot


def choose_industries_for_history(snapshot: pd.DataFrame, limit: int) -> pd.DataFrame:
    """Choose a small real-data universe to keep the first dashboard responsive."""
    if limit < 1:
        raise ValueError("limit must be greater than 0")
    if "industry" not in snapshot.columns:
        raise ValueError("snapshot must include an industry column")

    candidates = snapshot.copy()
    if "change_pct" in candidates.columns:
        candidates = candidates.sort_values("change_pct", ascending=False)

    if "industry_code" not in candidates.columns:
        candidates["industry_code"] = candidates["industry"]

    return (
        candidates[["industry_code", "industry"]]
        .dropna(subset=["industry"])
        .head(limit)
        .astype(str)
        .reset_index(drop=True)
    )


def load_industry_histories(
    industries: tuple[tuple[str, str], ...],
    start_date: str,
    end_date: str,
    period: str = "日k",
    adjust: str = "",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load daily history for selected A-share industry boards.

    The function returns `(history, failures)` so the UI can show partial data
    even if one upstream industry request fails.
    """
    histories: list[pd.DataFrame] = []
    failures: list[dict[str, str]] = []

    for symbol, industry in _unique_pairs(industries):
        try:
            raw = ak.stock_board_industry_hist_em(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                period=period,
                adjust=adjust,
            )
        except Exception:
            try:
                raw = _fetch_industry_history_direct(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    period=period,
                    adjust=adjust,
                )
            except Exception as exc:  # pragma: no cover - upstream network/API errors
                failures.append({"industry": industry, "error": str(exc)})
                continue

        try:
            normalized = _normalize_industry_history(raw, industry)
            if normalized.empty:
                failures.append({"industry": industry, "error": "empty history"})
            else:
                histories.append(normalized)
        except Exception as exc:  # pragma: no cover - upstream network/API errors
            failures.append({"industry": industry, "error": str(exc)})

    history = pd.concat(histories, ignore_index=True) if histories else pd.DataFrame()
    failure_frame = pd.DataFrame(failures, columns=["industry", "error"])
    return history, failure_frame


def _fetch_industry_snapshot_direct() -> pd.DataFrame:
    """Fetch the same Eastmoney industry snapshot directly as a fallback."""
    url = "https://17.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "100",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:90 t:2 f:!50",
        "fields": "f12,f14,f2,f3,f4,f8,f20,f104,f105,f128,f136",
    }
    payload = _get_json(url, params=params)
    diff = payload.get("data", {}).get("diff", [])
    rows = [
        {
            "板块代码": item.get("f12"),
            "板块名称": item.get("f14"),
            "最新价": item.get("f2"),
            "涨跌幅": item.get("f3"),
            "涨跌额": item.get("f4"),
            "换手率": item.get("f8"),
            "总市值": item.get("f20"),
            "上涨家数": item.get("f104"),
            "下跌家数": item.get("f105"),
            "领涨股票": item.get("f128"),
            "领涨股票-涨跌幅": item.get("f136"),
        }
        for item in diff
    ]
    return pd.DataFrame(rows)


def _fetch_industry_history_direct(
    symbol: str,
    start_date: str,
    end_date: str,
    period: str,
    adjust: str,
) -> pd.DataFrame:
    """Fetch Eastmoney industry kline data directly as a fallback."""
    period_map = {"日k": "101", "周k": "102", "月k": "103"}
    adjust_map = {"": "0", "qfq": "1", "hfq": "2"}
    if period not in period_map:
        raise ValueError(f"Unsupported period: {period}")
    if adjust not in adjust_map:
        raise ValueError(f"Unsupported adjust: {adjust}")
    if not symbol.startswith("BK"):
        raise ValueError("Direct history fallback requires an Eastmoney BK industry code.")

    url = "http://7.push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": f"90.{symbol}",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": period_map[period],
        "fqt": adjust_map[adjust],
        "beg": start_date,
        "end": end_date,
        "smplmt": "10000",
        "lmt": "1000000",
    }
    payload = _get_json(url, params=params)
    klines = payload.get("data", {}).get("klines", [])
    rows = [item.split(",") for item in klines]
    return pd.DataFrame(
        rows,
        columns=[
            "日期",
            "开盘",
            "收盘",
            "最高",
            "最低",
            "成交量",
            "成交额",
            "振幅",
            "涨跌幅",
            "涨跌额",
            "换手率",
        ],
    )


def _normalize_industry_history(raw: pd.DataFrame, industry: str) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()

    history = raw.rename(
        columns={
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "涨跌幅": "pct_change",
            "涨跌额": "change_amount",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "换手率": "turnover_rate",
        }
    ).copy()
    history["industry"] = industry

    required = {"date", "close"}
    missing = required.difference(history.columns)
    if missing:
        raise RuntimeError(f"history for {industry} missing columns: {sorted(missing)}")

    history["date"] = pd.to_datetime(history["date"], errors="coerce")
    for column in [
        "open",
        "close",
        "high",
        "low",
        "pct_change",
        "change_amount",
        "volume",
        "amount",
        "amplitude",
        "turnover_rate",
    ]:
        if column in history.columns:
            history[column] = pd.to_numeric(history[column], errors="coerce")

    history = history.dropna(subset=["date", "close"])
    return history.sort_values(["industry", "date"]).reset_index(drop=True)


def _get_json(url: str, params: dict[str, str]) -> dict:
    with requests.Session() as session:
        session.trust_env = False
        response = session.get(
            url,
            params=params,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
    response.raise_for_status()
    return response.json()


def _unique_pairs(items: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for symbol, industry in items:
        symbol_value = str(symbol).strip()
        industry_value = str(industry).strip()
        if symbol_value and industry_value and symbol_value not in seen:
            seen.add(symbol_value)
            result.append((symbol_value, industry_value))
    return result
