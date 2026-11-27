"""面向复盘研究的服务端 LLM Agent（OpenAI Responses API）。

只传入脱敏后的结构化研究摘要；不会读取原始交割单、用户文件或私有知识库。
默认关闭，不配置 API Key，不会调用外部模型。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Mapping


class AgentNotConfigured(RuntimeError):
    pass


class AgentDisabled(RuntimeError):
    pass


class AgentRequestError(RuntimeError):
    pass


def _enabled() -> bool:
    return os.getenv("DQ_INTELLIGENCE_LLM_ENABLED", "0").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _web_search_enabled() -> bool:
    return os.getenv("DQ_INTELLIGENCE_WEB_SEARCH", "0").strip().lower() in {
        "1", "true", "yes", "on",
    }


def agent_status() -> dict:
    """不返回密钥，只报告部署配置是否就绪。"""
    has_key = bool(os.getenv("OPENAI_API_KEY", "").strip())
    enabled = _enabled()
    return {
        "provider": "openai_responses",
        "enabled": enabled and has_key,
        "configured": has_key,
        "web_search_enabled": enabled and has_key and _web_search_enabled(),
        "model": os.getenv("DQ_INTELLIGENCE_LLM_MODEL", "gpt-6.2-astra"),
        "status": "ready" if enabled and has_key else (
            "disabled" if not enabled else "missing_api_key"
        ),
        "detail": (
            "已启用；点击后才会调用模型。"
            if enabled and has_key else
            "LLM 默认关闭；需在服务端设置 OPENAI_API_KEY 和 DQ_INTELLIGENCE_LLM_ENABLED=1。"
            if not enabled else
            "已启用开关但缺少 OPENAI_API_KEY；请在服务端密钥管理中配置。"
        ),
    }


def _compact_candidate(row: Mapping[str, Any]) -> dict:
    structure = row.get("structure") if isinstance(row.get("structure"), Mapping) else {}
    cohesion = row.get("cohesion") if isinstance(row.get("cohesion"), Mapping) else {}
    expectation = row.get("expectation_gap") if isinstance(row.get("expectation_gap"), Mapping) else {}
    lifecycle = row.get("lifecycle") if isinstance(row.get("lifecycle"), Mapping) else {}
    opinions = row.get("expert_opinions")
    opinion_summary = []
    if isinstance(opinions, list):
        for item in opinions[:5]:
            if not isinstance(item, Mapping):
                continue
            decision = item.get("decision_framework")
            decision = decision if isinstance(decision, Mapping) else {}
            mode_assessments = decision.get("mode_assessments")
            mode_assessments = mode_assessments if isinstance(mode_assessments, list) else []
            opinion_summary.append({
                "expert": item.get("expert_name"),
                "stance": item.get("stance"),
                "confidence": item.get("confidence"),
                "summary": item.get("summary"),
                "unknowns": item.get("unknowns", [])[:4]
                if isinstance(item.get("unknowns"), list) else [],
                "decision_framework": {
                    "status": decision.get("status"),
                    "preferred_mode": decision.get("preferred_mode"),
                    "selection_tier": decision.get("selection_tier"),
                    "mode_assessments": [
                        {
                            "mode": row.get("mode"),
                            "status": row.get("status"),
                            "blockers": row.get("blockers", [])[:3],
                            "required_confirmations": row.get("required_confirmations", [])[:4],
                        }
                        for row in mode_assessments[:5]
                        if isinstance(row, Mapping)
                    ],
                },
            })
    return {
        "code": row.get("code"),
        "name": row.get("name"),
        "identity": row.get("identity"),
        "role": row.get("role"),
        "mainline": structure.get("mainline_name"),
        "mainline_rank": structure.get("mainline_rank"),
        "mainline_state": structure.get("mainline_state"),
        "board_height": structure.get("height"),
        "first_seal_time": structure.get("first_seal_time"),
        "open_count": structure.get("open_num"),
        "amount": structure.get("amount"),
        "turnover_rate": structure.get("turnover_rate"),
        "cohesion": {
            "status": cohesion.get("status"),
            "member_count": cohesion.get("member_count"),
            "coverage_ratio": cohesion.get("coverage_ratio"),
            "advancer_ratio": cohesion.get("advancer_ratio"),
            "pairwise_correlation": cohesion.get("pairwise_correlation"),
            "synchronized_up_ratio": cohesion.get("synchronized_up_ratio"),
            "synchronized_down_ratio": cohesion.get("synchronized_down_ratio"),
        },
        "expectation_gap": {
            "status": expectation.get("status"),
            "basis": expectation.get("basis"),
            "note": expectation.get("note"),
            "positive_evidence": expectation.get("positive_evidence", []),
            "negative_evidence": expectation.get("negative_evidence", []),
        },
        "lifecycle": {
            "stage": lifecycle.get("stage"),
            "observation_count": lifecycle.get("observation_count"),
            "events": lifecycle.get("events", []),
        },
        "expert_opinions": opinion_summary,
    }


def _research_facts(result: Mapping[str, Any]) -> dict:
    candidates = result.get("candidates")
    rows = [
        _compact_candidate(item)
        for item in candidates[:12]
        if isinstance(item, Mapping)
    ] if isinstance(candidates, list) else []
    return {
        "trade_date": result.get("trade_date"),
        "market": result.get("market"),
        "coverage": result.get("coverage"),
        "total_leader": result.get("total_leader"),
        "collaboration": result.get("collaboration"),
        "candidates": rows,
        "limitations": result.get("limitations", []),
    }


_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "stance": {"type": "string", "enum": [
            "supportive", "neutral", "cautious", "insufficient_evidence",
        ]},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "summary": {"type": "string"},
        "key_agreement": {"type": "array", "items": {"type": "string"}},
        "key_disagreement": {"type": "array", "items": {"type": "string"}},
        "evidence_for": {"type": "array", "items": {"type": "string"}},
        "evidence_against": {"type": "array", "items": {"type": "string"}},
        "unknowns": {"type": "array", "items": {"type": "string"}},
        "next_checks": {"type": "array", "items": {"type": "string"}},
        "caveats": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "stance", "confidence", "summary", "key_agreement", "key_disagreement",
        "evidence_for", "evidence_against", "unknowns", "next_checks", "caveats",
    ],
}


def _parse_response(payload: Mapping[str, Any]) -> tuple[dict, list[dict]]:
    if payload.get("status") == "incomplete":
        details = payload.get("incomplete_details")
        raise AgentRequestError(f"模型输出不完整：{details or 'token_limit_or_interrupted'}")
    texts: list[str] = []
    citations: list[dict] = []
    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, Mapping) or item.get("type") != "message":
                continue
            contents = item.get("content")
            if not isinstance(contents, list):
                continue
            for content in contents:
                if not isinstance(content, Mapping):
                    continue
                if content.get("type") == "refusal":
                    raise AgentRequestError("模型拒绝了本次研究请求。")
                if content.get("type") == "output_text":
                    value = content.get("text")
                    if isinstance(value, str):
                        texts.append(value)
                    annotations = content.get("annotations")
                    if isinstance(annotations, list):
                        for annotation in annotations:
                            if not isinstance(annotation, Mapping):
                                continue
                            if annotation.get("type") == "url_citation":
                                url = annotation.get("url")
                                if isinstance(url, str) and url.startswith(("https://", "http://")):
                                    citations.append({
                                        "title": annotation.get("title") or url,
                                        "url": url,
                                    })
    if not texts:
        raise AgentRequestError("模型响应没有可解析的结构化文本。")
    try:
        result = json.loads("\n".join(texts))
    except json.JSONDecodeError as exc:
        raise AgentRequestError("模型返回内容不是有效 JSON。") from exc
    if not isinstance(result, dict):
        raise AgentRequestError("模型输出结构不符合预期。")
    deduped: list[dict] = []
    seen: set[str] = set()
    for citation in citations:
        if citation["url"] not in seen:
            seen.add(citation["url"])
            deduped.append(citation)
    return result, deduped


def run_research(deterministic_result: Mapping[str, Any]) -> dict:
    """显式执行一次研究分析。不会保存原文或把文档传给模型。"""
    status = agent_status()
    if not status["configured"]:
        raise AgentNotConfigured("尚未配置 OPENAI_API_KEY。")
    if not status["enabled"]:
        raise AgentDisabled("LLM Agent 当前处于关闭状态。")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("DQ_INTELLIGENCE_LLM_MODEL", "gpt-6.2-astra").strip()
    endpoint = os.getenv("DQ_INTELLIGENCE_RESPONSES_URL", "https://api.openai.com/v1/responses").strip()
    timeout_raw = os.getenv("DQ_INTELLIGENCE_LLM_TIMEOUT", "60")
    try:
        timeout = max(5, min(180, int(timeout_raw)))
    except ValueError:
        timeout = 60
    facts = _research_facts(deterministic_result)
    instructions = (
        "你是A股龙头研究分析Agent，不是任何真实游资本人。"
        "只根据输入的结构化事实分析，不得把未知数据补成事实，不得预测确定涨跌，不得生成具体买卖价、仓位或下单指令。"
        "区分量化事实、前序快照代理判断和你的研究推断。"
        "输入中的 expectation_gap 是前序复盘框架代理，不是真实市场一致预期。"
        "cohesion 只有 status=measured 时才可作为成分股同步证据；partial_proxy/unknown 不可表述为已测得合力。"
        "生命周期数据只覆盖已保存快照，不能把观察快照连续数说成真实连续交易日。"
        "若启用了 web_search，只能用带来源的公开信息补充政策/产业催化和市场背景；"
        "来源缺失、数据冲突或信息时间不清楚时，放入 unknowns。"
        "模式选择器的 conditional_setup 只代表观察清单，不是买点；blocked 必须保留为否决。"
        "你只能评估模式条件是否得到输入证据支持，不得替代确定性模式选择器，也不得提出具体买卖动作、价格或仓位。"
        "返回结构化研究结论，不要模仿某位交易者的口吻。"
    )
    user_input = (
        "请对这份只读量化研究摘要做交叉验证，识别主线与龙头的支持证据、反向证据和数据缺口。"
        "不得把本次研究结果回写成当时已知的事前预期。\n"
        + json.dumps(facts, ensure_ascii=False, separators=(",", ":"))
    )
    request_body: dict[str, Any] = {
        "model": model,
        "instructions": instructions,
        "input": user_input,
        "store": False,
        "max_output_tokens": 1800,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "dragon_intelligence_research",
                "strict": True,
                "schema": _SCHEMA,
            }
        },
    }
    web_search = _web_search_enabled()
    if web_search:
        request_body["tools"] = [{"type": "web_search", "search_context_size": "medium"}]

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(3_000_001)
    except urllib.error.HTTPError as exc:
        detail = exc.read(3000).decode("utf-8", errors="replace")
        raise AgentRequestError(f"OpenAI API 返回 HTTP {exc.code}：{detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AgentRequestError(f"连接 OpenAI Responses API 失败：{type(exc).__name__}") from exc
    if len(raw) > 3_000_000:
        raise AgentRequestError("模型响应超过 3 MB 安全上限。")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AgentRequestError("OpenAI API 响应不是有效 JSON。") from exc
    if not isinstance(payload, Mapping):
        raise AgentRequestError("OpenAI API 响应结构不符合预期。")
    analysis, citations = _parse_response(payload)
    return {
        "provider": "openai_responses",
        "model": model,
        "web_search_enabled": web_search,
        "trade_date": deterministic_result.get("trade_date"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis": analysis,
        "citations": citations,
        "read_only": True,
        "decision_impact": False,
        "sent_private_documents": False,
        "note": "LLM 研究仅消费结构化复盘摘要，不读取或上传原始交割单、私有心法和其他用户文件。",
    }


__all__ = [
    "AgentDisabled",
    "AgentNotConfigured",
    "AgentRequestError",
    "agent_status",
    "run_research",
]
