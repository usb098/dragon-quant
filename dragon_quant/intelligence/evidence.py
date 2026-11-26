"""事前预期代理与龙头生命周期事件：只使用当时可见的已保存快照。"""

from __future__ import annotations

from typing import Any, Mapping


def _dict(value: Any) -> dict:
    return dict(value) if isinstance(value, Mapping) else {}


def _rows(value: Any) -> list[dict]:
    return [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _candidate(snapshot: Any, code: str) -> dict | None:
    review = _dict(_dict(snapshot).get("review"))
    leaders = _dict(review.get("leaders"))
    sources = (
        _rows(review.get("review_candidates")),
        _rows(leaders.get("mainline_leaders")),
        _rows(_dict(leaders.get("space_board")).get("stocks")),
        [_dict(leaders.get("market_total_leader")).get("candidate")]
        if isinstance(_dict(leaders.get("market_total_leader")).get("candidate"), Mapping)
        else [],
    )
    merged: dict | None = None
    for source in sources:
        for row in source:
            if _text(row.get("code")) != code:
                continue
            merged = {**(merged or {}), **row}
    return merged


def _height(candidate: Mapping[str, Any] | None) -> float | None:
    if not isinstance(candidate, Mapping):
        return None
    for key in ("height", "board_height", "high_num"):
        value = _number(candidate.get(key))
        if value is not None and 0 < value <= 99:
            if key == "high_num" and value > 99:
                continue
            return value
    return None


def _mainline(candidate: Mapping[str, Any] | None) -> dict:
    raw = candidate.get("mainline") if isinstance(candidate, Mapping) else None
    if isinstance(raw, Mapping):
        return dict(raw)
    if isinstance(raw, str):
        return {"board_name": raw}
    return {}


def _frozen_feedback_expectation(
    code: str,
    feedback: Any,
    prev_plan: Any,
    *,
    trade_date: str | None = None,
    fallback_expected: Mapping[str, Any] | None = None,
) -> dict | None:
    payload = _dict(feedback)
    items = _rows(payload.get("items"))
    row = next((item for item in items if _text(item.get("code")) == code), None)
    if row is None:
        return None

    plan = _dict(prev_plan)
    plans = _rows(plan.get("feedback_plans"))
    plan_row = next((item for item in plans if _text(item.get("code")) == code), None)
    expected = _dict(_dict(plan_row).get("expected"))
    source = _text(row.get("expectations_source")) or "unknown"
    if not expected and source == "config_fallback" and isinstance(fallback_expected, Mapping):
        expected = dict(fallback_expected)
    basis = (
        "frozen_previous_plan_feedback"
        if source == "prev_plan"
        else "frozen_config_expectation"
        if source == "config_fallback"
        else "frozen_expectation_unknown"
    )
    date = _text(payload.get("eval_date"))
    if trade_date and date and date != trade_date:
        return None
    unknown_reason = _text(row.get("unknown_reason"))
    if row.get("state") == "unknown" or unknown_reason:
        return {
            "status": "unknown",
            "basis": basis,
            "previous_trade_date": _text(payload.get("source_plan_date")),
            "evaluation_date": date,
            "reason": unknown_reason or "feedback_unknown",
            "feedback_state": _text(row.get("state")),
            "expectations_source": source,
            "positive_evidence": [],
            "negative_evidence": [],
            "actual_gap_pct": _number(row.get("gap_pct")),
            "actual_auction_ratio": _number(row.get("auction_ratio")),
            "expected_gap_low": _number(expected.get("gap_low")),
            "expected_gap_high": _number(expected.get("gap_high")),
            "expected_ratio_low": _number(expected.get("ratio_low")),
            "note": "T+1 冻结预期反馈缺少有效行情或必需字段；不把缺失解释为达标或不达标。",
        }

    gap = _number(row.get("gap_pct"))
    ratio = _number(row.get("auction_ratio"))
    low = _number(expected.get("gap_low"))
    high = _number(expected.get("gap_high"))
    ratio_low = _number(expected.get("ratio_low"))
    if None in (gap, low, high, ratio, ratio_low):
        return {
            "status": "unknown",
            "basis": basis,
            "previous_trade_date": _text(payload.get("source_plan_date")),
            "evaluation_date": date,
            "reason": "frozen_expectation_fields_missing",
            "feedback_state": _text(row.get("state")),
            "expectations_source": source,
            "positive_evidence": [],
            "negative_evidence": [],
            "actual_gap_pct": gap,
            "actual_auction_ratio": ratio,
            "expected_gap_low": low,
            "expected_gap_high": high,
            "expected_ratio_low": ratio_low,
            "note": "冻结预期区间或实际竞价字段缺失，无法比较。",
        }

    positive: list[str] = []
    negative: list[str] = []
    if gap > high:
        positive.append(f"实际竞价缺口 {gap:.2f}% 高于冻结预期上沿 {high:.2f}%")
    elif gap < low:
        negative.append(f"实际竞价缺口 {gap:.2f}% 低于冻结预期下沿 {low:.2f}%")
    else:
        positive.append(f"实际竞价缺口 {gap:.2f}% 落在冻结区间 [{low:.2f}%, {high:.2f}%] 内")
    if ratio >= ratio_low:
        positive.append(f"竞价额比 {ratio:.2f} 达到冻结下限 {ratio_low:.2f}")
    else:
        negative.append(f"竞价额比 {ratio:.2f} 低于冻结下限 {ratio_low:.2f}")
    if row.get("state") in ("weakened", "invalidated"):
        negative.append(f"T+1 反馈状态为 {row.get('state')}")
    if positive and negative:
        status = "mixed"
        reason = "mixed_frozen_expectation_evidence"
    elif gap > high and ratio >= ratio_low and row.get("state") == "confirmed":
        status = "above_prior_expectation"
        reason = "above_frozen_expectation_range"
    elif negative:
        status = "below_prior_expectation"
        reason = "below_frozen_expectation"
    elif row.get("state") == "confirmed":
        status = "met_prior_expectation"
        reason = "confirmed_within_frozen_expectation"
    else:
        status = "unknown"
        reason = "feedback_not_confirmed"
    return {
        "status": status,
        "basis": basis,
        "previous_trade_date": _text(payload.get("source_plan_date")),
        "evaluation_date": date,
        "reason": reason,
        "feedback_state": _text(row.get("state")),
        "expectations_source": source,
        "actual_gap_pct": gap,
        "actual_auction_ratio": ratio,
        "expected_gap_low": low,
        "expected_gap_high": high,
        "expected_ratio_low": ratio_low,
        "positive_evidence": positive,
        "negative_evidence": negative,
        "note": "按 T-1 已冻结预期与 T+1 实际竞价/反馈比较；这代表系统自身事前基线，不等于全市场一致预期。",
    }


def build_pre_event_expectation(
    candidate: Mapping[str, Any],
    previous_snapshots: list[Any],
    *,
    feedback: Any = None,
    prev_plan: Any = None,
) -> dict:
    """比较 T-1 冻结预期与 T+1 反馈；缺失时回退前序快照框架代理。

    冻结预期反馈来自 prep 的 feedback.items 与 prev_plan.feedback_plans。
    它是系统事前基线，不是外部市场一致预期。
    """
    code = _text(candidate.get("code")) or ""
    previous = previous_snapshots[0] if previous_snapshots else None
    prior = _candidate(previous, code) if code and previous is not None else None
    fallback_expected = _dict(prior).get("expectations") if prior is not None else None
    frozen = _frozen_feedback_expectation(
        code,
        feedback,
        prev_plan,
        trade_date=_text(candidate.get("trade_date")),
        fallback_expected=fallback_expected if isinstance(fallback_expected, Mapping) else None,
    ) if code else None
    if frozen is not None:
        return frozen

    previous_date = _text(_dict(previous).get("trade_date")) if previous is not None else None
    if prior is None:
        return {
            "status": "unknown",
            "basis": "prior_snapshot_framework_proxy",
            "previous_trade_date": previous_date,
            "reason": "prior_candidate_missing",
            "positive_evidence": [],
            "negative_evidence": [],
            "actual_gap_pct": None,
            "actual_auction_ratio": None,
            "expected_gap_low": None,
            "expected_gap_high": None,
            "expected_ratio_low": None,
            "note": "没有冻结预期反馈或可比较的前序候选快照；不倒推或补造事前预期。",
        }

    prior_role = _text(prior.get("role")) or "unknown"
    current_role = _text(candidate.get("role")) or "unknown"
    prior_mainline = _mainline(prior)
    current_mainline = _mainline(candidate)
    prior_rank = _number(prior_mainline.get("rank") or prior.get("mainline_rank"))
    current_rank = _number(
        current_mainline.get("rank") or candidate.get("mainline_rank")
        or _dict(candidate.get("structure")).get("mainline_rank")
    )
    prior_state = _text(prior_mainline.get("state") or prior.get("mainline_state"))
    current_state = _text(
        current_mainline.get("state") or candidate.get("mainline_state")
        or _dict(candidate.get("structure")).get("mainline_state")
    )
    prior_height = _height(prior)
    current_height = _height(candidate)
    positive: list[str] = []
    negative: list[str] = []

    role_order = {"leader": 0, "vanguard": 1, "mainstay": 2, "capacity": 3, "follower": 4}
    if current_role in role_order and prior_role in role_order:
        if role_order[current_role] < role_order[prior_role]:
            positive.append(f"角色由 {prior_role} 提升为 {current_role}")
        elif role_order[current_role] > role_order[prior_role]:
            negative.append(f"角色由 {prior_role} 降为 {current_role}")
    if current_state == "strengthening":
        positive.append("当前主线状态为强化")
    elif current_state == "weakening":
        negative.append("当前主线状态为走弱")
    if prior_rank is not None and current_rank is not None:
        if current_rank < prior_rank:
            positive.append(f"主线排名由第 {prior_rank:g} 上升到第 {current_rank:g}")
        elif current_rank > prior_rank:
            negative.append(f"主线排名由第 {prior_rank:g} 下降到第 {current_rank:g}")
    if prior_height is not None and current_height is not None:
        if current_height > prior_height:
            positive.append(f"连板高度由 {prior_height:g} 板升至 {current_height:g} 板")
        elif current_height < prior_height:
            negative.append(f"连板高度由 {prior_height:g} 板回落至 {current_height:g} 板")

    if positive and negative:
        status = "mixed"
        reason = "positive_and_negative_evidence"
    elif positive:
        status = "above_prior_expectation"
        reason = "positive_framework_change"
    elif negative:
        status = "below_prior_expectation"
        reason = "negative_framework_change"
    elif prior_role == current_role and prior_state == current_state:
        status = "met_prior_expectation"
        reason = "role_and_mainline_state_unchanged"
    else:
        status = "unknown"
        reason = "insufficient_comparable_fields"

    return {
        "status": status,
        "basis": "prior_snapshot_framework_proxy",
        "previous_trade_date": previous_date,
        "evaluation_date": None,
        "reason": reason,
        "feedback_state": None,
        "expectations_source": None,
        "actual_gap_pct": None,
        "actual_auction_ratio": None,
        "expected_gap_low": None,
        "expected_gap_high": None,
        "expected_ratio_low": None,
        "previous_role": prior_role,
        "current_role": current_role,
        "previous_mainline_rank": prior_rank,
        "current_mainline_rank": current_rank,
        "previous_mainline_state": prior_state,
        "current_mainline_state": current_state,
        "previous_height": prior_height,
        "current_height": current_height,
        "positive_evidence": positive,
        "negative_evidence": negative,
        "note": "仅与上一份历史复盘快照的角色、主线和高度作比较；不是市场一致预期，也不是投资评级。",
    }


_STAGE_LABELS = {
    "first_observation": "首次观察",
    "handoff_candidate": "新老龙交接候选",
    "new_high": "创近期高度新高",
    "continuing": "龙头延续",
    "strengthening": "结构强化",
    "climax": "高潮观察",
    "weakening": "走弱观察",
    "former_total_leader": "前总龙头",
    "sector_leader": "主线核心",
    "emerging": "潜在新核心",
    "risk_watch": "风险观察",
    "watch": "持续观察",
}


def build_leader_lifecycle(
    candidate: Mapping[str, Any],
    *,
    current_total_leader_code: str | None,
    previous_snapshots: list[Any],
    phase: str,
    daily_bars: Any = None,
    feedback: Any = None,
) -> dict:
    """比较最近多份历史快照；观察到的快照数不是完整交易日数。"""
    code = _text(candidate.get("code")) or ""
    is_total = bool(code) and current_total_leader_code == code
    current_height = _height(candidate)
    observations: list[dict] = []
    previous_total_codes: list[str | None] = []
    for snapshot in previous_snapshots[:10]:
        payload = _dict(snapshot)
        review = _dict(payload.get("review"))
        leaders = _dict(review.get("leaders"))
        total = _dict(leaders.get("market_total_leader"))
        total_code = _text(total.get("code"))
        previous_total_codes.append(total_code)
        prior = _candidate(snapshot, code)
        observations.append({
            "trade_date": _text(payload.get("trade_date")),
            "height": _height(prior) if prior is not None else None,
            "role": _text(prior.get("role")) if prior is not None else None,
            "candidate_present": prior is not None,
            "is_total_leader": (
                prior is not None
                and total_code == code
                and total.get("status") == "identified"
            ),
            "mainline_state": _text(_mainline(prior).get("state")) if prior is not None else None,
        })

    previous_code = previous_total_codes[0] if previous_total_codes else None
    prior_heights = [item["height"] for item in observations if item["height"] is not None]
    peak_height = max(prior_heights) if prior_heights else None
    height_delta = (
        current_height - observations[0]["height"]
        if current_height is not None and observations and observations[0]["height"] is not None
        else None
    )
    events: list[str] = []
    if is_total:
        if previous_code and previous_code != code:
            stage = "handoff_candidate"
            events.append("leader_handoff")
        elif not observations or not any(item["is_total_leader"] for item in observations):
            stage = "first_observation"
            events.append("first_total_leader_observation")
        elif peak_height is not None and current_height is not None and current_height > peak_height:
            stage = "new_high"
            events.append("height_new_high")
        elif height_delta is not None and height_delta < 0:
            stage = "weakening"
            events.append("height_retraced")
        elif phase == "climax":
            stage = "climax"
        elif phase == "recession" or _text(_mainline(candidate).get("state")) == "weakening":
            stage = "weakening"
        elif height_delta is not None and height_delta > 0:
            stage = "strengthening"
        else:
            stage = "continuing"
    elif any(item["is_total_leader"] for item in observations):
        stage = "former_total_leader"
        events.append("total_leader_lost")
    elif _text(candidate.get("role")) == "leader":
        stage = "sector_leader"
    elif _text(candidate.get("role")) == "vanguard":
        stage = "emerging"
    elif phase in ("ice", "recession"):
        stage = "risk_watch"
    else:
        stage = "watch"

    previous_roles = [item["role"] for item in observations if item["role"]]
    if previous_roles and _text(candidate.get("role")) != previous_roles[0]:
        events.append("role_changed")
    if height_delta is not None and height_delta < 0:
        events.append("height_retraced")
    streak = 1 if is_total else 0
    if is_total:
        for item in observations:
            if not item["is_total_leader"]:
                break
            streak += 1

    # 近期 K 线事件：只在有连续日 K 时识别，不把缺失当作没有事件。
    raw_bars = daily_bars if isinstance(daily_bars, list) else []
    bars = [
        dict(item) for item in raw_bars
        if isinstance(item, Mapping)
        and isinstance(item.get("date"), str)
        and item.get("date") <= (_text(candidate.get("trade_date")) or "9999-99-99")
    ]
    bars.sort(key=lambda item: str(item.get("date") or ""))
    current_bar = bars[-1] if bars else None
    previous_bar = bars[-2] if len(bars) >= 2 else None

    def candle_down(bar: Mapping[str, Any] | None) -> bool | None:
        if not isinstance(bar, Mapping):
            return None
        open_price = _number(bar.get("open"))
        close_price = _number(bar.get("close"))
        if open_price is None or close_price is None:
            return None
        return close_price < open_price

    current_down = candle_down(current_bar)
    previous_down = candle_down(previous_bar)
    candle_context = {
        "status": "measured" if current_bar and previous_bar else "insufficient_history",
        "current_date": _text(_dict(current_bar).get("date")),
        "previous_date": _text(_dict(previous_bar).get("date")),
        "current_down_candle": current_down,
        "previous_down_candle": previous_down,
        "bullish_engulfing_after_negative": None,
        "board_break_count": None,
        "note": "近端 K 线事件仅覆盖本地日 K 可用窗口；不等同于完整龙头事件档案。",
    }
    if current_bar is not None and previous_bar is not None:
        if current_down is True and previous_down is False:
            recent_prior = bars[:-1][-10:]
            prior_negative = any(candle_down(item) is True for item in recent_prior)
            if not prior_negative:
                events.append("first_negative_in_observed_window")
            else:
                events.append("negative_day_observed")
        elif current_down is False and previous_down is True:
            events.append("rebound_after_negative")
            prev_open = _number(previous_bar.get("open"))
            prev_close = _number(previous_bar.get("close"))
            current_open = _number(current_bar.get("open"))
            current_close = _number(current_bar.get("close"))
            if (
                None not in (prev_open, prev_close, current_open, current_close)
                and current_close > prev_open
                and current_open < prev_close
            ):
                candle_context["bullish_engulfing_after_negative"] = True
                events.append("bullish_engulfing_after_negative")
            else:
                candle_context["bullish_engulfing_after_negative"] = False

    feedback_items = _rows(_dict(feedback).get("items"))
    feedback_row = next(
        (item for item in feedback_items if _text(item.get("code")) == code),
        None,
    )
    feedback_evidence = _dict(_dict(feedback_row).get("evidence"))
    broken_count = _number(feedback_evidence.get("broken_count"))
    candle_context["board_break_count"] = (
        int(broken_count) if broken_count is not None else None
    )
    if broken_count is not None and broken_count > 0:
        events.append("intraday_board_break_observed")

    observed_heights = [
        value for value in (peak_height, current_height)
        if value is not None
    ]
    return {
        "stage": stage,
        "label": _STAGE_LABELS[stage],
        "previous_total_leader_code": previous_code,
        "total_leader_observed_streak": streak,
        "observation_count": len(observations),
        "candidate_observation_count": sum(
            1 for item in observations if item["candidate_present"]
        ),
        "height_history": [
            {"trade_date": item["trade_date"], "height": item["height"]}
            for item in observations if item["height"] is not None
        ],
        "observed_height_peak": max(observed_heights) if observed_heights else None,
        "height_delta_vs_previous": height_delta,
        "candle_context": candle_context,
        "events": list(dict.fromkeys(events)),
        "scope": "基于当前及最多 10 份已保存复盘快照；缺失日期不补齐，因此 streak 是观察快照连续数，不等于完整交易日连续数。",
    }


__all__ = ["build_pre_event_expectation", "build_leader_lifecycle"]
