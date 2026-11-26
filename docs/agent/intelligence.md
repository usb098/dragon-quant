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
