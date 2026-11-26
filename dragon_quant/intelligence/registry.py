"""独立理念专家注册表。

新增游资理念时，新增独立 adapter 并显式登记；不要把多个理念揉成一套共享规则。
Adapter 契约：analyze_candidate(context, candidate) -> JSON-compatible opinion。
"""

from __future__ import annotations

from typing import Any

from .experts import chen_xiaoqun

_EXPERTS = {
    "chen_xiaoqun": {
        "meta": chen_xiaoqun.EXPERT_META,
        "analyze_candidate": chen_xiaoqun.analyze_candidate,
    },
}


def resolve_experts(expert_ids: list[str] | None = None) -> list[dict[str, Any]]:
    selected = list(_EXPERTS) if expert_ids is None else list(dict.fromkeys(expert_ids))
    unknown = [expert_id for expert_id in selected if expert_id not in _EXPERTS]
    if unknown:
        raise ValueError(f"未知理念专家：{', '.join(unknown)}")
    return [
        {
            "meta": dict(_EXPERTS[expert_id]["meta"]),
            "analyze_candidate": _EXPERTS[expert_id]["analyze_candidate"],
        }
        for expert_id in selected
    ]


def list_experts() -> list[dict[str, Any]]:
    return [dict(spec["meta"]) for spec in _EXPERTS.values()]
