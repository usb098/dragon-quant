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
