from __future__ import annotations

from dragon_quant.intelligence.evidence import (
    build_leader_lifecycle,
    build_pre_event_expectation,
)


def _snapshot(day, *, code="600001", role="vanguard", rank=3, state="stable",
              height=3, total_code=None):
    candidate = {
        "code": code,
        "name": "股票A",
        "role": role,
        "height": height,
        "mainline": {"board_name": "机器人", "rank": rank, "state": state},
    }
    review = {
        "review_candidates": [candidate],
        "leaders": {
            "market_total_leader": {
                "status": "identified" if total_code else "unconfirmed",
                "code": total_code,
            },
            "mainline_leaders": [candidate] if role == "leader" else [],
            "space_board": {"stocks": [candidate]},
        },
    }
    return {"trade_date": day, "review": review}


def test_pre_event_expectation_uses_only_previous_saved_framework():
    previous = _snapshot("2026-11-26", role="vanguard", rank=3, height=3)
    current = {
        "code": "600001",
        "role": "leader",
        "height": 5,
        "mainline": {"board_name": "机器人", "rank": 1, "state": "strengthening"},
    }
    result = build_pre_event_expectation(current, [previous])
    assert result["status"] == "above_prior_expectation"
    assert result["basis"] == "prior_snapshot_framework_proxy"
    assert result["previous_trade_date"] == "2026-11-26"
    assert result["positive_evidence"]
    assert "不是市场一致预期" in result["note"]


def test_no_prior_candidate_stays_unknown():
    current = {"code": "600999", "role": "leader"}
    result = build_pre_event_expectation(current, [_snapshot("2026-11-26")])
    assert result["status"] == "unknown"
    assert result["reason"] == "prior_candidate_missing"


def test_lifecycle_detects_handoff_and_height_retrace():
    previous = [
        _snapshot("2026-11-26", code="600001", role="leader", height=6, total_code="600001"),
        _snapshot("2026-11-25", code="600001", role="leader", height=5, total_code="600001"),
    ]
    current = {"code": "600001", "role": "leader", "height": 5,
               "mainline": {"board_name": "机器人", "state": "stable"}}
    result = build_leader_lifecycle(
        current,
        current_total_leader_code="600001",
        previous_snapshots=previous,
        phase="fermentation",
    )
    assert result["stage"] == "weakening"
    assert result["height_delta_vs_previous"] == -1
    assert "height_retraced" in result["events"]
    assert result["total_leader_observed_streak"] == 3


def test_lifecycle_marks_new_leader_handoff():
    previous = [_snapshot("2026-11-26", code="600009", role="leader", height=7, total_code="600009")]
    current = {"code": "600001", "role": "leader", "height": 5,
               "mainline": {"board_name": "机器人", "state": "strengthening"}}
    result = build_leader_lifecycle(
        current,
        current_total_leader_code="600001",
        previous_snapshots=previous,
        phase="fermentation",
    )
    assert result["stage"] == "handoff_candidate"
    assert result["previous_total_leader_code"] == "600009"
    assert "leader_handoff" in result["events"]



def test_frozen_t1_feedback_takes_precedence_over_prior_framework_proxy():
    previous = _snapshot("2026-11-26", role="vanguard", rank=3, height=3)
    candidate = {
        "code": "600001",
        "trade_date": "2026-11-27",
        "role": "leader",
        "height": 5,
    }
    feedback = {
        "source_plan_date": "2026-11-26",
        "eval_date": "2026-11-27",
        "items": [{
            "code": "600001",
            "state": "confirmed",
            "gap_pct": 8.5,
            "auction_ratio": 1.4,
            "unknown_reason": None,
            "expectations_source": "prev_plan",
        }],
    }
    plan = {
        "source_trade_date": "2026-11-26",
        "feedback_plans": [{
            "code": "600001",
            "expected": {
                "gap_low": 3.0,
                "gap_high": 7.0,
                "ratio_low": 1.2,
                "seal_by": "10:00",
            },
        }],
    }
    result = build_pre_event_expectation(
        candidate,
        [previous],
        feedback=feedback,
        prev_plan=plan,
    )
    assert result["status"] == "above_prior_expectation"
    assert result["basis"] == "frozen_previous_plan_feedback"
    assert result["expected_gap_high"] == 7.0
    assert result["actual_gap_pct"] == 8.5


