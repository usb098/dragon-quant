import { useState } from "react";
import { monitorLiveDecision, type LiveDecisionResponse } from "../../api/assets";
import { Badge } from "../../components/Badge";

export function LiveDecisionPanel({ codes }: { codes: string[] }) {
  const [result, setResult] = useState<LiveDecisionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    if (!codes.length || loading) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await monitorLiveDecision(codes.slice(0, 30)));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-3 rounded-lg border border-hairline p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-body font-semibold text-ink">盘中实时观察</div>
          <div className="text-caption text-ink-3">只在点击刷新时请求行情；不自动轮询、不产生交易信号。</div>
        </div>
        <button className="rounded-md border border-hairline px-3 py-1.5 text-body" disabled={!codes.length || loading} onClick={refresh}>
          {loading ? "刷新中…" : "刷新候选行情"}
        </button>
      </div>
      {!codes.length ? <div className="text-caption text-ink-3">当前快照没有可用候选代码。</div> : null}
      {error ? <div className="text-caption text-warning">行情读取失败：{error}</div> : null}
      {result ? (
        <>
          <div className="text-caption text-ink-3">UTC {result.generated_at} · 请求 {result.requested_codes.length} 只 · 新鲜度阈值 {result.freshness_threshold_seconds}s</div>
          <div className="grid gap-2">
            {result.items.map((item) => (
              <div key={item.code} className="grid gap-1 rounded-md bg-panel-2 p-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-body font-semibold text-ink">{item.code}</span>
                  <span className="text-body text-ink">{item.name ?? "—"}</span>
                  <Badge tone={item.freshness === "fresh" ? "positive" : item.freshness === "stale" ? "warning" : "muted"}>{item.freshness}</Badge>
                  <Badge tone={item.near_limit_up ? "warning" : "normal"}>{item.at_limit_up ? "涨停价附近/触板" : item.near_limit_up ? "接近涨停" : "未接近涨停"}</Badge>
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-caption text-ink-2">
                  <span>现价 {item.price?.toFixed(2) ?? "—"}</span>
                  <span>涨跌 {item.pct == null ? "—" : item.pct.toFixed(2) + "%"}</span>
                  <span>量比 {item.volume_ratio?.toFixed(2) ?? "—"}</span>
                  <span>换手 {item.turnover_rate?.toFixed(2) ?? "—"}%</span>
                  <span>均价上方 {item.above_vwap_proxy == null ? "未知" : item.above_vwap_proxy ? "是" : "否"}</span>
                  <span>买一量强于卖一量 {item.bid1_dominates_ask1 == null ? "未知" : item.bid1_dominates_ask1 ? "是" : "否"}</span>
                  <span>数据源 {item.source ?? "—"}</span>
                </div>
                {item.observation_status !== "live_observation" ? <div className="text-caption text-warning">{item.observation_status}：不可作为实时确认依据</div> : null}
              </div>
            ))}
          </div>
          <div className="text-caption text-ink-3">{result.note}</div>
        </>
      ) : null}
    </div>
  );
}
