import type {
  DragonIntelligenceCandidate,
  DragonIntelligenceResponse,
} from "../../api/assets";
import { Badge, type BadgeTone } from "../../components/Badge";

function stanceLabel(value: string): string {
  return ({
    supportive: "支持",
    neutral: "中性观察",
    cautious: "谨慎",
    insufficient_evidence: "证据不足",
  } as Record<string, string>)[value] ?? value;
}

function stanceTone(value: string): BadgeTone {
  if (value === "supportive") return "positive";
  if (value === "cautious") return "warning";
  if (value === "neutral") return "normal";
  return "muted";
}

function confidenceLabel(value: string): string {
  return ({ high: "高置信", medium: "中置信", low: "低置信", unknown: "未知" } as
    Record<string, string>)[value] ?? "未知";
}

function amountLabel(value: number | null): string {
  if (value == null) return "—";
  return (value / 100000000).toFixed(1) + " 亿";
}

function collaborationLabel(value: string): string {
  return ({
    single_expert: "单专家观点",
    aligned: "观点一致",
    divergent: "观点分歧",
    insufficient_evidence: "证据不足",
    non_comparable: "适用范围不同",
  } as Record<string, string>)[value] ?? value;
}

function CandidateCard({ candidate }: { candidate: DragonIntelligenceCandidate }) {
  const opinions = candidate.expert_opinions;
  return (
    <article className="grid gap-3 rounded-lg border border-hairline p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-body font-semibold text-ink">{candidate.code}</span>
          <span className="text-body text-ink">{candidate.name ?? "—"}</span>
          <Badge tone="outline">{candidate.identity_label}</Badge>
          <Badge tone={candidate.collaboration.status === "divergent" ? "warning" : "normal"}>
            {collaborationLabel(candidate.collaboration.status)}
          </Badge>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={candidate.confidence === "high" ? "positive" : "muted"}>
            {confidenceLabel(candidate.confidence)}
          </Badge>
          <Badge tone="normal">{candidate.lifecycle.label}</Badge>
        </div>
      </div>

      <div className="grid gap-2 md:grid-cols-3">
        <div className="rounded-md bg-panel-2 px-2.5 py-2">
          <div className="text-caption text-ink-3">主线与角色</div>
          <div className="text-body text-ink">
            {candidate.structure.mainline_name ?? "未归属"} · {candidate.role ?? "待确认"}
          </div>
          <div className="text-caption text-ink-3">
            主线排名 {candidate.structure.mainline_rank ?? "—"} · {candidate.structure.mainline_state ?? "状态未知"}
          </div>
        </div>
        <div className="rounded-md bg-panel-2 px-2.5 py-2">
          <div className="text-caption text-ink-3">空间与封板</div>
          <div className="text-body text-ink">
            {candidate.structure.height == null ? "高度未知" : candidate.structure.height + " 板"}
            {" · "}{candidate.structure.first_seal_time ?? "首封未知"}
          </div>
          <div className="text-caption text-ink-3">
            开板 {candidate.structure.open_num ?? "—"} 次 · {candidate.structure.limit_up_type ?? "板型未知"}
          </div>
        </div>
        <div className="rounded-md bg-panel-2 px-2.5 py-2">
          <div className="text-caption text-ink-3">资金与合力代理</div>
          <div className="text-body text-ink">
            成交额 {amountLabel(candidate.structure.amount)}
            {" · "}换手 {candidate.structure.turnover_rate == null ? "—" : candidate.structure.turnover_rate + "%"}
          </div>
          <div className="text-caption text-ink-3">
            板块涨停 {candidate.cohesion.limit_up_num ?? "—"} 家 ·{" "}
            {candidate.cohesion.status === "partial_proxy" ? "静态代理" : "数据不足"}
          </div>
        </div>
      </div>

      {opinions.length ? (
        <div className="grid gap-2">
          {opinions.map((opinion) => (
            <div key={opinion.expert_id} className="grid gap-2 rounded-md border border-hairline px-3 py-2.5">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-body font-medium text-ink">{opinion.expert_name}</span>
                <Badge tone={stanceTone(opinion.stance)}>{stanceLabel(opinion.stance)}</Badge>
                <Badge tone="muted">{confidenceLabel(opinion.confidence)}</Badge>
              </div>
              <p className="text-body text-ink-2">{opinion.summary}</p>
              {opinion.evidence_for.length ? (
                <div className="grid gap-1">
                  <div className="text-caption font-medium text-ink-3">支持证据</div>
                  {opinion.evidence_for.map((item) => (
                    <div key={item} className="text-body text-ink-2">• {item}</div>
                  ))}
                </div>
              ) : null}
              {opinion.evidence_against.length ? (
                <div className="grid gap-1">
                  <div className="text-caption font-medium text-ink-3">反向证据</div>
                  {opinion.evidence_against.map((item) => (
                    <div key={item} className="text-body text-ink-2">• {item}</div>
                  ))}
                </div>
              ) : null}
              {opinion.unknowns.length ? (
                <div className="grid gap-1">
                  <div className="text-caption font-medium text-ink-3">尚未验证</div>
                  {opinion.unknowns.slice(0, 3).map((item) => (
                    <div key={item} className="text-body text-ink-3">• {item}</div>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-body text-ink-3">当前没有启用的专家观点。</div>
      )}
      <div className="text-caption text-ink-3">{candidate.collaboration.note}</div>
    </article>
  );
}

export function DragonIntelligencePanel({
  data,
  loading,
  error,
}: {
  data: DragonIntelligenceResponse | null;
  loading: boolean;
  error: string | null;
}) {
  if (loading && !data) {
    return <div className="rounded-lg border border-hairline p-3 text-body text-ink-3">正在生成只读龙头理解结果…</div>;
  }
  if (!data) {
    return (
      <div className="grid gap-2 rounded-lg border border-hairline p-3">
        <div className="text-body text-ink-3">{error ?? "该日暂无龙头理解结果。"}</div>
        <div className="text-caption text-ink-3">请先生成该日 prep 快照；此工作台不会自行触发采集或复盘。</div>
      </div>
    );
  }

  const total = data.total_leader;
  const phaseLabel = data.market?.phase_label ?? "待观察";
  return (
    <div className="grid gap-3">
      {error ? (
        <div className="rounded-md border border-warning-line bg-warning-soft px-3 py-2 text-body text-ink">
          {error}
        </div>
      ) : null}
      <div className="grid gap-2 md:grid-cols-3">
        <div className="rounded-md border border-hairline px-3 py-2.5">
          <div className="text-caption text-ink-3">市场情绪</div>
          <div className="text-body font-semibold text-ink">{phaseLabel}</div>
          <div className="text-caption text-ink-3">
            {data.market?.state ?? "unknown"} · 分数 {data.market?.score ?? "—"}
          </div>
        </div>
        <div className="rounded-md border border-hairline px-3 py-2.5">
          <div className="text-caption text-ink-3">总龙头交叉验证</div>
          <div className="text-body font-semibold text-ink">
            {total?.code ?? "暂不指定"}
          </div>
          <div className="text-caption text-ink-3">
            {total?.status ?? "unavailable"} · 涨停池 {data.coverage?.complete ? "完整" : "不完整/未知"}
          </div>
        </div>
        <div className="rounded-md border border-hairline px-3 py-2.5">
          <div className="text-caption text-ink-3">引擎候选</div>
          <div className="text-body font-semibold text-ink">
            {data.candidate_pool_count ?? data.candidates.length} 只
          </div>
          <div className="text-caption text-ink-3">
            {data.candidates_truncated ? "当前展示前 20 只" : "覆盖当前候选集合"}
          </div>
        </div>
      </div>

      <div className="grid gap-2 rounded-md border border-hairline px-3 py-2.5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-body font-medium text-ink">多理念协同</span>
          <Badge tone={data.collaboration.status === "divergent" ? "warning" : "normal"}>
            {collaborationLabel(data.collaboration.status)}
          </Badge>
        </div>
        <div className="text-body text-ink-2">{data.collaboration.note}</div>
        <div className="flex flex-wrap gap-2">
          {data.experts.map((expert) => (
            <Badge key={expert.id} tone={data.active_expert_ids?.includes(expert.id) ? "positive" : "muted"}>
              {expert.name} · {expert.market_scope.join("、")} · {expert.time_horizon}
            </Badge>
          ))}
        </div>
      </div>

      <div className="grid gap-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="text-body font-medium text-ink">候选龙头与专家观点</div>
          <span className="text-caption text-ink-3">候选来源：复盘候选池、空间板、主线龙头</span>
        </div>
        {data.candidates.length ? (
          <div className="grid gap-2">
            {data.candidates.map((candidate) => (
              <CandidateCard key={candidate.code} candidate={candidate} />
            ))}
          </div>
        ) : (
          <div className="rounded-md border border-hairline p-3 text-body text-ink-3">没有可用候选；不从空数据推断龙头。</div>
        )}
      </div>

      <div className="grid gap-2 rounded-md border border-hairline px-3 py-2.5">
        <div className="text-body font-medium text-ink">当前能力边界与下一步验证</div>
        {(data.limitations ?? []).slice(0, 4).map((item) => (
          <div key={item} className="text-body text-ink-3">• {item}</div>
        ))}
        {(data.next_checks ?? []).slice(0, 3).map((item) => (
          <div key={item} className="text-body text-ink-2">→ {item}</div>
        ))}
      </div>
      <div className="text-caption text-ink-3">
        研究辅助层 · 只读 · 不改变现有评分、资格、仓位或买卖规则。专家观点是理念适配器的独立输出，不构成投资建议。
      </div>
    </div>
  );
}
