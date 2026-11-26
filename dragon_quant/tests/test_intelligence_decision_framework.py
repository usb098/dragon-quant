from __future__ import annotations

from dragon_quant.intelligence.decision_framework import build_decision_framework


def _candidate(
    *,
    phase="fermentation",
    market_state="strong",
    role="leader",
    mainline_state="strengthening",
    complete=True,
    cohesion_status="measured",
    advancer_ratio=0.67,
    expectation_status="above_prior_expectation",
    events=None,
    is_total_leader=True,
):
    return {
        "role": role,
        "is_total_leader": is_total_leader,
        "is_space_board": True,
        "structure": {
            "mainline_state": mainline_state,
            "mainline_rank": 1,
            "limit_up_type": "换手板",
            "open_num": 1,
            "first_seal_time": "10:15:00",
        },
        "cohesion": {
            "status": cohesion_status,
            "advancer_ratio": advancer_ratio,
            "pairwise_correlation": 0.12,
        },
        "expectation_gap": {"status": expectation_status},
        "lifecycle": {"events": events or []},
    }, {
        "market": {"phase": phase, "state": market_state},
        "coverage_complete": complete,
    }


def test_core_leader_in_fermentation_prefers_conditional_breakout_watch():
    candidate, context = _candidate()
    result = build_decision_framework(context, candidate)
    assert result["status"] == "conditional_watch"
    assert result["preferred_mode"] == "breakout_follow"
    board = next(row for row in result["mode_assessments"] if row["mode"] == "breakout_follow")
    assert board["status"] == "conditional_setup"
    assert result["can_execute"] is False
    assert result["decision_impact"] is False
    assert any("竞价" in item for item in board["required_confirmations"])


def test_first_negative_switches_priority_from_breakout_to_pullback():
    candidate, context = _candidate(events=["first_negative_in_observed_window"])
    result = build_decision_framework(context, candidate)
    assert result["preferred_mode"] == "pullback_absorption"
    mode = next(row for row in result["mode_assessments"] if row["mode"] == "pullback_absorption")
    assert mode["status"] == "conditional_setup"


def test_rebound_after_negative_prefers_repair_not_unconditional_dip_buy():
    candidate, context = _candidate(events=[
        "first_negative_in_observed_window", "rebound_after_negative",
    ])
    result = build_decision_framework(context, candidate)
    assert result["preferred_mode"] == "repair_rebound"


def test_recession_or_ice_forces_stand_aside():
    candidate, context = _candidate(phase="recession")
    result = build_decision_framework(context, candidate)
    assert result["status"] == "stand_aside"
    assert result["preferred_mode"] == "none"
    assert result["can_execute"] is False


def test_weakening_mainline_blocks_new_risk_modes():
    candidate, context = _candidate(mainline_state="weakening")
    result = build_decision_framework(context, candidate)
    assert result["status"] == "stand_aside"
    assert "所属主线正在走弱" in result["hard_risks"]


def test_follower_is_deprioritized_even_in_good_market():
    candidate, context = _candidate(role="follower", is_total_leader=False)
    result = build_decision_framework(context, candidate)
    assert result["status"] == "stand_aside"
    assert result["selection_tier"] == "D_low_priority"


def test_missing_coverage_cohesion_and_expectation_never_invent_confirmation():
    candidate, context = _candidate(
        complete=False,
        cohesion_status="unknown",
        expectation_status="unknown",
    )
    result = build_decision_framework(context, candidate)
    board = next(row for row in result["mode_assessments"] if row["mode"] == "breakout_follow")
    assert result["gates"]["market_coverage_complete"] is False
    assert result["gates"]["cohesion_measured"] is False
    assert result["gates"]["expectation_status"] == "unknown"
    assert any("竞价" in item for item in board["required_confirmations"])
    assert result["can_execute"] is False


def test_unknown_market_phase_is_insufficient_data():
    candidate, context = _candidate(phase="unknown")
    result = build_decision_framework(context, candidate)
    assert result["status"] == "insufficient_data"
    assert result["preferred_mode"] == "none"
