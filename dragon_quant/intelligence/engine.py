"""龙头理解引擎：结构化候选、客观证据、独立专家观点与分歧编排。

纯函数：只消费已保存的 prep 快照；不读文件/数据库/网络/时钟，不修改策略或仓位。
"""

from __future__ import annotations

import math
from typing import Any, Mapping

from .registry import list_experts, resolve_experts

_ROLE_ORDER = {"leader": 0, "vanguard": 1, "mainstay": 2, "capacity": 3, "follower": 4}
_IDENTITY_LABELS = {
    "total_leader": "总龙头",
    "mainline_leader": "主线龙头",
    "vanguard": "先锋",
    "mainstay": "中军",
    "capacity": "容量核心",
    "follower": "跟风",
    "unconfirmed": "待确认",
}
_STAGE_LABELS = {
    "first_observation": "首次观察",
    "handoff_candidate": "新老龙交接候选",
    "continuing": "延续",
    "strengthening": "强化",
    "climax": "高潮观察",
    "weakening": "走弱观察",
    "sector_leader": "主线核心",
    "emerging": "潜在新核心",
    "risk_watch": "风险观察",
    "watch": "持续观察",
}


def _dict(value: Any) -> dict:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[dict]:
    return [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _old_total_leader(previous_snapshot: Any) -> str | None:
    previous_review = _dict(_dict(previous_snapshot).get("review"))
    previous_leaders = _dict(previous_review.get("leaders"))
    total = _dict(previous_leaders.get("market_total_leader"))
    return _text(total.get("code"))


def _build_candidate_rows(
    review: Mapping[str, Any],
    leaders: Mapping[str, Any],
    mainlines: list[dict],
    previous_snapshot: Any,
    phase: str,
) -> list[dict]:
    rows: dict[str, dict] = {}

    def add(raw: Mapping[str, Any], source: str) -> None:
        code = _text(raw.get("code"))
        if not code:
            return
        current = rows.setdefault(code, {"code": code, "sources": []})
        if source not in current["sources"]:
            current["sources"].append(source)
        for key, value in raw.items():
            if value is not None and value != "":
                current[key] = value
        current["code"] = code

    for row in _list(review.get("review_candidates")):
        add(row, "review_candidates")
    for row in _list(leaders.get("mainline_leaders")):
        add(row, "mainline_leaders")
    space = _dict(leaders.get("space_board"))
    for row in _list(space.get("stocks")):
        add(row, "space_board")
    total = _dict(leaders.get("market_total_leader"))
    total_candidate = _dict(total.get("candidate"))
    if total_candidate:
        add(total_candidate, "market_total_leader")

    mainline_by_name = {
        _text(item.get("board_name")): item
        for item in mainlines
        if _text(item.get("board_name"))
    }
    previous_code = _old_total_leader(previous_snapshot)
    total_status = _text(total.get("status")) or "unavailable"
    total_code = _text(total.get("code"))
    coverage_complete = _dict(leaders.get("coverage")).get("complete") is True
    output: list[dict] = []

    for code, raw in rows.items():
        role = _text(raw.get("role"))
        mainline_raw = raw.get("mainline")
        mainline = _dict(mainline_raw)
        mainline_name = (
            _text(mainline.get("board_name"))
            or _text(mainline_raw if isinstance(mainline_raw, str) else None)
        )
        board = mainline_by_name.get(mainline_name, {})
        rank = _number(mainline.get("rank"))
        if rank is None:
            rank = _number(raw.get("mainline_rank"))
        if rank is None:
            rank = _number(board.get("rank"))
        mainline_state = (
            _text(mainline.get("state"))
            or _text(raw.get("mainline_state"))
            or _text(board.get("state"))
        )
        mainline_score = (
            _number(mainline.get("mainline_score"))
            or _number(raw.get("mainline_score"))
            or _number(board.get("mainline_score"))
        )
        height = _number(raw.get("height"))
        is_total = total_status == "identified" and total_code == code and coverage_complete and role == "leader"
        is_space = any(item.get("code") == code for item in _list(space.get("stocks")))
        identity = (
            "total_leader" if is_total else
            "mainline_leader" if role == "leader" else
            role if role in ("vanguard", "mainstay", "capacity", "follower") else
            "unconfirmed"
        )
        confidence = _text(raw.get("role_confidence")) or "low"
        if is_total:
            confidence = _text(total.get("confidence")) or confidence
        elif role is None:
            confidence = "unknown"

        if is_total:
            if previous_code == code:
                if phase == "climax":
                    stage = "climax"
                elif phase == "recession" or mainline_state == "weakening":
                    stage = "weakening"
                elif phase in ("startup", "fermentation") or mainline_state == "strengthening":
                    stage = "strengthening"
                else:
                    stage = "continuing"
            elif previous_code:
                stage = "handoff_candidate"
            else:
                stage = "first_observation"
        elif role == "leader":
            stage = "sector_leader"
        elif role == "vanguard":
            stage = "emerging"
        elif phase in ("ice", "recession"):
            stage = "risk_watch"
        else:
            stage = "watch"

        cohesion_count = _number(board.get("limit_up_num"))
        if cohesion_count is None:
            cohesion_count = _number(raw.get("board_limit_up_num"))
        continuity = _number(board.get("continuous_plate_num"))
        concentration = _number(board.get("concentration"))
        cohesion_known = any(value is not None for value in (cohesion_count, continuity, concentration))
        cohesion = {
            "status": "partial_proxy" if cohesion_known else "unknown",
            "limit_up_num": cohesion_count,
            "continuous_plate_num": continuity,
            "concentration": concentration,
            "note": "板块静态指标只能作为扩散代理，不能替代成分股联动时间序列。",
        }
        structure = {
            "height": int(height) if height is not None and height.is_integer() else height,
            "mainline_name": mainline_name,
            "mainline_rank": int(rank) if rank is not None and rank.is_integer() else rank,
            "mainline_score": mainline_score,
            "mainline_state": mainline_state,
            "role": role,
            "role_confidence": confidence,
            "role_basis": _text(raw.get("role_basis")),
            "is_space_board": is_space,
            "first_seal_time": _text(raw.get("first_seal_time")),
            "limit_up_type": _text(raw.get("limit_up_type")),
            "open_num": _number(raw.get("open_num")),
            "amount": _number(raw.get("amount")),
            "turnover_rate": _number(raw.get("turnover_rate")),
            "main_net_amount": _number(raw.get("main_net_amount")),
            "is_one_word": raw.get("is_one_word") is True,
        }
        output.append({
            "code": code,
            "name": _text(raw.get("name")),
            "identity": identity,
            "identity_label": _IDENTITY_LABELS[identity],
            "role": role,
            "confidence": confidence,
            "is_total_leader": is_total,
            "is_space_board": is_space,
            "sources": list(raw["sources"]),
            "structure": structure,
            "cohesion": cohesion,
            "expectation_gap": {
                "status": "unknown",
                "reason": "no_independent_market_consensus_baseline",
            },
            "lifecycle": {
                "stage": stage,
                "label": _STAGE_LABELS[stage],
                "previous_total_leader_code": previous_code,
                "scope": "基于当前快照与最近一份前序快照的粗粒度观察，不等同于完整生命周期识别。",
            },
            "expert_opinions": [],
        })

    output.sort(key=lambda item: (
        0 if item["is_total_leader"] else 1,
        _ROLE_ORDER.get(item.get("role"), 9),
        item["structure"]["mainline_rank"] if item["structure"]["mainline_rank"] is not None else 999,
        -(item["structure"]["height"] or 0),
        item["code"],
    ))
    return output


def _collaboration_for_opinions(
    opinions: list[dict], active_experts: list[dict]
) -> dict:
    if not opinions:
        return {
            "status": "insufficient_evidence",
            "consensus_stance": None,
            "note": "当前没有候选的专家观点；只展示客观量化证据，不形成理念判断。",
        }
    if len(active_experts) > 1:
        profiles: set[tuple[tuple[str, ...], str]] = set()
        for expert in active_experts:
            meta = expert.get("meta") if isinstance(expert, Mapping) else {}
            meta = meta if isinstance(meta, Mapping) else {}
            scope = meta.get("market_scope")
            horizon = meta.get("time_horizon")
            if not isinstance(scope, list) or not scope or not isinstance(horizon, str) or not horizon:
                return {
                    "status": "non_comparable",
                    "consensus_stance": None,
                    "note": "至少一位专家未声明适用市场或持有周期；先分别展示，不强行合并观点。",
                }
            profiles.add((tuple(sorted(str(item) for item in scope)), horizon))
        if len(profiles) > 1:
            return {
                "status": "non_comparable",
                "consensus_stance": None,
                "note": "专家适用市场或持有周期不同；按各自适用范围分组观察，不把不同交易系统做投票。",
            }

    stances = [
        item.get("stance") for item in opinions
        if item.get("stance") not in (None, "insufficient_evidence")
    ]
    unique = sorted(set(stances))
    if not active_experts:
        status = "insufficient_evidence"
        consensus = None
        note = "当前没有启用专家；只展示客观量化证据，不形成理念判断。"
    elif len(active_experts) == 1:
        status = "single_expert"
        consensus = None
        note = "当前只有一位独立专家启用；展示其单独观点，不称为多专家共识。"
    elif not stances:
        status = "insufficient_evidence"
        consensus = None
        note = "专家均缺少足够证据，保留未知，不强行合成结论。"
    elif len(unique) == 1 and len(stances) == len(active_experts):
        status = "aligned"
        consensus = unique[0]
        note = "专家方向一致；仍保留各自证据链，不做分数平均。"
    else:
        status = "divergent"
        consensus = None
        note = "专家观点存在分歧；分别展示支持与反对证据，不以平均分掩盖冲突。"
    return {"status": status, "consensus_stance": consensus, "note": note}


def _collaboration_status(candidate_rows: list[dict], active_experts: list[dict]) -> dict:
    target = next((row for row in candidate_rows if row["is_total_leader"]), None)
    target = target or (candidate_rows[0] if candidate_rows else None)
    opinions = target.get("expert_opinions", []) if target else []
    summary = _collaboration_for_opinions(opinions, active_experts)
    return {
        **summary,
        "active_expert_ids": [item["meta"]["id"] for item in active_experts],
        "target_code": target.get("code") if target else None,
    }


def analyze_dragon_intelligence(
    snapshot: Any,
    *,
    previous_snapshot: Any = None,
    expert_ids: list[str] | None = None,
) -> dict:
    """对一个 prep 快照生成只读龙头理解结果。"""

    data = _dict(snapshot)
    review = _dict(data.get("review"))
    if not review:
        return {
            "schema_version": "dragon_intelligence_v1",
            "status": "unavailable",
            "reason": "review_snapshot_missing",
            "trade_date": _text(data.get("trade_date")),
            "read_only": True,
            "decision_impact": False,
            "candidates": [],
            "experts": list_experts(),
            "collaboration": {
                "status": "insufficient_evidence",
                "consensus_stance": None,
                "active_expert_ids": [],
                "target_code": None,
                "note": "缺少复盘结果，无法启动龙头理解分析。",
            },
        }

    selected_experts = resolve_experts(expert_ids)
    leaders = _dict(review.get("leaders"))
    market = _dict(review.get("market"))
    emotion = _dict(review.get("emotion_cycle"))
    mainlines = _list(review.get("mainlines"))
    phase = _text(emotion.get("phase")) or "unknown"
    coverage = _dict(leaders.get("coverage"))
    coverage_complete = coverage.get("complete") is True
    candidate_rows = _build_candidate_rows(
        review, leaders, mainlines, previous_snapshot, phase
    )

    context = {
        "market": {
            "phase": phase,
            "phase_label": _text(emotion.get("phase_label")) or "待观察",
            "state": _text(market.get("state")) or "unknown",
            "score": _number(market.get("score")),
        },
        "coverage_complete": coverage_complete,
    }
    active_meta = [{"meta": dict(item["meta"])} for item in selected_experts]
    for candidate in candidate_rows:
        for expert in selected_experts:
            opinion = expert["analyze_candidate"](context, candidate)
            candidate["expert_opinions"].append(opinion)
        candidate["collaboration"] = _collaboration_for_opinions(
            candidate["expert_opinions"], active_meta
        )

    collaboration = _collaboration_status(candidate_rows, active_meta)
    limitations = [
        "本引擎只读取已保存的 prep 快照，不调用实时行情或外部新闻。",
        "预期差暂不评分：缺少独立的一致预期基线，不能把 T+1 结果倒灌成事前预期。",
        "市场合力暂以主线涨停家数、持续天数和集中度作静态代理，尚未计算板块成分股的同步联动。",
        "龙头生命周期仅使用当前快照和最近前序快照，首阴、反包、被关次数等事件链尚未完整接入。",
        "陈小群模块目前是公开理念的确定性规则适配器，不是联网 LLM Agent，也不代表本人观点。",
    ]
    return {
        "schema_version": "dragon_intelligence_v1",
        "status": "ready" if candidate_rows else "partial",
        "reason": None if candidate_rows else "candidate_pool_empty",
        "trade_date": _text(data.get("trade_date")),
        "read_only": True,
        "decision_impact": False,
        "market": context["market"],
        "coverage": {
            "complete": coverage_complete,
            "observed_total": _number(coverage.get("observed_total")),
            "reported_total": _number(coverage.get("reported_total")),
            "status": _text(coverage.get("status")) or "unknown",
        },
        "total_leader": {
            "status": _text(_dict(leaders.get("market_total_leader")).get("status")) or "unavailable",
            "code": _text(_dict(leaders.get("market_total_leader")).get("code")),
            "reason": _text(_dict(leaders.get("market_total_leader")).get("reason")),
            "candidate_count": len(_list(_dict(leaders.get("market_total_leader")).get("candidates"))),
        },
        "candidate_pool_count": len(candidate_rows),
        "candidates": candidate_rows[:20],
        "candidates_truncated": len(candidate_rows) > 20,
        "experts": list_experts(),
        "active_expert_ids": [item["meta"]["id"] for item in selected_experts],
        "collaboration": collaboration,
        "limitations": limitations,
        "next_checks": [
            "核对主线成分股的同步涨跌、涨停扩散与龙头分歧时的承接。",
            "建立事前市场一致预期快照，再评估超预期/低于预期。",
            "连续追踪总龙头、主线龙头和潜在新龙头，补齐首阴、反包、被关及新老交接事件。",
        ],
    }
