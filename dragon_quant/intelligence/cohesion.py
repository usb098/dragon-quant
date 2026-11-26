"""主线成分股合力测量：只消费已保存日 K 与板块成分快照，不触网。"""

from __future__ import annotations

import math
from typing import Any, Mapping


def _num(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 3:
        return None
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    x = [value - mean_left for value in left]
    y = [value - mean_right for value in right]
    sum_x2 = sum(value * value for value in x)
    sum_y2 = sum(value * value for value in y)
    if sum_x2 <= 1e-12 or sum_y2 <= 1e-12:
        return None
    value = sum(a * b for a, b in zip(x, y)) / math.sqrt(sum_x2 * sum_y2)
    return max(-1.0, min(1.0, value))


def _code(value: Any) -> str | None:
    if isinstance(value, Mapping):
        value = value.get("code")
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text if text else None


def _stock_returns(
    stock_daily: Mapping[str, Any],
    *,
    trade_date: str,
    lookback_days: int,
) -> dict[str, dict[str, float]]:
    payload = stock_daily.get("rows")
    if not isinstance(payload, Mapping):
        return {}
    output: dict[str, dict[str, float]] = {}
    for raw_code, raw_bars in payload.items():
        if not isinstance(raw_code, str) or not isinstance(raw_bars, list):
            continue
        bars: dict[str, dict] = {}
        for bar in raw_bars:
            if not isinstance(bar, Mapping):
                continue
            day = bar.get("date")
            if isinstance(day, str) and day and day <= trade_date:
                bars[day] = dict(bar)
        dates = sorted(bars)[-max(lookback_days + 1, 4):]
        returns: dict[str, float] = {}
        previous_close: float | None = None
        for day in dates:
            bar = bars[day]
            close = _num(bar.get("close"))
            pct = _num(bar.get("pct"))
            if close is not None and close > 0 and previous_close is not None and previous_close > 0:
                returns[day] = (close / previous_close - 1.0) * 100.0
            elif pct is not None:
                returns[day] = pct
            if close is not None and close > 0:
                previous_close = close
        output[raw_code] = returns
    return output


def _board_members(row: Mapping[str, Any]) -> list[str]:
    raw = row.get("stock_list")
    if not isinstance(raw, list):
        raw = row.get("members")
    if not isinstance(raw, list):
        return []
    seen: set[str] = set()
    result: list[str] = []
    for item in raw:
        code = _code(item)
        if code and code not in seen:
            seen.add(code)
            result.append(code)
    return result


def _measure_board(
    row: Mapping[str, Any],
    returns_by_code: Mapping[str, Mapping[str, float]],
    *,
    trade_date: str,
    minimum_members: int,
    minimum_coverage: float,
) -> dict:
    members = _board_members(row)
    count = len(members)
    current = {
        code: _num(returns_by_code.get(code, {}).get(trade_date))
        for code in members
    }
    known_current = {code: value for code, value in current.items() if value is not None}
    coverage = len(known_current) / count if count else None
    advancer_ratio = (
        sum(1 for value in known_current.values() if value > 0) / len(known_current)
        if known_current else None
    )
    decliner_ratio = (
        sum(1 for value in known_current.values() if value < 0) / len(known_current)
        if known_current else None
    )
    current_values = list(known_current.values())
    mean_return = sum(current_values) / len(current_values) if current_values else None
    median_return = None
    if current_values:
        ordered = sorted(current_values)
        middle = len(ordered) // 2
        median_return = (
            ordered[middle] if len(ordered) % 2
            else (ordered[middle - 1] + ordered[middle]) / 2
        )

    common_dates: set[str] = set()
    for code in members:
        common_dates.update(returns_by_code.get(code, {}).keys())
    aligned_dates = sorted(common_dates)[-5:]
    correlations: list[float] = []
    synchronized_up: list[bool] = []
    synchronized_down: list[bool] = []
    for left_index, left_code in enumerate(members):
        for right_code in members[left_index + 1:]:
            left_series = returns_by_code.get(left_code, {})
            right_series = returns_by_code.get(right_code, {})
            shared = [day for day in aligned_dates if day in left_series and day in right_series]
            correlation = _pearson(
                [float(left_series[day]) for day in shared],
                [float(right_series[day]) for day in shared],
            )
            if correlation is not None:
                correlations.append(correlation)

    for day in aligned_dates:
        values = [
            returns_by_code.get(code, {}).get(day)
            for code in members
        ]
        valid = [float(value) for value in values if value is not None]
        if len(valid) < max(3, math.ceil(count * minimum_coverage)):
            continue
        positive = sum(1 for value in valid if value > 0) / len(valid)
        negative = sum(1 for value in valid if value < 0) / len(valid)
        synchronized_up.append(positive >= 0.6)
        synchronized_down.append(negative >= 0.6)

    pairwise = sum(correlations) / len(correlations) if correlations else None
    synchronized_up_ratio = (
        sum(synchronized_up) / len(synchronized_up) if synchronized_up else None
    )
    synchronized_down_ratio = (
        sum(synchronized_down) / len(synchronized_down) if synchronized_down else None
    )
    enough_members = count >= minimum_members
    enough_coverage = coverage is not None and coverage >= minimum_coverage
    enough_history = len(aligned_dates) >= 3 and bool(correlations)
    measured = enough_members and enough_coverage and enough_history
    if measured:
        status = "measured"
    elif known_current or correlations:
        status = "partial_proxy"
    else:
        status = "unknown"

    return {
        "status": status,
        "member_count": count,
        "covered_count": len(known_current),
        "coverage_ratio": round(coverage, 4) if coverage is not None else None,
        "advancer_ratio": round(advancer_ratio, 4) if advancer_ratio is not None else None,
        "decliner_ratio": round(decliner_ratio, 4) if decliner_ratio is not None else None,
        "mean_return_pct": round(mean_return, 4) if mean_return is not None else None,
        "median_return_pct": round(median_return, 4) if median_return is not None else None,
        "pairwise_correlation": round(pairwise, 4) if pairwise is not None else None,
        "correlation_pairs": len(correlations),
        "synchronized_up_ratio": round(synchronized_up_ratio, 4)
        if synchronized_up_ratio is not None else None,
        "synchronized_down_ratio": round(synchronized_down_ratio, 4)
        if synchronized_down_ratio is not None else None,
        "history_sessions": len(aligned_dates),
        "data_as_of": trade_date if trade_date in {
            day for values in returns_by_code.values() for day in values
        } else None,
        "note": (
            "基于板块成分股近 5 个共同交易日的收益同步与相关性；覆盖率达标才标记 measured。"
            if measured else
            "成分股数量、当日行情覆盖或共同历史长度不足，当前仅作部分代理，不推断板块合力。"
        ),
    }


def build_market_cohesion(
    block_asset: Any,
    stock_daily_asset: Any,
    *,
    trade_date: str,
    minimum_members: int = 5,
    minimum_coverage: float = 0.6,
) -> dict[str, dict]:
    """按板块名称返回合力指标；无数据处返回 unknown，不把缺失当作 0。"""

    block = block_asset if isinstance(block_asset, Mapping) else {}
    stock_daily = stock_daily_asset if isinstance(stock_daily_asset, Mapping) else {}
    rows = block.get("rows")
    if not isinstance(rows, list):
        return {}
    returns = _stock_returns(stock_daily, trade_date=trade_date, lookback_days=5)
    output: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        name = row.get("name") or row.get("board_name")
        if not isinstance(name, str) or not name.strip():
            continue
        output[name.strip()] = _measure_board(
            row,
            returns,
            trade_date=trade_date,
            minimum_members=minimum_members,
            minimum_coverage=minimum_coverage,
        )
    return output


__all__ = ["build_market_cohesion"]
