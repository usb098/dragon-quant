# 龙头理解引擎与多理念专家协作

## 目标

在现有 prep 结果上增加只读的龙头认知层：整合市场情绪、主线、五角色、空间板与候选股证据；每个游资理念以独立 Expert Adapter 接入；协调层保留共识和分歧，不把观点压成平均分。

第一位接入专家为陈小群公开理念的规则化适配器。它不是人物本人，也不是联网 LLM Agent，不模仿个人口吻，不生成具体买卖指令。

## 数据流

\`\`\`mermaid
flowchart TD
  A[prep 已保存快照] --> B[Dragon Intelligence 纯计算引擎]
  B --> C[统一候选与客观证据]
  C --> D[市场情绪 / 主线 / 空间板 / 角色 / 前序快照]
  D --> E1[陈小群理念 Expert Adapter]
  D --> E2[未来独立游资 Expert Adapter]
  D --> E3[未来独立游资 Expert Adapter]
  E1 --> F[独立观点集合]
  E2 --> F
  E3 --> F
  F --> G{协同编排}
  G --> H[共识证据]
  G --> I[分歧与未知]
  H --> J[只读 API / 龙头理解工作台]
  I --> J
\`\`\`

## 独立专家契约

- 每个专家有独立 id、版本、理念元数据、独立 adapter 与观点输出。
- Adapter 输入相同的客观市场事实，不能读取或改写其他专家的观点。
- 观点至少包含 stance、confidence、summary、evidence_for、evidence_against、unknowns、risk_flags；专家元数据声明 market_scope、time_horizon、style、collaboration_roles。
- 协同层不做简单分数平均。单一专家标记 single_expert；同市场/同周期观点一致标记 aligned；结论冲突标记 divergent；适用市场或周期不同标记 non_comparable 并分组展示。每只候选独立计算协同状态。
- 后续接入真实 LLM Agent 时，Agent 负责公告/政策/产业链与预期差研究；必须提供来源、发布时间、事实时间和证据状态。无证据时返回 unknown。

## 当前实现边界

- 输入：本地已保存 prep snapshot 和最近前序 snapshot。
- 结构证据：市场周期、全市场空间板覆盖、主线排名/变化、板块涨停数/持续天数/集中度、角色、首封时间、开板次数、成交额/换手率等已有字段。
- 生命周期：仅基于当前与最近前序快照做粗粒度状态提示；不是完整事件链。
- 市场合力：当前只有板块静态代理，尚未实现成分股同步联动时序。
- 预期差：没有独立的一致预期基线前不评分。
- 决策隔离：read_only=true、decision_impact=false；不改变 prep 评分、资格、仓位、买卖规则。
- API：GET /api/prep/{trade_date}/dragon-intelligence，只读，无外部网络调用。

## 私有研究资料规划

用户后续提供的交割单、访谈、心法和复盘材料属于独立私有知识库，不放入公开仓库、不进入 Python wheel，也不默认上传云端。建议按专家 ID 分区，并保存来源、日期、原始文件哈希、抽取版本和引用定位；先蒸馏出可核对的理念条目，再由每位专家自己的 adapter 消费。跨专家协作只交换规范化观点与证据引用，不混合原始知识库。

## 下一阶段

1. 完成市场合力的成分股联动时间序列。
2. 建立事前市场一致预期快照与实际表现比较。
3. 建立首阴、反包、被关次数与新老龙头交接事件链。
4. 接入可配置的外部研究 Agent，并对引用、时效、冲突和失败做审计。
5. 通过历史 walk-forward 与消融实验验证后，才允许有限影响候选排序。
