from __future__ import annotations

import pytest

from dragon_quant.intelligence.llm_agent import (
    AgentDisabled,
    AgentNotConfigured,
    _parse_response,
    agent_status,
    run_research,
)


def test_agent_is_disabled_by_default_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DQ_INTELLIGENCE_LLM_ENABLED", raising=False)
    status = agent_status()
    assert status["enabled"] is False
    assert status["configured"] is False
    assert status["status"] == "disabled"
    with pytest.raises(AgentNotConfigured):
        run_research({"trade_date": "2026-11-27"})


def test_agent_with_key_but_disabled_does_not_call_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "not-a-real-key")
    monkeypatch.setenv("DQ_INTELLIGENCE_LLM_ENABLED", "0")
    with pytest.raises(AgentDisabled):
        run_research({"trade_date": "2026-11-27"})


def test_parser_extracts_structured_result_and_web_citations():
    payload = {
        "status": "completed",
        "output": [{
            "type": "message",
            "content": [{
                "type": "output_text",
                "text": '{"stance":"neutral"}',
                "annotations": [{
                    "type": "url_citation",
                    "url": "https://example.com/research",
                    "title": "公开来源",
                }],
            }],
        }],
    }
    result, citations = _parse_response(payload)
    assert result["stance"] == "neutral"
    assert citations == [{
        "title": "公开来源",
        "url": "https://example.com/research",
    }]


def test_parser_rejects_incomplete_response():
    with pytest.raises(Exception, match="模型输出不完整"):
        _parse_response({
            "status": "incomplete",
            "incomplete_details": {"reason": "max_output_tokens"},
        })
