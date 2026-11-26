"""Chen Xiaoqun research decision framework.

This module returns research candidates, mode fit and missing confirmations only.
It never emits prices, position sizes or order instructions.
"""

from __future__ import annotations

from typing import Any, Mapping


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str:
    return value.strip().lower() if isinstance(value, str) and value.strip() else "unknown"


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _contains(events: set[str], *tokens: str) -> bool:
    return any(token in events for token in tokens)


def _assessment(mode: str, label: str, status: str, evidence: list[str],
                blockers: list[str], confirmations: list[str]) -> dict[str, Any]:
    return {
        "mode": mode,
        "label": label,
        "status": status,
        "evidence": list(dict.fromkeys(evidence)),
        "blockers": list(dict.fromkeys(blockers)),
        "required_confirmations": list(dict.fromkeys(confirmations)),
    }


def build_decision_framework(context: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Generate a conditional, read-only mode assessment from a saved prep snapshot."""

    market = _mapping(context.get("market"))
    structure = _mapping(candidate.get("structure"))
    cohesion = _mapping(candidate.get("cohesion"))
    expectation = _mapping(candidate.get("expectation_gap"))
    lifecycle = _mapping(candidate.get("lifecycle"))

    phase = _text(market.get("phase"))
    market_state = _text(market.get("state"))
    role = _text(candidate.get("role"))
    mainline_state = _text(structure.get("mainline_state"))
    expectation_status = _text(expectation.get("status"))
    cohesion_status = _text(cohesion.get("status"))
    advancer_ratio = _number(cohesion.get("advancer_ratio"))
    correlation = _number(cohesion.get("pairwise_correlation"))
    events = {
        str(item).strip().lower()
        for item in lifecycle.get("events", [])
        if isinstance(item, str)
    } if isinstance(lifecycle.get("events"), list) else set()

    risk_off = phase in {"ice", "recession", "退潮", "冰点"} or market_state == "ice"
    overheated = phase in {"climax", "高潮"} or market_state == "weak"
    supportive_phase = phase in {
        "startup", "fermentation", "continuation", "启动", "发酵", "延续", "主升",
    }
    phase_known = phase != "unknown"
    core_role = role in {"leader", "vanguard"} or candidate.get("is_total_leader") is True
    follower = role == "follower"
    mainline_ok = mainline_state == "strengthening"
    coverage_complete = context.get("coverage_complete") is True
    measured_cohesion = cohesion_status == "measured"
    cohesion_positive = (
        measured_cohesion
        and advancer_ratio is not None
        and advancer_ratio > 0.5
        and (correlation is None or correlation >= 0)
    )
    expectation_positive = expectation_status in {
        "above_prior_expectation", "met_prior_expectation",
    }
    first_negative = _contains(
        events, "first_negative_in_observed_window", "negative_day_observed",
    )
    repair_seen = _contains(
        events, "rebound_after_negative", "bullish_engulfing_after_negative",
    )

    hard_risks: list[str] = []
    cautions: list[str] = []
    if risk_off:
        hard_risks.append("市场处于冰点/退潮状态，停止寻找进攻型新开仓模式")
    if mainline_state == "weakening":
        hard_risks.append("所属主线正在走弱")
    if follower:
        hard_risks.append("当前角色更接近跟风，优先级低于主线核心")
    if not phase_known:
        cautions.append("市场情绪阶段未知")
    if overheated:
        cautions.append("市场高潮/弱势环境需防止一致性拥挤或亏钱效应扩散")
    if not coverage_complete:
        cautions.append("全市场覆盖不完整，不能确认总龙头或市场空间板唯一性")
    if not measured_cohesion:
        cautions.append("板块成分股联动未达到实测标准，合力证据不足")
    if not expectation_positive:
        cautions.append("没有高于/符合冻结事前预期的证据，不能声称出现正向预期差")

    mode_rows: list[dict[str, Any]] = []

    # Breakout / board-follow: only qualify for next-session intraday observation.
    board_evidence: list[str] = []
    board_blockers: list[str] = list(hard_risks)
    board_missing: list[str] = []
    if core_role:
        board_evidence.append("股票角色属于主线龙头/先锋或已确认总龙头候选")
    else:
        board_blockers.append("尚未确认主线核心角色")
    if mainline_ok:
        board_evidence.append("主线状态为 strengthening")
    else:
        board_blockers.append("主线未显示强化")
    if not coverage_complete:
        board_missing.append("完整涨停池与最高空间板交叉确认")
    if measured_cohesion:
        if cohesion_positive:
            board_evidence.append("成分股联动实测显示多数上涨且相关性未呈负向")
        else:
            board_blockers.append("成分股联动实测未显示正向扩散")
    else:
        board_missing.append("足够覆盖的成分股同步表现")
    if expectation_positive:
        board_evidence.append("事前冻结预期的反馈为符合或超出预期")
    else:
        board_missing.append("可比较的冻结预期与 T+1 反馈")
    board_missing.extend([
        "T+1 竞价缺口与竞价额比",
        "开盘后板块扩散、核心股承接和封单变化",
        "炸板后的回封质量、滑点和实际可成交性",
    ])
    board_status = (
        "blocked" if board_blockers else
        "conditional_setup" if supportive_phase and not overheated else
        "insufficient_evidence"
    )
    if overheated and not board_blockers:
        board_missing.append("高潮分歧是否收敛及风险收益比")
    if not supportive_phase and not board_blockers:
        board_missing.append("市场阶段进入可验证的发酵/延续窗口")
    mode_rows.append(_assessment(
        "breakout_follow", "打板/接力", board_status, board_evidence,
        board_blockers, board_missing,
    ))

    # Pullback / absorption: require a visible first-negative or defined pullback event.
    pullback_evidence: list[str] = []
    pullback_blockers = list(hard_risks)
    pullback_missing: list[str] = []
    if core_role:
        pullback_evidence.append("候选属于主线核心角色")
    else:
        pullback_blockers.append("候选不是已确认的主线核心")
    if mainline_ok:
        pullback_evidence.append("主线尚显示强化")
    else:
        pullback_blockers.append("主线强化条件不成立")
    if first_negative:
        pullback_evidence.append("生命周期观察记录到近端收阴/负向日")
    else:
        pullback_missing.append("首阴或有定义的回撤/分歧事件")
    pullback_missing.extend([
        "抛压衰减、价格企稳和关键位置承接",
        "分时量价转强及板块同步修复",
        "明确的判断失效条件与可执行退出条件",
    ])
    pullback_status = (
        "blocked" if pullback_blockers else
        "conditional_setup" if first_negative and supportive_phase else
        "insufficient_evidence"
    )
    mode_rows.append(_assessment(
        "pullback_absorption", "低吸/分歧承接", pullback_status,
        pullback_evidence, pullback_blockers, pullback_missing,
    ))

    # Weak-to-strong: require core role and an above-plan T+1 reaction.
    w2s_evidence: list[str] = []
    w2s_blockers = list(hard_risks)
    w2s_missing: list[str] = []
    if core_role:
        w2s_evidence.append("候选角色属于主线核心")
    else:
        w2s_blockers.append("缺少主线核心角色")
    if expectation_status == "above_prior_expectation":
        w2s_evidence.append("实际反馈高于冻结事前预期")
    else:
        w2s_missing.append("高于冻结预期的 T+1 竞价/反馈证据")
    w2s_missing.extend([
        "开盘后强度保持、主动承接和板块扩散",
        "突破关键位置后的成交确认",
    ])
    w2s_status = (
        "blocked" if w2s_blockers else
        "conditional_setup" if core_role and expectation_status == "above_prior_expectation" and supportive_phase else
        "insufficient_evidence"
    )
    mode_rows.append(_assessment(
        "weak_to_strong", "弱转强", w2s_status, w2s_evidence,
        w2s_blockers, w2s_missing,
    ))

    # Trend following requires role/structure plus missing multi-period trend proof.
    trend_evidence: list[str] = []
    trend_blockers = list(hard_risks)
    trend_missing: list[str] = []
    trend_role = role in {"mainstay", "capacity"} or _text(structure.get("limit_up_type")) == "trend"
    if trend_role:
        trend_evidence.append("角色/板型具有中军、容量或趋势观察特征")
    else:
        trend_missing.append("趋势/容量型标的角色证据")
    if mainline_ok:
        trend_evidence.append("所属主线处于强化状态")
    else:
        trend_missing.append("主线趋势与行业相对强度")
    trend_missing.extend([
        "多周期均线/趋势斜率与成交量趋势",
        "波动率、回撤空间和趋势失效条件",
    ])
    trend_status = (
        "blocked" if trend_blockers else
        "conditional_setup" if trend_role and mainline_ok and not risk_off else
        "insufficient_evidence"
    )
    mode_rows.append(_assessment(
        "trend_follow", "趋势跟随", trend_status, trend_evidence,
        trend_blockers, trend_missing,
    ))

    # Anti-nuclear / repair is distinct from an ordinary first-negative dip.
    repair_evidence: list[str] = []
    repair_blockers = list(hard_risks)
    repair_missing: list[str] = []
    if core_role:
        repair_evidence.append("候选属于主线核心角色")
    else:
        repair_blockers.append("候选不是主线核心")
    if repair_seen:
        repair_evidence.append("生命周期记录到收阴后的反弹/阳线反包线索")
    else:
        repair_missing.append("收阴后有定义的修复事件")
    if mainline_ok:
        repair_evidence.append("主线状态未显示走弱")
    else:
        repair_blockers.append("主线强化证据不足")
    repair_missing.extend([
        "修复时板块广度、成交量与回封承接同步改善",
        "事件驱动是否仍有效及次日跟随验证",
    ])
    repair_status = (
        "blocked" if repair_blockers else
        "conditional_setup" if repair_seen and supportive_phase else
        "insufficient_evidence"
    )
    mode_rows.append(_assessment(
        "repair_rebound", "反核/修复", repair_status, repair_evidence,
        repair_blockers, repair_missing,
    ))

    conditional_modes = [row["mode"] for row in mode_rows if row["status"] == "conditional_setup"]
    if hard_risks:
        preferred_mode = "none"
        decision_status = "stand_aside"
        decision_label = "暂不参与"
    elif not phase_known or (not core_role and role not in {"mainstay", "capacity"}):
        preferred_mode = "none"
        decision_status = "insufficient_data"
        decision_label = "等待证据"
    else:
        preference_order = (
            ["repair_rebound", "pullback_absorption", "weak_to_strong", "breakout_follow", "trend_follow"]
            if repair_seen or first_negative else
            ["weak_to_strong", "breakout_follow", "trend_follow", "pullback_absorption", "repair_rebound"]
        )
        preferred_mode = next(
            (mode for mode in preference_order if mode in conditional_modes),
            "none",
        )
        if preferred_mode != "none":
            decision_status = "conditional_watch"
            decision_label = "进入条件观察，不是买点"
        else:
            decision_status = "wait_for_confirmation"
            decision_label = "等待触发/补充数据"

    preferred_label = "不指定模式" if preferred_mode == "none" else next(
        row["label"] for row in mode_rows if row["mode"] == preferred_mode
    )
    selection_tier = (
        "A_core_watch" if candidate.get("is_total_leader") is True and coverage_complete and mainline_ok else
        "B_mainline_core_watch" if core_role and mainline_ok else
        "C_secondary_watch" if role in {"mainstay", "capacity"} and mainline_ok else
        "D_low_priority"
    )

    return {
        "framework_version": "chen_xiaoqun_decision_v0.2",
        "status": decision_status,
        "status_label": decision_label,
        "selection_tier": selection_tier,
        "preferred_mode": preferred_mode,
        "preferred_mode_label": preferred_label,
        "mode_assessments": mode_rows,
        "gates": {
            "market_phase": phase,
            "market_state": market_state,
            "market_gate": "blocked" if risk_off else "caution" if overheated or not phase_known else "supportive" if supportive_phase else "unknown",
            "mainline_gate": "supportive" if mainline_ok else "blocked" if mainline_state == "weakening" else "unknown",
            "role_gate": "core" if core_role else "follower" if follower else "secondary_or_unknown",
            "market_coverage_complete": coverage_complete,
            "cohesion_measured": measured_cohesion,
            "cohesion_positive_proxy": cohesion_positive if measured_cohesion else None,
            "expectation_status": expectation_status,
        },
        "hard_risks": list(dict.fromkeys(hard_risks)),
        "cautions": list(dict.fromkeys(cautions)),
        "principle_refs": [
            "CX-P01", "CX-P02", "CX-P03", "CX-P04", "CX-P06",
            "CX-P07", "CX-P08", "CX-P09", "CX-P10", "CX-P12", "CX-P14",
        ],
        "required_live_data": [
            "次日竞价缺口、竞价额比和竞价结构",
            "盘中分时量价、封单变化、炸板/回封与主动承接",
            "板块成分股同步扩散和负反馈",
            "成交可得性、滑点、交易限制与风险收益空间",
        ],
        "can_execute": False,
        "read_only": True,
        "decision_impact": False,
        "note": (
            "这是基于已保存 prep 快照的条件式研究选择，不是交易指令。"
            "即使存在 conditional_setup，也必须等待实时竞价、盘口、量价和可成交性确认；"
            "当前模块不输出买入价、卖出价、仓位或胜率承诺。"
        ),
    }


__all__ = ["build_decision_framework"]
