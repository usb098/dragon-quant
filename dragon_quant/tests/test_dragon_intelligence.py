from __future__ import annotations

import pytest

from dragon_quant.intelligence.engine import analyze_dragon_intelligence


def _snapshot(*, phase="fermentation", complete=True, role="leader",
              mainline_state="strengthening", trade_date="2026-11-26"):
    candidate = {
        "code": "600001", "name": "核心股A", "role": role,
        "role_confidence": "high", "role_basis": "板块内高度最高",
        "mainline": {"board_name": "机器人", "rank": 1,
                     "mainline_score": 90.0, "state": mainline_state},
        "mainline_rank": 1, "height": 5, "first_seal_time": "10:15:00",
        "limit_up_type": "换手板", "open_num": 1, "amount": 2.5e9,
        "turnover_rate": 18.0,
    }
    identified = complete and role == "leader"
    review = {
        "market": {"state": "strong", "score": 78},
        "emotion_cycle": {"phase": phase, "phase_label": phase},
        "mainlines": [{
            "board_name": "机器人", "rank": 1, "mainline_score": 90.0,
            "state": mainline_state, "limit_up_num": 8,
            "continuous_plate_num": 2, "concentration": 0.18,
        }],
        "leaders": {
            "coverage": {"complete": complete, "status": "complete" if complete else "partial",
                         "observed_total": 20, "reported_total": 20 if complete else 300},
            "space_board": {"height": 5, "count": 1, "stocks": [candidate]},
            "mainline_leaders": [candidate] if role == "leader" else [],
            "market_total_leader": {
                "status": "identified" if identified else "unconfirmed" if complete else "provisional",
                "code": "600001" if identified else None,
                "reason": "unique_space_board_is_mainline_leader",
                "confidence": "high" if identified else "low",
                "candidate": candidate,
                "candidates": [candidate],
            },
        },
        "review_candidates": [candidate],
    }
    return {"trade_date": trade_date, "review": review}


def test_confirmed_total_leader_is_explained_without_overwriting_review_scores():
    result = analyze_dragon_intelligence(_snapshot())
    assert result["status"] == "ready"
    assert result["read_only"] is True
    assert result["decision_impact"] is False
    assert result["total_leader"]["code"] == "600001"
    candidate = result["candidates"][0]
    assert candidate["identity"] == "total_leader"
    assert candidate["lifecycle"]["stage"] == "first_observation"
    assert candidate["cohesion"]["status"] == "partial_proxy"
    assert candidate["expectation_gap"]["status"] == "unknown"
    assert candidate["expert_opinions"][0]["stance"] == "supportive"


def test_incomplete_market_coverage_never_confirms_total_leader():
    result = analyze_dragon_intelligence(_snapshot(complete=False))
    assert result["total_leader"]["status"] == "provisional"
    assert result["total_leader"]["code"] is None
    assert result["candidates"][0]["identity"] != "total_leader"
    assert any("覆盖不完整" in item for item in result["candidates"][0]["expert_opinions"][0]["unknowns"])


def test_lifecycle_marks_possible_leader_handoff_without_claiming_confirmation():
    previous = _snapshot(trade_date="2026-11-25")
    previous["review"]["leaders"]["market_total_leader"]["code"] = "600009"
    previous["review"]["leaders"]["market_total_leader"]["candidate"]["code"] = "600009"
    result = analyze_dragon_intelligence(_snapshot(), previous_snapshot=previous)
    assert result["candidates"][0]["lifecycle"]["stage"] == "handoff_candidate"
    assert result["candidates"][0]["lifecycle"]["previous_total_leader_code"] == "600009"


def test_market_recession_changes_expert_stance_to_cautious():
    result = analyze_dragon_intelligence(_snapshot(phase="recession"))
    assert result["candidates"][0]["expert_opinions"][0]["stance"] == "cautious"
    assert "market_cycle_risk" in result["candidates"][0]["expert_opinions"][0]["risk_flags"]


def test_follower_role_is_not_promoted_to_total_leader():
    result = analyze_dragon_intelligence(_snapshot(role="follower"))
    assert result["candidates"][0]["identity"] == "follower"
    assert result["candidates"][0]["is_total_leader"] is False


def test_only_one_expert_is_not_reported_as_multi_expert_consensus():
    result = analyze_dragon_intelligence(_snapshot())
    assert result["collaboration"]["status"] == "single_expert"
    assert result["collaboration"]["consensus_stance"] is None


def test_unknown_expert_is_rejected():
    with pytest.raises(ValueError, match="未知理念专家"):
        analyze_dragon_intelligence(_snapshot(), expert_ids=["not_registered"])


def test_missing_review_snapshot_returns_read_only_unavailable_result():
    result = analyze_dragon_intelligence({"trade_date": "2026-11-26"})
    assert result["status"] == "unavailable"
    assert result["read_only"] is True
    assert result["decision_impact"] is False
    assert result["candidates"] == []



def test_divergent_experts_preserve_disagreement_without_averaging():
    from dragon_quant.intelligence.engine import _collaboration_status

    candidates = [{
        "code": "600001",
        "is_total_leader": True,
        "expert_opinions": [
            {"stance": "supportive"},
            {"stance": "cautious"},
        ],
    }]
    experts = [
        {"meta": {"id": "chen_xiaoqun"}},
        {"meta": {"id": "expert_two"}},
    ]
    result = _collaboration_status(candidates, experts)
    assert result["status"] == "divergent"
    assert result["consensus_stance"] is None
    assert result["active_expert_ids"] == ["chen_xiaoqun", "expert_two"]


def test_no_enabled_experts_does_not_claim_single_expert_consensus():
    from dragon_quant.intelligence.engine import _collaboration_status

    result = _collaboration_status(
        [{"code": "600001", "is_total_leader": True, "expert_opinions": []}],
        [],
    )
    assert result["status"] == "insufficient_evidence"
    assert result["consensus_stance"] is None
