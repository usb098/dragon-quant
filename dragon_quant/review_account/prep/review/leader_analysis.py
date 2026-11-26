"""全市场空间板、主线龙头交叉验证与情绪周期标签（纯函数）。

只消费 prep 已冻结的涨停池、主线与角色结果；不触网、不读时钟、不生成交易指令。
覆盖不完整、最高板并列或主线证据缺失时显式返回待确认，不强行指定总龙头。
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from dragon_quant.infra.board_height import parse_board_height

_CST = timezone(timedelta(hours=8))


def _num(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            number = float(value)
        except ValueError:
            return None
    elif isinstance(value, (int, float)):
        number = float(value)
    else:
        return None
    return number if math.isfinite(number) else None


def _height(row: Mapping[str, Any]) -> int | None:
    direct = _num(row.get("height"))
    if direct is not None and direct >= 1 and direct.is_integer() and direct <= 99:
        return int(direct)
    return parse_board_height(row)


def _seal_time(value: Any) -> str | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = _num(value)
        if number is not None and number >= 1_000_000_000:
            try:
                return datetime.fromtimestamp(number, _CST).strftime("%H:%M:%S")
            except (OverflowError, OSError, ValueError):
                return None
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw.isdigit() and len(raw) >= 10:
        try:
            return datetime.fromtimestamp(float(raw), _CST).strftime("%H:%M:%S")
        except (OverflowError, OSError, ValueError):
            return None
    parts = raw.split(":")
    if len(parts) not in (2, 3):
        return None
    try:
        hour, minute = int(parts[0]), int(parts[1])
        second = int(parts[2]) if len(parts) == 3 else 0
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        return None
    return f"{hour:02d}:{minute:02d}:{second:02d}"


def _time_key(value: Any) -> float:
    normalized = _seal_time(value)
    if normalized is None:
        return float("inf")
    hour, minute, second = (int(part) for part in normalized.split(":"))
    return hour * 3600 + minute * 60 + second


def _stock(row: Mapping[str, Any], role: Mapping[str, Any] | None = None) -> dict:
    role = role if isinstance(role, Mapping) else {}
    evidence = role.get("evidence") if isinstance(role.get("evidence"), Mapping) else {}
    limit_up_type = row.get("limit_up_type")
    amount = _num(row.get("amount"))
    if amount is None:
        amount = _num(evidence.get("amount"))
    seal = _seal_time(row.get("first_limit_up_time")) or _seal_time(
        evidence.get("first_seal_time")
    )
    return {
        "code": str(row.get("code") or ""),
        "name": row.get("name") if isinstance(row.get("name"), str) else None,
        "height": _height(row),
        "first_seal_time": seal,
        "limit_up_type": limit_up_type if isinstance(limit_up_type, str) else None,
        "reason_type": row.get("reason_type") if isinstance(row.get("reason_type"), str) else None,
        "open_num": _num(row.get("open_num")),
        "amount": amount,
        "is_one_word": isinstance(limit_up_type, str) and "一字" in limit_up_type,
        "role": role.get("role") if isinstance(role.get("role"), str) else None,
    }


def _rows(pool_payload: Any) -> tuple[list[dict], dict]:
    payload = pool_payload if isinstance(pool_payload, Mapping) else {}
    raw_rows = payload.get("rows")
    raw_rows = raw_rows if isinstance(raw_rows, list) else []
    output: list[dict] = []
    seen: set[str] = set()
    for row in raw_rows:
        if not isinstance(row, Mapping):
            continue
        code = row.get("code")
        if not isinstance(code, str) or not code or code in seen:
            continue
        seen.add(code)
        stock = _stock(row)
        if stock["height"] is not None:
            output.append(stock)
    total_raw = _num(payload.get("total"))
    total = int(total_raw) if total_raw is not None and total_raw >= 0 else None
    truncated = payload.get("truncated") is True
    complete = bool(payload) and not truncated and total is not None and len(seen) >= total
    status = "missing" if not payload else ("empty" if not output else (
        "complete" if complete else "partial"
    ))
    return output, {
        "status": status,
        "reported_total": total,
        "observed_total": len(seen),
        "rows_with_height": len(output),
        "truncated": truncated,
        "complete": complete,
    }


def _mainline_leaders(
    mainlines: Any, roles: Mapping[str, Any], row_by_code: Mapping[str, dict]
) -> list[dict]:
    board_by_name: dict[str, dict] = {}
    if isinstance(mainlines, list):
        for board in mainlines:
            if isinstance(board, Mapping):
                name = board.get("board_name")
                if isinstance(name, str) and name:
                    board_by_name[name] = dict(board)

    candidates: list[dict] = []
    for code, role in roles.items():
        if not isinstance(code, str) or not isinstance(role, Mapping):
            continue
        if role.get("role") != "leader" or code not in row_by_code:
            continue
        item = dict(row_by_code[code])
        mainline = role.get("mainline")
        mainline = mainline if isinstance(mainline, Mapping) else {}
        name = mainline.get("board_name")
        board = board_by_name.get(name, {}) if isinstance(name, str) else {}
        item.update({
            "mainline": name if isinstance(name, str) else None,
            "mainline_rank": _num(mainline.get("rank")) or _num(board.get("rank")),
            "mainline_score": (
                _num(mainline.get("mainline_score"))
                if _num(mainline.get("mainline_score")) is not None
                else _num(board.get("mainline_score"))
            ),
            "mainline_state": mainline.get("state") or board.get("state"),
            "role_confidence": role.get("role_confidence"),
            "role_basis": role.get("role_basis"),
        })
        candidates.append(item)

    candidates.sort(key=lambda item: (
        -(_num(item.get("height")) or 0),
        _num(item.get("mainline_rank")) or float("inf"),
        -(_num(item.get("mainline_score")) or 0),
        _time_key(item.get("first_seal_time")),
        1 if item.get("is_one_word") else 0,
        str(item.get("code") or ""),
    ))
    return candidates


def _public_stock(row: Mapping[str, Any]) -> dict:
    keys = (
        "code", "name", "height", "first_seal_time", "limit_up_type",
        "reason_type", "open_num", "amount", "is_one_word", "role",
        "mainline", "mainline_rank", "mainline_score", "role_confidence",
    )
    return {key: row.get(key) for key in keys if key in row}


def build_leader_analysis(
    pool_payload: Any,
    mainlines: Any,
    roles: Mapping[str, Any] | None,
) -> dict:
    """涨停池 + 主线/角色 → 空间板、梯队、主线龙头与总龙头确认状态。

    唯一最高空间板必须同时是已识别的主线 leader，且涨停池覆盖完整，
    才返回 identified；否则返回 contested/provisional/unconfirmed。
    """
    rows, coverage = _rows(pool_payload)
    roles = roles if isinstance(roles, Mapping) else {}
    row_by_code = {row["code"]: row for row in rows}
    for code, role in roles.items():
        if code in row_by_code and isinstance(role, Mapping):
            row_by_code[code]["role"] = role.get("role")

    rows.sort(key=lambda item: (
        -int(item["height"]),
        _time_key(item.get("first_seal_time")),
        -(_num(item.get("amount")) or 0),
        item["code"],
    ))
    max_height = rows[0]["height"] if rows else None
    space_rows = [row for row in rows if row["height"] == max_height] if rows else []

    by_height: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_height[int(row["height"])].append(row)
    ladder = [
        {
            "height": height,
            "count": len(items),
            "codes": [item["code"] for item in items[:8]],
            "names": [item["name"] for item in items[:8] if item["name"]],
        }
        for height, items in sorted(by_height.items(), reverse=True)
    ]

    leaders = _mainline_leaders(mainlines, roles, row_by_code)
    space_codes = {row["code"] for row in space_rows}
    matching = [item for item in leaders if item["code"] in space_codes]
    candidate = matching[0] if matching else (leaders[0] if leaders else None)
    total = {
        "status": "unavailable",
        "code": None,
        "candidate": candidate,
        "candidates": [],
        "confidence": "unknown",
        "reason": "mainline_leader_unavailable",
    }

    if coverage["status"] == "missing":
        total["reason"] = "limit_up_pool_missing"
    elif not space_rows:
        total["reason"] = "space_board_unavailable"
    elif not coverage["complete"]:
        total.update({
            "status": "provisional", "candidate": space_rows[0],
            "candidates": space_rows, "confidence": "low",
            "reason": "limit_up_pool_incomplete",
        })
    elif len(space_rows) > 1:
        total.update({
            "status": "contested", "candidate": space_rows[0],
            "candidates": space_rows, "confidence": "low",
            "reason": "multiple_stocks_share_space_board",
        })
    elif matching:
        selected = matching[0]
        confidence = "high"
        if selected.get("role_confidence") != "high" or selected.get("is_one_word"):
            confidence = "medium"
        total.update({
            "status": "identified", "code": selected["code"],
            "candidate": selected, "candidates": [selected],
            "confidence": confidence,
            "reason": "unique_space_board_is_mainline_leader",
        })
    else:
        total.update({
            "status": "unconfirmed", "candidate": space_rows[0],
            "candidates": space_rows, "confidence": "low",
            "reason": (
                "space_board_not_mainline_leader"
                if leaders else "mainline_leader_unavailable"
            ),
        })

    public_leaders = [_public_stock(item) for item in leaders]
    if isinstance(total.get("candidate"), Mapping):
        total["candidate"] = _public_stock(total["candidate"])
    total["candidates"] = [
        _public_stock(item) for item in total["candidates"]
        if isinstance(item, Mapping)
    ]
    space_stocks = []
    for item in space_rows:
        role = roles.get(item["code"])
        stock = dict(item)
        if isinstance(role, Mapping):
            stock["role"] = role.get("role")
            mainline = role.get("mainline")
            if isinstance(mainline, Mapping):
                stock["mainline"] = mainline.get("board_name")
                stock["role_confidence"] = role.get("role_confidence")
        space_stocks.append(_public_stock(stock))

    return {
        "analysis_version": "space_leader_v1",
        "coverage": coverage,
        "space_board": {"height": max_height, "count": len(space_rows), "stocks": space_stocks},
        "ladder": ladder,
        "mainline_leaders": public_leaders,
        "market_total_leader": total,
    }


def classify_emotion_cycle(market: Any) -> dict:
    """市场四态 + T-1 变化 → 可审计的阶段标签，不推导买卖指令。"""
    payload = market if isinstance(market, Mapping) else {}
    state = payload.get("state") if isinstance(payload.get("state"), str) else "unknown"
    previous = payload.get("prev_state") if isinstance(payload.get("prev_state"), str) else None
    change = _num(payload.get("score_change"))
    phase, reason, confidence = "unknown", "market_or_history_insufficient", "low"

    if state == "ice":
        phase, reason, confidence = "ice", "market_state_ice", "medium"
    elif state == "weak":
        phase, reason = "recession", "market_state_weak"
        confidence = "medium" if previous else "low"
    elif state == "neutral":
        if previous in ("ice", "weak") and change is not None and change > 0:
            phase, reason, confidence = "startup", "weak_to_neutral_with_rising_score", "medium"
        elif previous == "neutral" and change is not None and change > 0:
            phase, reason, confidence = "fermentation", "neutral_state_score_rising", "medium"
        elif previous == "strong" and change is not None and change < 0:
            phase, reason, confidence = "recession", "strong_to_neutral_with_falling_score", "medium"
    elif state == "strong":
        if previous in ("ice", "weak") and change is not None and change > 0:
            phase, reason, confidence = "startup", "weak_to_strong_with_rising_score", "medium"
        elif previous == "neutral" and change is not None and change > 0:
            phase, reason, confidence = "fermentation", "neutral_to_strong_with_rising_score", "medium"
        elif previous == "strong":
            if change is not None and change < 0:
                phase, reason, confidence = "recession", "strong_state_score_falling", "low"
            else:
                phase, reason = "climax", "strong_state_persisted"
                confidence = "medium"

    labels = {
        "startup": "启动", "fermentation": "发酵", "climax": "高潮",
        "recession": "退潮", "ice": "冰点", "unknown": "待观察",
    }
    return {
        "method_version": "emotion_cycle_v1",
        "phase": phase,
        "phase_label": labels[phase],
        "confidence": confidence,
        "reason": reason,
        "market_state": state,
        "prev_state": previous,
        "score_change": change,
        "informational_only": True,
    }


__all__ = ["build_leader_analysis", "classify_emotion_cycle"]
