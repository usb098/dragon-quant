"""Read-only intraday quote observations for prep candidates.

The monitor deliberately reports data quality and observable conditions only.
It never creates an entry signal, price target, position size or order.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

MAX_CODES = 30
FRESH_SECONDS = 120


def _quote_map(rows: list[Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for row in rows or []:
        code = str(getattr(row, "code", "") or "")
        if code:
            result[code] = row
    return result


def _quote_payload(quote: Any, source: str, now_ms: int) -> dict[str, Any]:
    stamp = int(getattr(quote, "timestamp", 0) or 0)
    age_seconds = max(0.0, (now_ms - stamp) / 1000) if stamp > 0 else None
    price = float(getattr(quote, "price", 0) or 0)
    prev = float(getattr(quote, "prev_close", 0) or 0)
    limit_up = float(getattr(quote, "limit_up", 0) or 0)
    avg = float(getattr(quote, "avg_price", 0) or 0)
    bid = float(getattr(quote, "bid1_volume", 0) or 0)
    ask = float(getattr(quote, "ask1_volume", 0) or 0)
    valid = price > 0 and prev > 0
    freshness = (
        "timestamp_unknown" if age_seconds is None
        else "stale" if age_seconds > FRESH_SECONDS
        else "fresh"
    )
    near_limit = bool(valid and limit_up > 0 and price >= limit_up * 0.99)
    at_limit = bool(valid and limit_up > 0 and price >= limit_up - max(0.01, limit_up * 0.0005))
    return {
        "code": str(getattr(quote, "code", "")),
        "name": str(getattr(quote, "name", "")),
        "source": source,
        "quote_timestamp_ms": stamp or None,
        "quote_age_seconds": round(age_seconds, 1) if age_seconds is not None else None,
        "freshness": freshness,
        "price": price if valid else None,
        "prev_close": prev if valid else None,
        "pct": float(getattr(quote, "pct", 0) or 0) if valid else None,
        "amount": float(getattr(quote, "amount", 0) or 0) if valid else None,
        "volume_ratio": float(getattr(quote, "volume_ratio", 0) or 0) if valid else None,
        "turnover_rate": float(getattr(quote, "turnover_rate", 0) or 0) if valid else None,
        "limit_up": limit_up or None,
        "avg_price": avg or None,
        "bid1_volume": bid or None,
        "ask1_volume": ask or None,
        "above_vwap_proxy": (price > avg) if valid and avg > 0 else None,
        "near_limit_up": near_limit,
        "at_limit_up": at_limit,
        "bid1_dominates_ask1": (bid > ask) if bid > 0 or ask > 0 else None,
        "observation_status": (
            "insufficient_quote" if not valid
            else "stale_quote" if freshness == "stale"
            else "timestamp_unverified" if freshness == "timestamp_unknown"
            else "live_observation"
        ),
        "mode_notes": [
            "接近涨停仅是价格位置观察，不代表封单质量或可成交性",
            "均价线仅作分时强弱代理，不能单独构成低吸条件",
            "买一/卖一量字段口径依赖数据源，不代表完整盘口深度",
        ],
    }


def monitor_quotes(codes: list[str], providers: Mapping[str, Any], now_ms: int | None = None) -> dict[str, Any]:
    """Fetch explicit user-requested candidates and return quality-labelled observations."""
    if len(codes) > MAX_CODES:
        raise ValueError(f"codes must contain at most {MAX_CODES} entries")
    normalized = list(dict.fromkeys(str(code).strip() for code in codes if str(code).strip()))
    if not normalized:
        raise ValueError(f"codes must contain 1..{MAX_CODES} unique stock codes")
    if any(not code.isdigit() or len(code) != 6 for code in normalized):
        raise ValueError("each code must be a six-digit A-share stock code")

    now_ms = now_ms or int(datetime.now(timezone.utc).timestamp() * 1000)
    results: dict[str, tuple[Any, str]] = {}
    errors: dict[str, str] = {}
    for source in ("tdx", "tencent"):
        provider = providers.get(source)
        if provider is None:
            continue
        try:
            rows = provider.batch_get_quotes(normalized)
            for code, quote in _quote_map(rows).items():
                if code not in results:
                    results[code] = (quote, source)
                else:
                    existing, _ = results[code]
                    if not getattr(existing, "timestamp", 0) and getattr(quote, "timestamp", 0):
                        results[code] = (quote, source)
        except Exception as exc:  # provider failures are visible, never silently treated as zero
            errors[source] = str(exc)[:240]

    items = []
    for code in normalized:
        found = results.get(code)
        if found is None:
            items.append({
                "code": code, "name": None, "source": None,
                "freshness": "missing", "observation_status": "no_quote",
                "price": None, "pct": None, "near_limit_up": None,
                "at_limit_up": None, "above_vwap_proxy": None,
                "bid1_dominates_ask1": None,
                "mode_notes": ["所有行情源均未返回该股票有效快照"],
            })
            continue
        quote, source = found
        items.append(_quote_payload(quote, source, now_ms))

    return {
        "generated_at": datetime.fromtimestamp(now_ms / 1000, timezone.utc).isoformat(),
        "requested_codes": normalized,
        "items": items,
        "provider_errors": errors,
        "freshness_threshold_seconds": FRESH_SECONDS,
        "can_execute": False,
        "read_only": True,
        "decision_impact": False,
        "note": "盘中行情观察层：不是买卖信号。缺少完整逐笔、盘口深度、竞价历史、板块同步和成交可得性时，不升级为可执行判断。",
    }
