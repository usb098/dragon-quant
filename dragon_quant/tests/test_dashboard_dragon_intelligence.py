from __future__ import annotations

from web_ui.backend.routers.assets import prep_dragon_intelligence


class FakeAssets:
    def __init__(self, current, previous=None):
        self.current = current
        self.previous = previous

    def get_prep_snapshot(self, trade_date, source):
        assert trade_date == "2026-11-26"
        assert source == "v2"
        return self.current

    def get_previous_prep_snapshot(self, trade_date, source):
        return self.previous, {}


def _snapshot():
    candidate = {
        "code": "600001", "name": "龙头A", "role": "leader",
        "role_confidence": "high", "height": 5, "mainline_rank": 1,
        "mainline": {"board_name": "机器人", "rank": 1, "state": "strengthening"},
    }
    return {
        "trade_date": "2026-11-26",
        "review": {
            "market": {"state": "strong", "score": 80},
            "emotion_cycle": {"phase": "fermentation", "phase_label": "发酵"},
            "mainlines": [{"board_name": "机器人", "rank": 1, "limit_up_num": 7}],
            "leaders": {
                "coverage": {"complete": True, "status": "complete"},
                "space_board": {"stocks": [candidate], "height": 5, "count": 1},
                "mainline_leaders": [candidate],
                "market_total_leader": {
                    "status": "identified", "code": "600001",
                    "confidence": "high", "candidate": candidate, "candidates": [candidate],
                },
            },
            "review_candidates": [candidate],
        },
    }


def test_dragon_intelligence_endpoint_is_read_only_and_returns_expert_opinions():
    result = prep_dragon_intelligence(
        "2026-11-26", source="v2", experts=None, assets=FakeAssets(_snapshot())
    )
    assert result["read_only"] is True
    assert result["decision_impact"] is False
    assert result["active_expert_ids"] == ["chen_xiaoqun"]
    assert result["collaboration"]["status"] == "single_expert"
    assert result["candidates"][0]["expert_opinions"][0]["expert_id"] == "chen_xiaoqun"



def test_agent_status_does_not_expose_api_key(monkeypatch):
    from web_ui.backend.routers.assets import dragon_intelligence_agent_status

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("DQ_INTELLIGENCE_LLM_ENABLED", "1")
    payload = dragon_intelligence_agent_status()
    assert payload["configured"] is False
    assert payload["enabled"] is False
    assert payload["status"] == "missing_api_key"
    assert "OPENAI_API_KEY" not in payload
