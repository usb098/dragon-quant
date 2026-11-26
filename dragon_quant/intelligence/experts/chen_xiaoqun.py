"""陈小群公开理念的规则化适配器。

这是对公开交易理念的结构化抽象，不是人物本人，也不做角色扮演。
仅消费已经采集的 prep 快照，不联网、不补造数据、不产生买卖指令。
"""

from __future__ import annotations

from typing import Any, Mapping

EXPERT_META = {
    "id": "chen_xiaoqun",
    "name": "陈小群理念专家",
    "version": "0.1.0",
    "kind": "deterministic_framework",
    "framework": "public_framework_distillation_v1",
    "market_scope": ["A股"],
    "time_horizon": "short_term",
    "style": "emotion_mainline_leader",
    "collaboration_roles": ["core_leader_judgement", "emotion_cycle", "discipline"],
    "principles": [
        "情绪周期",
        "只做主线龙头",
        "龙头走出来后再确认",
        "市场合力",
        "预期差",
        "空仓与纪律",
    ],
}


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def analyze_candidate(context: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict:
    """按陈小群理念输出独立观点；缺失证据必须保留为未知。"""

    market = context.get("market")
    market = market if isinstance(market, Mapping) else {}
    phase = _text(market.get("phase")) or "unknown"
    role = _text(candidate.get("role")) or "unknown"
    is_total_leader = candidate.get("is_total_leader") is True
    coverage_complete = context.get("coverage_complete") is True
    structure = candidate.get("structure") if isinstance(candidate.get("structure"), Mapping) else {}
    cohesion = candidate.get("cohesion") if isinstance(candidate.get("cohesion"), Mapping) else {}
    expectation = candidate.get("expectation_gap") if isinstance(candidate.get("expectation_gap"), Mapping) else {}

    supporting: list[str] = []
    against: list[str] = []
    unknowns: list[str] = []
    risk_flags: list[str] = []

    if is_total_leader and coverage_complete:
        supporting.append("全市场空间板、唯一性与主线龙头身份已交叉确认")
    elif candidate.get("is_space_board") is True:
        supporting.append("处于已观测全市场最高空间板，但总龙头条件尚未全部满足")
    if role == "leader":
        supporting.append("在已识别主线内被分配为龙头角色")
    if structure.get("mainline_state") == "strengthening":
        supporting.append("所属主线较上一快照强化")
    if structure.get("mainline_state") == "weakening":
        against.append("所属主线较上一快照走弱")
        risk_flags.append("mainline_weakening")

    if not coverage_complete:
        unknowns.append("全市场涨停池覆盖不完整，无法确认全市场最高板")
    expectation_status = _text(expectation.get("status")) or "unknown"
    if expectation_status == "above_prior_expectation":
        supporting.append("相对上一份复盘快照的角色/主线框架代理出现正向变化")
    elif expectation_status == "below_prior_expectation":
        against.append("相对上一份复盘快照的角色/主线框架代理出现负向变化")
        risk_flags.append("below_prior_snapshot_proxy")
    elif expectation_status == "mixed":
        unknowns.append("前序框架对比同时出现正反证据，不能压成单一预期差方向")
    else:
        unknowns.append("尚无可比较的前序框架代理；不能把它表述为真实市场一致预期")

    if cohesion.get("status") == "measured":
        supporting.append(
            "成分股联动指标达到覆盖门槛："
            f"上涨占比 {cohesion.get('advancer_ratio')}, "
            f"收益相关性 {cohesion.get('pairwise_correlation')}"
        )
    else:
        unknowns.append("成分股合力覆盖/共同历史不足；静态涨停数不能替代实测联动")
    unknowns.append("未接入外部题材/公告研究 Agent，本次不评价题材催化真实性")

    if phase in ("ice", "recession"):
        stance = "cautious"
        confidence = "medium" if phase == "recession" else "low"
        posture = "risk_off_observation"
        summary = "市场处于冰点或退潮环境，优先观察亏钱效应与修复证据，不因单只高标强势推断行情安全。"
        risk_flags.append("market_cycle_risk")
    elif phase == "climax":
        stance = "cautious"
        confidence = "medium"
        posture = "consensus_risk_watch"
        summary = "市场处于高潮阶段，重点观察一致性拥挤、高位分歧和龙头承接，不把高热度等同于低风险。"
        risk_flags.append("high_consensus_risk")
    elif is_total_leader and coverage_complete:
        stance = "supportive"
        confidence = "high" if candidate.get("confidence") == "high" else "medium"
        posture = "core_leader_watch"
        summary = "结构证据支持其作为当前总龙头观察对象；仍需用板块联动、预期差和次日反馈验证合力。"
    elif role == "leader":
        stance = "neutral"
        confidence = "medium" if candidate.get("confidence") == "high" else "low"
        posture = "mainline_leader_watch"
        summary = "具备主线内部核心角色，但尚不能据此认定为全市场总龙头。"
    elif role == "vanguard":
        stance = "neutral"
        confidence = "low"
        posture = "emerging_watch"
        summary = "具备先锋特征，仍需确认其能否持续带动板块并获得市场合力。"
    elif role in ("mainstay", "capacity"):
        stance = "neutral"
        confidence = "low"
        posture = "capacity_observation"
        summary = "具备中军或容量观察价值，但不等同于短线情绪总龙头。"
    elif role == "follower":
        stance = "cautious"
        confidence = "medium"
        posture = "avoid_non_core"
        summary = "当前证据更接近跟风角色，不符合只聚焦主线核心的理念。"
        risk_flags.append("non_core_role")
    else:
        stance = "insufficient_evidence"
        confidence = "low"
        posture = "wait_for_evidence"
        summary = "龙头身份尚未确认，先补足主线归属和市场地位证据。"

    if phase == "unknown":
        unknowns.append("市场情绪周期缺少有效状态或前序快照")
        confidence = "low"
        if stance == "supportive":
            stance = "neutral"
            posture = "observe_only"
            summary = "结构上存在总龙头候选，但情绪周期未知，当前只作观察，不形成方向性判断。"

    return {
        "expert_id": EXPERT_META["id"],
        "expert_name": EXPERT_META["name"],
        "expert_version": EXPERT_META["version"],
        "stance": stance,
        "confidence": confidence,
        "posture": posture,
        "summary": summary,
        "evidence_for": supporting,
        "evidence_against": against,
        "unknowns": list(dict.fromkeys(unknowns)),
        "risk_flags": list(dict.fromkeys(risk_flags)),
    }
