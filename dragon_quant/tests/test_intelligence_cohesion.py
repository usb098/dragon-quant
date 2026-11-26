from __future__ import annotations

from dragon_quant.intelligence.cohesion import build_market_cohesion


def _asset(rows):
    return {"rows": rows}


def _daily_asset(codes, *, dates=("2026-11-24", "2026-11-25", "2026-11-26", "2026-11-27")):
    rows = {}
    for index, code in enumerate(codes):
        closes = [10.0 + index, 10.2 + index, 10.5 + index, 10.9 + index]
        rows[code] = [
            {"date": day, "close": close, "volume": 1000}
            for day, close in zip(dates, closes)
        ]
    return {"trade_date": dates[-1], "rows": rows}


def test_mainline_cohesion_is_measured_when_members_and_history_are_covered():
    codes = [f"60000{i}" for i in range(1, 7)]
    result = build_market_cohesion(
        _asset([{"name": "机器人", "stock_list": [{"code": code} for code in codes]}]),
        _daily_asset(codes),
        trade_date="2026-11-27",
    )
    row = result["机器人"]
    assert row["status"] == "measured"
    assert row["member_count"] == 6
    assert row["covered_count"] == 6
    assert row["coverage_ratio"] == 1.0
    assert row["advancer_ratio"] == 1.0
    assert row["pairwise_correlation"] is not None
    assert row["history_sessions"] >= 3
    assert row["data_as_of"] == "2026-11-27"


def test_insufficient_members_and_missing_quotes_are_not_fabricated_as_zero():
    row = build_market_cohesion(
        _asset([{"name": "小板块", "stock_list": [{"code": "600001"}, {"code": "600002"}]}]),
        {"rows": {}},
        trade_date="2026-11-27",
    )["小板块"]
    assert row["status"] == "unknown"
    assert row["advancer_ratio"] is None
    assert row["pairwise_correlation"] is None
    assert row["coverage_ratio"] == 0.0
    assert row["member_count"] == 2


def test_low_coverage_is_partial_proxy_not_measured():
    codes = [f"60000{i}" for i in range(1, 7)]
    row = build_market_cohesion(
        _asset([{"name": "主线", "stock_list": [{"code": code} for code in codes]}]),
        _daily_asset(codes[:3]),
        trade_date="2026-11-27",
    )["主线"]
    assert row["status"] == "partial_proxy"
    assert row["coverage_ratio"] == 0.5
    assert row["advancer_ratio"] == 1.0
