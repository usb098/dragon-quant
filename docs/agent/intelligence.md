# intelligence — 龙头理解引擎与独立理念专家

> 触发：新增或修改龙头理解引擎、理念专家 Adapter、多专家协同、专家知识库接入时读取本文。
> 上游权威：AGENTS.md、docs/agent/architecture.md、docs/agent/prep-auction.md。

## 边界

- 龙头理解是 prep 快照之上的只读研究层，不另造一套涨停池、主线或角色识别。
- 引擎可扩大候选集合：合并 prep review_candidates、空间板和主线龙头，不仅验证扫描器 Top N。
- 量化层提供客观指标与覆盖状态；理念专家独立解释，不修改基础事实。
- 当前首个专家为陈小群公开理念的确定性规则 Adapter，不是本人、不代表本人、不做角色扮演，也不是联网 LLM Agent。
- 结果契约固定 read_only=true、decision_impact=false；不得直接改变评分、资格、仓位、买卖规则或实盘信号。

## Expert Adapter 契约

每位游资理念必须保持独立命名空间、版本、知识库与 Adapter。专家元数据还应声明 market_scope、time_horizon、style 和 collaboration_roles。Adapter 接收统一的只读 context 和单个 candidate，返回 JSON-compatible 观点：

- stance：supportive / neutral / cautious / insufficient_evidence。
- confidence：high / medium / low。
- summary：简要判断。
- evidence_for / evidence_against：支持和反向证据。
- unknowns：缺失、未验证或超出该理念适用边界的内容。
- risk_flags：结构化风险标签。

新增专家步骤：新建 experts/<expert_id>.py，实现 analyze_candidate；在 registry.py 显式注册；补齐样本测试；不要复制其他专家的规则或观点输出。

## 多专家协同

- 同一份客观事实分别送给各专家，专家之间不读取彼此判断。
- 协同层比较方向、置信度、证据质量和适用场景。
- 只有一个专家时标记 single_expert，不得称为共识。
- 多专家适用市场与持有周期一致时才比较方向：一致标记 aligned；相反标记 divergent，并展示分歧原因，不做简单平均分。
- 市场范围或持有周期不同/未声明时标记 non_comparable，按各自适用范围分组展示，不强行投票。
- 每只候选单独计算专家协同状态；全局摘要只针对总龙头或首个候选，不能替代逐股观点。
- 任一专家缺少有效判断时标记 insufficient_evidence，不把“观点 + 未知”误报为分歧。
- 适用周期、持仓周期、交易品种和流动性偏好不一致时，先分组比较，不强求统一结论。
- 可扩展的协同方式包括共识验证、互补视角、反方质询和风险审查；协调器不能覆盖专家原始输出。

## 当前证据边界

- 市场情绪取 prep market / emotion_cycle。
- 主线地位和角色取 prep mainlines / review_candidates / leaders。
- 全市场总龙头仍依赖空间板覆盖完整、唯一最高板与主线 leader 交叉确认。
- 市场合力现阶段只有板块涨停家数、持续天数、集中度等静态代理；缺少成分股联动时序。
- 预期差缺少独立事前市场共识快照时必须 unknown。
- 生命周期只做当前与最近前序快照的粗粒度提示；首阴、反包、被关次数等事件链未来补齐。
- 外部题材催化、公告与产业链研究需未来独立 Agent 提供有来源、发布时间和证据状态的结果。

## 私有资料与知识库

用户提供的交割单、访谈、心法、复盘等资料属于私有研究资产：

- 原始文件不提交到 Git、不进入 wheel、不自动上传外部服务。
- 按 expert_id 隔离存储；保留来源、原始文件哈希、日期、解析版本和引用定位。
- 蒸馏产物应能回溯原始材料；事实、本人公开表达、二手整理、研究者推断要分开标记。
- 专家之间只交换规范化结论与证据引用，不互相污染原始知识库。
- 对交割单做统计时必须记录样本窗口、资金规模、成交可得性、滑点/费用与幸存者偏差；不能从少数案例反推通用规则。

## LLM Research Agent

- 服务端模块：`dragon_quant/intelligence/llm_agent.py`；调用 OpenAI Responses API，使用 JSON Schema Structured Outputs。
- 默认关闭；只有设置 `OPENAI_API_KEY` 且 `DQ_INTELLIGENCE_LLM_ENABLED=1` 才能运行。浏览器只请求本项目后端，绝不接触 API Key。
- 可选公开网页检索由 `DQ_INTELLIGENCE_WEB_SEARCH=1` 单独启用；默认关闭。用户点击按钮后才发起一次研究请求。
- Agent 输入是量化结果的紧凑结构化摘要，不包含原始交割单、心法原件或私有文档；没有持久化 LLM 输出的数据库写操作。
- Web Search 引用从 Responses `url_citation` annotations 提取；无引用时不展示虚构链接。
- LLM 输出只作研究交叉检查，固定 read_only=true、decision_impact=false；不得直接改评分、资格、仓位或实盘。
- 资料蒸馏完整流程见 `docs/agent/distillation.md`；模板位于 `docs/templates/`。


## 第二阶段能力

- **市场合力**：使用 `intelligence/cohesion.py` 对板块成分股近端日 K 计算覆盖率、涨跌占比、收益相关性和同步方向日；覆盖与共同历史达标才标记 measured。
- **事前预期差**：优先比较 T-1 `prev_plan.feedback_plans[].expected` 冻结的 gap_low/gap_high/ratio_low 与 T 日 `feedback.items` 里的实际竞价缺口、竞价额比和反馈状态。来源标记为 frozen_previous_plan_feedback 或 frozen_config_expectation；缺失时退回 prior_snapshot_framework_proxy / unknown。它不是全市场一致预期。
- **生命周期**：最多回溯 10 份快照，并使用当前 `stock_daily` 与反馈 evidence 补充近端首次收阴、收阴后转强、阳线实体反包与盘中开板事件。日 K 或反馈不足时未评估；观察连续数不是完整交易日连续数。
- **公网安全**：`DQ_PUBLIC_DEPLOYMENT=1` 时强制 Basic Auth（密码至少 32 字符）与 `DQ_ALLOWED_HOSTS`。`/health` 仅供部署健康探针绕过认证与 Host 白名单；其它路由仍需认证。
