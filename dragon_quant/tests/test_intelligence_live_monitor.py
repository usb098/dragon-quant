from __future__ import annotations

from types import SimpleNamespace

import pytest

from dragon_quant.intelligence.live_monitor import monitor_quotes


class FakeProvider:
    def __init__(self, rows):
        self.rows = rows

    def batch_get_quotes(self, codes):
        return self.rows


def quote(code="600001", timestamp=1_798_000_000_000):
    return SimpleNamespace(
        code=code, name="样本股", timestamp=timestamp,
        price=10.0, prev_close=9.5, pct=5.26, amount=1e8,
        volume_ratio=1.8, turnover_rate=6.0, limit_up=10.45,
        avg_price=9.9, bid1_volume=1200, ask1_volume=400,
    )


def test_live_monitor_prefers_timestamped_fallback_over_tdx_without_timestamp():
    now = 1_798_000_100_000
    result = monitor_quotes(
        ["600001"],
        {
            "tdx": FakeProvider([quote(timestamp=0)]),
            "tencent": FakeProvider([quote(timestamp=now - 30_000)]),
        },
        now_ms=now,
    )
    item = result["items"][0]
    assert item["source"] == "tencent"
    assert item["freshness"] == "fresh"
    assert item["observation_status"] == "live_observation"
    assert item["near_limit_up"] is False
    assert result["can_execute"] is False


def test_live_monitor_does_not_treat_unknown_timestamp_as_fresh():
    result = monitor_quotes(["600001"], {"tdx": FakeProvider([quote(timestamp=0)])}, now_ms=1_798_000_100_000)
    assert result["items"][0]["freshness"] == "timestamp_unknown"
    assert result["items"][0]["observation_status"] == "timestamp_unverified"


def test_live_monitor_marks_stale_quote_and_missing_codes():
    now = 1_798_000_100_000
    result = monitor_quotes(["600001", "000001"], {
        "tencent": FakeProvider([quote(timestamp=now - 300_000)])
    }, now_ms=now)
    assert result["items"][0]["freshness"] == "stale"
    assert result["items"][1]["observation_status"] == "no_quote"


@pytest.mark.parametrize("codes", [[], ["600001", "bad"], ["600001"] * 31])
def test_live_monitor_rejects_invalid_or_oversized_code_lists(codes):
    with pytest.raises(ValueError):
        monitor_quotes(codes, {}, now_ms=1_798_000_100_000)
