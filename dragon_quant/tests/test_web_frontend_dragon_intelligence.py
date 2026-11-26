from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "web_ui" / "frontend" / "src"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_prep_page_loads_read_only_dragon_intelligence_endpoint():
    page = _read(SRC / "pages" / "prep" / "PrepPage.tsx")
    api = _read(SRC / "api" / "assets.ts")
    core = _read(SRC / "pages" / "prep" / "PrepCoreResult.tsx")
    assert "fetchPrepDragonIntelligence" in page
    assert "dragonIntelligence" in page
    assert "/dragon-intelligence" in api
    assert "DragonIntelligencePanel" in core


def test_dragon_intelligence_panel_preserves_opinions_and_unknowns():
    panel = _read(SRC / "pages" / "prep" / "DragonIntelligencePanel.tsx")
    for field in ("evidence_for", "evidence_against", "unknowns", "risk_flags",
                  "collaboration.note", "limitations", "next_checks"):
        assert field in panel
    assert "不改变现有评分、资格、仓位或买卖规则" in panel
    assert "single_expert" in panel
    assert "divergent" in panel
    assert "non_comparable" in panel
    assert "opinions.map" in panel
    assert "candidate.collaboration.note" in panel
    assert "expert.market_scope.join" in panel


def test_frontend_does_not_treat_the_expert_as_a_trading_signal():
    panel = _read(SRC / "pages" / "prep" / "DragonIntelligencePanel.tsx")
    assert "买入" not in panel
    assert "卖出" not in panel



def test_prep_page_runs_llm_agent_only_after_explicit_click():
    page = _read(SRC / "pages" / "prep" / "PrepPage.tsx")
    api = _read(SRC / "api" / "assets.ts")
    panel = _read(SRC / "pages" / "prep" / "DragonIntelligencePanel.tsx")
    assert "fetchDragonAgentStatus" in page
    assert "runPrepDragonAgent(date)" in page
    assert "onRunAgent={runAgent}" in page
    assert "/api/intelligence/agent/status" in api
    assert "LLM Agent 研究" in panel
    assert "sent_private_documents" in api


def test_panel_shows_frozen_expectation_and_observable_lifecycle_events():
    panel = _read(SRC / "pages" / "prep" / "DragonIntelligencePanel.tsx")
    for token in (
        "frozen_previous_plan_feedback",
        "actual_gap_pct",
        "expected_gap_high",
        "bullish_engulfing_after_negative",
        "first_negative_in_observed_window",
        "intraday_board_break_observed",
    ):
        assert token in panel