def test_unknown_frozen_feedback_is_not_replaced_by_prior_snapshot_proxy():
    previous = _snapshot("2026-11-26", role="vanguard", rank=3, height=3)
    candidate = {
        "code": "600001",
        "trade_date": "2026-11-27",
        "role": "leader",
        "height": 5,
    }
    feedback = {
        "source_plan_date": "2026-11-26",
        "eval_date": "2026-11-27",
        "items": [{
            "code": "600001",
            "state": "unknown",
            "gap_pct": None,
            "auction_ratio": None,
            "unknown_reason": "t1_quote_missing",
            "expectations_source": "prev_plan",
        }],
    }
    plan = {
        "source_trade_date": "2026-11-26",
        "feedback_plans": [{
            "code": "600001",
            "expected": {"gap_low": 3.0, "gap_high": 7.0, "ratio_low": 1.2},
        }],
    }
    result = build_pre_event_expectation(
        candidate,
        [previous],
        feedback=feedback,
        prev_plan=plan,
    )
    assert result["status"] == "unknown"
    assert result["basis"] == "frozen_previous_plan_feedback"
    assert result["reason"] == "t1_quote_missing"


def test_feedback_from_a_different_trade_date_is_not_consumed():
    candidate = {
        "code": "600001",
        "trade_date": "2026-11-27",
        "role": "leader",
        "height": 5,
    }
    feedback = {
        "source_plan_date": "2026-11-25",
        "eval_date": "2026-11-26",
        "items": [{
            "code": "600001",
            "state": "confirmed",
            "gap_pct": 8.5,
            "auction_ratio": 1.4,
            "unknown_reason": None,
            "expectations_source": "prev_plan",
        }],
    }
    result = build_pre_event_expectation(candidate, [], feedback=feedback)
    assert result["status"] == "unknown"
    assert result["reason"] == "prior_candidate_missing"



def test_lifecycle_peak_is_none_when_no_historical_heights_exist():
    previous = [{"trade_date": "2026-11-26", "review": {"leaders": {
        "market_total_leader": {"status": "unconfirmed", "code": None},
        "mainline_leaders": [],
        "space_board": {"stocks": []},
    }}}]
    current = {"code": "600001", "role": "follower"}
    result = build_leader_lifecycle(
        current,
        current_total_leader_code=None,
        previous_snapshots=previous,
        phase="unknown",
    )
    assert result["observed_height_peak"] is None
    assert result["candidate_observation_count"] == 0


def test_total_leader_observed_streak_counts_only_contiguous_saved_snapshots():
    one_prior = [
        _snapshot("2026-11-26", code="600001", role="leader", height=4, total_code="600001")
    ]
    current = {"code": "600001", "role": "leader", "height": 5}
    result = build_leader_lifecycle(
        current,
        current_total_leader_code="600001",
        previous_snapshots=one_prior,
        phase="fermentation",
    )
    assert result["total_leader_observed_streak"] == 2

    missing_middle = [
        _snapshot("2026-11-26", code="600001", role="leader", height=4, total_code="600001"),
        {"trade_date": "2026-11-25", "review": {"leaders": {
            "market_total_leader": {"status": "unconfirmed", "code": None},
            "mainline_leaders": [],
            "space_board": {"stocks": []},
        }}},
        _snapshot("2026-11-24", code="600001", role="leader", height=3, total_code="600001"),
    ]
    broken = build_leader_lifecycle(
        current,
        current_total_leader_code="600001",
        previous_snapshots=missing_middle,
        phase="fermentation",
    )
    assert broken["total_leader_observed_streak"] == 2



def test_lifecycle_recognizes_negative_rebound_engulfing_and_board_breaks():
    current = {
        "code": "600001",
        "trade_date": "2026-11-27",
        "role": "leader",
        "height": 5,
    }
    daily_bars = [
        {"date": "2026-11-26", "open": 10.0, "close": 9.5},
        {"date": "2026-11-27", "open": 9.0, "close": 10.5},
    ]
    feedback = {
        "items": [{
            "code": "600001",
            "evidence": {"broken_count": 2},
        }],
    }
    result = build_leader_lifecycle(
        current,
        current_total_leader_code="600001",
        previous_snapshots=[],
        phase="fermentation",
        daily_bars=daily_bars,
        feedback=feedback,
    )
    assert "rebound_after_negative" in result["events"]
    assert "bullish_engulfing_after_negative" in result["events"]
    assert "intraday_board_break_observed" in result["events"]
    assert result["candle_context"]["bullish_engulfing_after_negative"] is True
    assert result["candle_context"]["board_break_count"] == 2
