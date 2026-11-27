import type {
  DragonAgentResearch,
  DragonAgentStatus,
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

function ratioLabel(value: number | null): string {
  return value == null ? "—" : (value * 100).toFixed(1) + "%";
}

function expectationLabel(value: string, basis: string): string {
  if (basis === "frozen_previous_plan_feedback" || basis === "frozen_config_expectation") {
    return ({
      above_prior_expectation: "超出冻结预期",
      below_prior_expectation: "低于冻结预期",
      met_prior_expectation: "符合冻结预期",
      mixed: "正反证据并存",
      unknown: "未知",
    } as Record<string, string>)[value] ?? "未知";
  }
  return ({
    above_prior_expectation: "高于前序框架",
    below_prior_expectation: "低于前序框架",
    met_prior_expectation: "符合前序框架",
    mixed: "正反证据并存",
    unknown: "未知",
  } as Record<string, string>)[value] ?? "未知";
}

function expectationTone(value: string): BadgeTone {
  if (value === "above_prior_expectation") return "positive";
  if (value === "below_prior_expectation") return "warning";
  return "muted";
}

function lifecycleEventLabel(value: string): string {
  return ({
    leader_handoff: "新老龙交接",
    first_total_leader_observation: "首次确认总龙头",
    height_new_high: "近期高度新高",
    height_retraced: "高度回落",
    total_leader_lost: "失去总龙头身份",
    role_changed: "角色变化",
    first_negative_in_observed_window: "近端首次收阴",
    negative_day_observed: "出现收阴",
    rebound_after_negative: "收阴后转强",
    bullish_engulfing_after_negative: "收阴后阳线反包",
    intraday_board_break_observed: "盘中出现开板",
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

      <div className="grid gap-2 md:grid-cols-4">
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

      <div className="grid gap-2 md:grid-cols-2">
        <div className="grid gap-1 rounded-md border border-hairline px-3 py-2.5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-caption text-ink-3">事前预期与 T+1 反馈</span>
            <Badge tone={expectationTone(candidate.expectation_gap.status)}>
              {expectationLabel(candidate.expectation_gap.status, candidate.expectation_gap.basis)}
            </Badge>
          </div>
          <div className="text-caption text-ink-3">
            {candidate.expectation_gap.basis === "frozen_previous_plan_feedback"
              ? "来源：T-1 冻结计划 + T+1 实际反馈"
              : candidate.expectation_gap.basis === "frozen_config_expectation"
                ? "来源：T-1 冻结的系统配置预期"
                : "来源：前序快照框架代理"}
            {" · "}前序日 {candidate.expectation_gap.previous_trade_date ?? "—"}
          </div>
          {candidate.expectation_gap.actual_gap_pct != null ? (
            <div className="text-body text-ink-2">
              实际竞价缺口 {candidate.expectation_gap.actual_gap_pct.toFixed(2)}%
              {" · "}冻结区间{" "}
              {candidate.expectation_gap.expected_gap_low?.toFixed(2) ?? "—"}%–
              {candidate.expectation_gap.expected_gap_high?.toFixed(2) ?? "—"}%
            </div>
          ) : null}
          {candidate.expectation_gap.actual_auction_ratio != null ? (
            <div className="text-body text-ink-2">
              竞价额比 {candidate.expectation_gap.actual_auction_ratio.toFixed(2)}
              {" · "}冻结下限 {candidate.expectation_gap.expected_ratio_low?.toFixed(2) ?? "—"}
            </div>
          ) : null}
          {candidate.expectation_gap.positive_evidence.map((item) => (
            <div key={item} className="text-body text-ink-2">↑ {item}</div>
          ))}
          {candidate.expectation_gap.negative_evidence.map((item) => (
            <div key={item} className="text-body text-ink-3">↓ {item}</div>
          ))}
          <div className="text-caption text-ink-3">{candidate.expectation_gap.note}</div>
        </div>
        <div className="grid gap-1 rounded-md border border-hairline px-3 py-2.5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-caption text-ink-3">龙头生命周期</span>
            <Badge tone="normal">{candidate.lifecycle.label}</Badge>
          </div>
          <div className="text-body text-ink-2">
            总龙头观察连续 {candidate.lifecycle.total_leader_observed_streak} 份快照
            · 历史观察 {candidate.lifecycle.observation_count} 份
          </div>
          <div className="text-caption text-ink-3">
            观察高度峰值 {candidate.lifecycle.observed_height_peak ?? "—"} 板
            {" · "}较前一观察{" "}
            {candidate.lifecycle.height_delta_vs_previous == null
              ? "—"
              : candidate.lifecycle.height_delta_vs_previous + " 板"}
          </div>
          {candidate.lifecycle.events.map((event) => (
            <Badge key={event} tone="warning">{lifecycleEventLabel(event)}</Badge>
          ))}
          {candidate.lifecycle.candle_context ? (
            <div className="text-caption text-ink-3">
              日 K 事件覆盖：{candidate.lifecycle.candle_context.status === "measured" ? "已有最近两根日 K" : "历史不足"}
              {" · "}盘中开板记录 {candidate.lifecycle.candle_context.board_break_count ?? "未评估"} 次
            </div>
          ) : null}
          <div className="text-caption text-ink-3">{candidate.lifecycle.scope}</div>
        </div>
      </div>
      <div className="grid gap-1 rounded-md border border-hairline px-3 py-2.5">
        <div className="text-caption text-ink-3">成分股同步合力</div>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-body text-ink-2">
          <span>
            覆盖 {candidate.cohesion.covered_count ?? "—"}/
            {candidate.cohesion.member_count ?? "—"} ({ratioLabel(candidate.cohesion.coverage_ratio)})
          </span>
          <span>上涨 {ratioLabel(candidate.cohesion.advancer_ratio)}</span>
          <span>下跌 {ratioLabel(candidate.cohesion.decliner_ratio)}</span>
          <span>平均相关性 {candidate.cohesion.pairwise_correlation?.toFixed(2) ?? "—"}</span>
          <span>同步上涨日 {ratioLabel(candidate.cohesion.synchronized_up_ratio)}</span>
          <span>共同历史 {candidate.cohesion.history_sessions} 日</span>
        </div>
        <div className="text-caption text-ink-3">{candidate.cohesion.note}</div>
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
              {opinion.decision_framework ? (
                <div className="grid gap-2 rounded-md border border-hairline bg-panel-2 px-3 py-2.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-caption font-medium text-ink-3">条件式决策框架</span>
                    <Badge tone={opinion.decision_framework.status === "stand_aside" ? "warning" : "normal"}>
                      {opinion.decision_framework.status_label}
                    </Badge>
                    <Badge tone="outline">{opinion.decision_framework.preferred_mode_label}</Badge>
                    <Badge tone="muted">{opinion.decision_framework.selection_tier}</Badge>
                  </div>
                  <div className="grid gap-1">
                    {opinion.decision_framework.mode_assessments.map((item) => (
                      <div key={item.mode} className="grid gap-1 border-t border-hairline pt-1.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-body font-medium text-ink-2">{item.label}</span>
                          <Badge tone={item.status === "blocked" ? "warning" : item.status === "conditional_setup" ? "normal" : "muted"}>
                            {item.status === "blocked" ? "阻断" : item.status === "conditional_setup" ? "条件观察" : "证据不足"}
                          </Badge>
                        </div>
                        {item.blockers.map((reason) => (
                          <div key={reason} className="text-caption text-warning">{`× ${reason}`}</div>
                        ))}
                        {item.evidence.slice(0, 2).map((reason) => (
                          <div key={reason} className="text-caption text-ink-2">{`✓ ${reason}`}</div>
                        ))}
                        {item.required_confirmations.slice(0, 3).map((reason) => (
                          <div key={reason} className="text-caption text-ink-3">{`待确认：${reason}`}</div>
                        ))}
                      </div>
                    ))}
                  </div>
                  {opinion.decision_framework.hard_risks.map((reason) => (
                    <div key={reason} className="text-caption text-warning">风险门控：{reason}</div>
                  ))}
                  <div className="text-caption text-ink-3">{opinion.decision_framework.note}</div>
                </div>
              ) : null}
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
              {opinion.risk_flags.length ? (
                <div className="grid gap-1">
                  <div className="text-caption font-medium text-ink-3">风险标签</div>
                  <div className="flex flex-wrap gap-1.5">
                    {opinion.risk_flags.map((flag) => (
                      <Badge key={flag} tone="warning">{flag}</Badge>
                    ))}
                  </div>
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
  agentStatus,
  agentResearch,
  agentLoading,
  agentError,
  onRunAgent,
}: {
  data: DragonIntelligenceResponse | null;
  loading: boolean;
  error: string | null;
  agentStatus: DragonAgentStatus | null;
  agentResearch: DragonAgentResearch | null;
  agentLoading: boolean;
  agentError: string | null;
  onRunAgent: () => void;
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
        <div className="rounded-md border border-hairline px-3 py-2.5">
          <div className="text-caption text-ink-3">成分股合力</div>
          <div className="text-body font-semibold text-ink">
            {data.cohesion_summary?.boards_measured ?? 0}/
            {data.cohesion_summary?.boards_total ?? 0} 个板块实测
          </div>
          <div className="text-caption text-ink-3">
            预期代理可比 {data.expectation_proxy_summary?.candidates_with_comparable_prior_snapshot ?? 0} 只
            · 历史快照 {data.lifecycle_summary?.history_snapshots_available ?? 0} 份
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
      <div className="grid gap-2 rounded-md border border-hairline px-3 py-2.5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-body font-medium text-ink">LLM Agent 研究</span>
          <Badge tone={agentStatus?.enabled ? "positive" : "muted"}>
            {agentStatus?.enabled ? "已启用" : "未配置/关闭"}
          </Badge>
          <Badge tone="outline">{agentStatus?.model ?? "OpenAI Responses"}</Badge>
          {agentStatus?.web_search_enabled ? (
            <Badge tone="normal">公开网页检索已开</Badge>
          ) : null}
        </div>
        <div className="text-body text-ink-3">
          {agentStatus?.detail ?? "正在读取 LLM Agent 配置…"}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="btn btn-primary btn-sm"
            disabled={!agentStatus?.enabled || agentLoading}
            onClick={onRunAgent}
          >
            {agentLoading ? "研究分析中…" : "运行 LLM 交叉研究"}
          </button>
          <span className="text-caption text-ink-3">仅在点击后调用；不改写评分、资格和仓位。</span>
        </div>
        {agentError ? (
          <div
            role="alert"
            className="rounded-md border border-warning-line bg-warning-soft px-3 py-2 text-body text-ink"
          >
            {agentError}
          </div>
        ) : null}
        {agentResearch ? (
          <div className="grid gap-2 rounded-md border border-hairline p-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={stanceTone(agentResearch.analysis.stance)}>
                {stanceLabel(agentResearch.analysis.stance)}
              </Badge>
              <Badge tone="muted">{confidenceLabel(agentResearch.analysis.confidence)}</Badge>
              <span className="text-caption text-ink-3">
                {agentResearch.model} · {new Date(agentResearch.generated_at).toLocaleString()}
              </span>
            </div>
            <p className="text-body text-ink-2">{agentResearch.analysis.summary}</p>
            {agentResearch.analysis.key_agreement.length ? (
              <div className="grid gap-1">
                <div className="text-caption font-medium text-ink-3">与量化证据一致</div>
                {agentResearch.analysis.key_agreement.map((item) => (
                  <div key={item} className="text-body text-ink-2">• {item}</div>
                ))}
              </div>
            ) : null}
            {agentResearch.analysis.key_disagreement.length ? (
              <div className="grid gap-1">
                <div className="text-caption font-medium text-ink-3">与量化证据分歧</div>
                {agentResearch.analysis.key_disagreement.map((item) => (
                  <div key={item} className="text-body text-ink-2">• {item}</div>
                ))}
              </div>
            ) : null}
            {agentResearch.analysis.evidence_for.length ? (
              <div className="grid gap-1">
                <div className="text-caption font-medium text-ink-3">补充支持证据</div>
                {agentResearch.analysis.evidence_for.map((item) => (
                  <div key={item} className="text-body text-ink-2">• {item}</div>
                ))}
              </div>
            ) : null}
            {agentResearch.analysis.evidence_against.length ? (
              <div className="grid gap-1">
                <div className="text-caption font-medium text-ink-3">补充风险证据</div>
                {agentResearch.analysis.evidence_against.map((item) => (
                  <div key={item} className="text-body text-ink-2">• {item}</div>
                ))}
              </div>
            ) : null}
            {agentResearch.analysis.unknowns.length ? (
              <div className="grid gap-1">
                <div className="text-caption font-medium text-ink-3">仍未验证</div>
                {agentResearch.analysis.unknowns.map((item) => (
                  <div key={item} className="text-body text-ink-3">• {item}</div>
                ))}
              </div>
            ) : null}
            {agentResearch.analysis.next_checks.length ? (
              <div className="grid gap-1">
                <div className="text-caption font-medium text-ink-3">建议验证</div>
                {agentResearch.analysis.next_checks.map((item) => (
                  <div key={item} className="text-body text-ink-2">→ {item}</div>
                ))}
              </div>
            ) : null}
            {agentResearch.analysis.caveats.map((item) => (
              <div key={item} className="text-caption text-ink-3">
                注意：{item}
              </div>
            ))}
            {agentResearch.citations.length ? (
              <div className="grid gap-1">
                <div className="text-caption font-medium text-ink-3">公开来源</div>
                {agentResearch.citations.map((item) => (
                  <a
                    key={item.url}
                    className="text-body text-brand underline"
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {item.title}
                  </a>
                ))}
              </div>
            ) : null}
            <div className="text-caption text-ink-3">{agentResearch.note}</div>
          </div>
        ) : null}
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
