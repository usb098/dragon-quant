from __future__ import annotations

import copy

from dragon_quant.review_account.prep.review.leader_analysis import (
    build_leader_analysis,
    classify_emotion_cycle,
)


def _pool(rows, *, total=None, truncated=False):
    result = {"rows": rows, "truncated": truncated}
    if total is not None:
        result["total"] = total
    return result


def _role(mainline="机器人", *, confidence="high"):
    return {
        "role": "leader",
        "role_confidence": confidence,
        "role_basis": "板块内高度最高",
        "mainline": {"board_name": mainline, "rank": 1, "mainline_score": 92.0,
                     "state": "strengthening"},
        "evidence": {"height": 5, "first_seal_time": "09:35:00", "amount": 1e9},
    }


def _row(code, height, **kwargs):
    row = {"code": code, "name": f"股票{code}", "high_num": height,
           "limit_up_type": "换手板", "first_limit_up_time": "09:35:00"}
    row.update(kwargs)
    return row


def test_unique_space_board_and_mainline_leader_is_identified():
    rows = [_row("600001", 5), _row("600002", 3), _row("600003", 2)]
    result = build_leader_analysis(
        _pool(rows, total=3),
        [{"board_name": "机器人", "rank": 1, "mainline_score": 92.0,
          "state": "strengthening"}],
        {"600001": _role()},
    )
    assert result["space_board"]["height"] == 5
    assert result["space_board"]["stocks"][0]["code"] == "600001"
    assert [item["height"] for item in result["ladder"]] == [5, 3, 2]
    assert result["market_total_leader"]["status"] == "identified"
    assert result["market_total_leader"]["code"] == "600001"


def test_equal_top_height_is_contested_even_with_one_mainline_leader():
    result = build_leader_analysis(
        _pool([_row("600001", 5), _row("600002", 5)], total=2),
        [{"board_name": "机器人", "rank": 1, "mainline_score": 90.0}],
        {"600001": _role()},
    )
    assert result["market_total_leader"]["status"] == "contested"
    assert result["market_total_leader"]["code"] is None
    assert len(result["market_total_leader"]["candidates"]) == 2


def test_incomplete_pool_never_confirms_total_leader():
    result = build_leader_analysis(
        _pool([_row("600001", 5)], total=300, truncated=True),
        [{"board_name": "机器人", "rank": 1, "mainline_score": 90.0}],
        {"600001": _role()},
    )
    assert result["coverage"]["complete"] is False
    assert result["market_total_leader"]["status"] == "provisional"
    assert result["market_total_leader"]["code"] is None


def test_space_board_without_mainline_leader_is_unconfirmed():
    result = build_leader_analysis(
        _pool([_row("600001", 7), _row("600002", 5)], total=2),
        [{"board_name": "机器人", "rank": 1, "mainline_score": 90.0}],
        {"600002": _role()},
    )
    assert result["market_total_leader"]["status"] == "unconfirmed"
    assert result["market_total_leader"]["reason"] == "space_board_not_mainline_leader"


def test_packed_board_height_is_decoded_and_rows_are_not_mutated():
    rows = [_row("600001", 5), {"code": "600002", "name": "高标B",
             "high_num": 0x00060004, "high": "6天4板"}]
    before = copy.deepcopy(rows)
    result = build_leader_analysis(_pool(rows, total=2), [], {})
    assert result["space_board"]["height"] == 5
    assert rows == before


def test_missing_pool_is_explicitly_unavailable():
    result = build_leader_analysis(None, [], {})
    assert result["coverage"]["status"] == "missing"
    assert result["market_total_leader"]["status"] == "unavailable"
    assert result["market_total_leader"]["reason"] == "limit_up_pool_missing"


def test_emotion_cycle_uses_prev_snapshot_for_cycle_phases():
    startup = classify_emotion_cycle({"state": "neutral", "prev_state": "ice",
                                      "score_change": 8.0})
    fermentation = classify_emotion_cycle({"state": "neutral", "prev_state": "neutral",
                                           "score_change": 5.0})
    climax = classify_emotion_cycle({"state": "strong", "prev_state": "strong",
                                     "score_change": 1.0})
    recession = classify_emotion_cycle({"state": "weak", "prev_state": "strong",
                                        "score_change": -18.0})
    ice = classify_emotion_cycle({"state": "ice", "prev_state": "weak",
                                  "score_change": -10.0})
    assert startup["phase"] == "startup"
    assert fermentation["phase"] == "fermentation"
    assert climax["phase"] == "climax"
    assert recession["phase"] == "recession"
    assert ice["phase"] == "ice"


def test_first_neutral_snapshot_does_not_guess_cycle_phase():
    result = classify_emotion_cycle(
        {"state": "neutral", "prev_state": None, "score_change": None}
    )
    assert result["phase"] == "unknown"
    assert result["phase_label"] == "待观察"
    assert result["informational_only"] is True
