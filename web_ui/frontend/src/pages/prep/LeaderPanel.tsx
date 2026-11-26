import { Badge } from "../../components/Badge";
import { display, type LeaderAnalysisView } from "./prepModel";

const STATUS_LABELS: Record<string, string> = {
  identified: "已识别",
  contested: "高标并列",
  provisional: "暂定候选",
  unconfirmed: "待交叉验证",
  unavailable: "不可判",
};

const REASON_LABELS: Record<string, string> = {
  limit_up_pool_missing: "缺少全市场涨停池",
  limit_up_pool_incomplete: "涨停池分页不完整，最高板只是已观测下界",
  multiple_stocks_share_space_board: "多只股票并列最高板",
  space_board_not_mainline_leader: "空间板尚未同时满足主线龙头条件",
  mainline_leader_unavailable: "主线龙头证据不足",
  space_board_unavailable: "没有可识别的连板高度",
};

function statusTone(status: string | null): "positive" | "warning" | "muted" {
  if (status === "identified") return "positive";
  if (status === "contested" || status === "provisional") return "warning";
  return "muted";
}

export function LeaderPanel({ data }: { data: LeaderAnalysisView | null }) {
  if (!data) {
    return (
      <div className="text-body text-ink-3">
        该历史快照尚无空间板分析字段，请对该日运行 prep --recompute。
      </div>
    );
  }

  const status = data.totalLeaderStatus;
  const leaderCode = data.totalLeaderCode ?? data.totalLeaderCandidateCode;
  const leaderName = data.totalLeaderName ?? data.totalLeaderCandidateName;
  const leaderTitle = status === "identified" ? "总龙头" : "总龙头候选";
  const coverageLabel = data.coverageComplete === true
    ? "全量涨停池 " + (data.observedTotal ?? "—") + " 只"
    : "涨停池不完整（已观测 " + (data.observedTotal ?? "—") +
      " / 报告 " + (data.reportedTotal ?? "—") + "）";

  return (
    <div className="grid gap-3">
      <div className="grid gap-2 md:grid-cols-3">
        <div className="grid content-start gap-1 rounded-md border border-hairline px-3 py-2.5">
          <div className="text-caption text-ink-3">情绪周期</div>
          <div className="text-body font-semibold text-ink">{data.phaseLabel ?? "待观察"}</div>
          <div className="text-caption text-ink-3">解释性标签，不直接驱动买卖或仓位</div>
        </div>
        <div className="grid content-start gap-1 rounded-md border border-hairline px-3 py-2.5">
          <div className="text-caption text-ink-3">全市场空间板</div>
          <div className="text-body font-semibold text-ink">
            {data.spaceBoardHeight == null ? "—" : data.spaceBoardHeight + " 板"}
          </div>
          <div className="text-caption text-ink-2">
            {data.spaceBoardCount} 只并列最高板
            {data.spaceStocks.length ? " · " + data.spaceStocks.map((item) => item.code).join("、") : ""}
          </div>
        </div>
        <div className="grid content-start gap-1 rounded-md border border-hairline px-3 py-2.5">
          <div className="flex items-center gap-2">
            <div className="text-caption text-ink-3">{leaderTitle}</div>
            <Badge tone={statusTone(status)}>{STATUS_LABELS[status ?? ""] ?? "待确认"}</Badge>
          </div>
          <div className="text-body font-semibold text-ink">
            {leaderCode ? leaderCode + " " + (leaderName ?? "") : "暂不指定"}
          </div>
          <div className="text-caption text-ink-3">
            {REASON_LABELS[data.totalLeaderReason ?? ""] ?? data.totalLeaderReason ?? "缺少确认依据"}
          </div>
        </div>
      </div>

      <div className="grid gap-2 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="grid content-start gap-2 rounded-md border border-hairline px-3 py-2.5">
          <div className="text-body font-medium text-ink">连板梯队</div>
          {data.ladder.length ? (
            <div className="grid gap-1">
              {data.ladder.slice(0, 6).map((item) => (
                <div key={item.height} className="flex items-center justify-between gap-3 text-body">
                  <span className="num text-ink">{item.height} 板</span>
                  <span className="num text-ink-2">{item.count} 只</span>
                  <span className="truncate text-caption text-ink-3">{item.codes.join("、")}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-body text-ink-3">无可用连板梯队数据。</div>
          )}
        </div>
        <div className="grid content-start gap-2 rounded-md border border-hairline px-3 py-2.5">
          <div className="text-body font-medium text-ink">主线龙头</div>
          {data.mainlineLeaders.length ? (
            <div className="grid gap-1">
              {data.mainlineLeaders.slice(0, 5).map((item) => (
                <div key={(item.mainline ?? "mainline") + "-" + item.code}
                     className="flex flex-wrap items-center justify-between gap-2 text-body">
                  <span className="text-ink-2">{item.mainline ?? "主线待归属"}</span>
                  <span className="num text-ink">
                    {item.code} · {item.height == null ? "—" : item.height + " 板"}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-body text-ink-3">当前无可识别的主线龙头。</div>
          )}
        </div>
      </div>
      <div className="text-caption text-ink-3">
        {coverageLabel}。只有覆盖完整、唯一最高空间板且属于主线 leader 时才确认总龙头；否则保持待确认。
      </div>
    </div>
  );
}
