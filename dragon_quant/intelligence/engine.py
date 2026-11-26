"""龙头理解引擎：结构化候选、客观证据、独立专家观点与分歧编排。

纯函数：只消费已保存的 prep 快照；不读文件/数据库/网络/时钟，不修改策略或仓位。
"""

from __future__ import annotations

import math
from typing import Any, Mapping

from .registry import list_experts, resolve_experts
from .cohesion import build_market_cohesion
from .evidence import build_leader_lifecycle, build_pre_event_expectation

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


def _build_candidate_rows(
    review: Mapping[str, Any],
    leaders: Mapping[str, Any],
    mainlines: list[dict],
    previous_snapshot: Any,
    phase: str,
    *,
    previous_snapshots: list[Any] | None = None,
    cohesion_by_board: Mapping[str, Any] | None = None,
    current_total_leader_code: str | None = None,
    trade_date: str = "",
    current_feedback: Any = None,
    frozen_prev_plan: Any = None,
    daily_bars_by_code: Mapping[str, Any] | None = None,
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
    history = list(previous_snapshots or [])
    if not history and previous_snapshot is not None:
        history = [previous_snapshot]
    previous_snapshot = history[0] if history else previous_snapshot
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

        cohesion_count = _number(board.get("limit_up_num"))
        if cohesion_count is None:
            cohesion_count = _number(raw.get("board_limit_up_num"))
        continuity = _number(board.get("continuous_plate_num"))
        concentration = _number(board.get("concentration"))
        cohesion_known = any(value is not None for value in (cohesion_count, continuity, concentration))
        static_cohesion = {
            "status": "partial_proxy" if cohesion_known else "unknown",
            "limit_up_num": cohesion_count,
            "continuous_plate_num": continuity,
            "concentration": concentration,
            "member_count": None,
            "covered_count": None,
            "coverage_ratio": None,
            "advancer_ratio": None,
            "decliner_ratio": None,
            "mean_return_pct": None,
            "median_return_pct": None,
            "pairwise_correlation": None,
            "correlation_pairs": 0,
            "synchronized_up_ratio": None,
            "synchronized_down_ratio": None,
            "history_sessions": 0,
            "data_as_of": None,
            "note": "暂无足够成分股日 K 时，仅展示板块涨停家数等静态代理。",
        }
        measured_cohesion = (cohesion_by_board or {}).get(mainline_name)
        cohesion = (
            {**static_cohesion, **dict(measured_cohesion)}
            if isinstance(measured_cohesion, Mapping) else static_cohesion
        )
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
        candidate_view = {
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
            "expert_opinions": [],
        }
        prior_context = {
            **candidate_view,
            "trade_date": trade_date,
            "height": height,
            "mainline": {
                "board_name": mainline_name,
                "rank": rank,
                "state": mainline_state,
            },
            "mainline_rank": rank,
            "mainline_state": mainline_state,
        }
        candidate_view["expectation_gap"] = build_pre_event_expectation(
            prior_context,
            history,
            feedback=current_feedback,
            prev_plan=frozen_prev_plan,
        )
        candidate_view["lifecycle"] = build_leader_lifecycle(
            prior_context,
            current_total_leader_code=current_total_leader_code if is_total else None,
            previous_snapshots=history,
            phase=phase,
            daily_bars=(daily_bars_by_code or {}).get(code),
            feedback=current_feedback,
        )
        output.append(candidate_view)

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
    previous_snapshots: list[Any] | None = None,
    market_assets: Mapping[str, Any] | None = None,
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
    history = list(previous_snapshots or [])
    if not history and previous_snapshot is not None:
        history = [previous_snapshot]
    previous_snapshot = history[0] if history else previous_snapshot
    sources = dict(market_assets or {})
    cohesion_by_board = build_market_cohesion(
        sources.get("ths_block_top"),
        sources.get("stock_daily"),
        trade_date=_text(data.get("trade_date")) or "",
    )
    current_total = _text(_dict(leaders.get("market_total_leader")).get("code"))
    candidate_rows = _build_candidate_rows(
        review, leaders, mainlines, previous_snapshot, phase,
        previous_snapshots=history,
        cohesion_by_board=cohesion_by_board,
        current_total_leader_code=current_total,
        trade_date=_text(data.get("trade_date")) or "",
        current_feedback=data.get("feedback"),
        frozen_prev_plan=sources.get("prev_plan"),
        daily_bars_by_code=(
            _dict(sources.get("stock_daily")).get("rows")
            if isinstance(_dict(sources.get("stock_daily")).get("rows"), Mapping)
            else {}
        ),
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
    measured_boards = sum(
        1 for item in cohesion_by_board.values()
        if isinstance(item, Mapping) and item.get("status") == "measured"
    )
    partial_boards = sum(
        1 for item in cohesion_by_board.values()
        if isinstance(item, Mapping) and item.get("status") == "partial_proxy"
    )
    expectation_measured = sum(
        1 for item in candidate_rows
        if item.get("expectation_gap", {}).get("status") != "unknown"
    )
    frozen_feedback_count = sum(
        1 for item in candidate_rows
        if str(item.get("expectation_gap", {}).get("basis", "")).startswith("frozen_")
    )
    prior_proxy_count = sum(
        1 for item in candidate_rows
        if item.get("expectation_gap", {}).get("basis") == "prior_snapshot_framework_proxy"
        and item.get("expectation_gap", {}).get("status") != "unknown"
    )
    limitations = [
        "本引擎只读取已保存的 prep 与日 K 资产；不主动补采行情。",
        "预期差优先使用 T-1 冻结预期与 T+1 feedback 对照；仅在反馈/冻结基线缺失时回退前序框架代理，均不等同于全市场一致预期。",
        f"市场合力已计算 {measured_boards} 个覆盖达标板块；{partial_boards} 个板块仅有部分/静态代理，其余明确保留未知。",
        "生命周期最多追溯 10 份已保存快照；快照缺失的交易日不补齐，不能把观察连续数误作完整连板周期。",
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
        "cohesion_summary": {
            "boards_total": len(cohesion_by_board),
            "boards_measured": measured_boards,
            "boards_partial": partial_boards,
        },
        "expectation_proxy_summary": {
            "candidates_with_comparable_prior_snapshot": expectation_measured,
            "candidates_with_frozen_feedback": frozen_feedback_count,
            "candidates_using_prior_snapshot_proxy": prior_proxy_count,
            "candidates_total": len(candidate_rows),
            "basis": "frozen_previous_plan_feedback_then_prior_snapshot_framework_proxy",
        },
        "lifecycle_summary": {
            "history_snapshots_available": len(history),
            "max_history_snapshots": 10,
            "scope": "saved_snapshots_only",
        },
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
