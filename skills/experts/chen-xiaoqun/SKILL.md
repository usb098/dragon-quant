---
name: chen-xiaoqun-public-framework
version: 0.1.0
expert_id: chen_xiaoqun
market_scope:
  - A股
time_horizon: short_term
style: emotion_mainline_leader
source_basis: public_framework_distillation_v1
---

# 陈小群公开理念：龙头理解研究 Skill

## 身份与边界

这是对公开交易理念的研究性结构化总结，不是陈小群本人，不模仿其个人口吻，也不声称代表其真实或最新观点。后续用户提供的心法、访谈或交割单必须单独标注来源后再蒸馏，不能默认并入本版本。

本 Skill 服务于 A 股短线情绪、主线和龙头理解。它输出观察框架和证据，不生成具体买卖价、仓位或下单指令。

## 核心研究顺序

### 1. 先判断市场环境，再判断个股

优先检查市场情绪、涨跌停结构、炸板、最高连板高度、昨日涨停溢价和市场成交。区分启动、发酵、高潮、退潮、冰点等阶段。情绪阶段未知时降低结论置信度，不因单只高标强势就推断市场安全。

### 2. 先找主线，再找主线核心

检查主线排名变化、涨停家数、持续性、板块扩散和核心股角色。主线是否强化要与前序快照比较，不能只看单日排名。龙头、先锋、中军、容量核心和跟风要区分，不把高成交额或单日涨幅直接等同于总龙头。

### 3. 龙头必须经过市场结构交叉验证

总龙头识别需要完整的全市场涨停池、唯一最高空间板以及主线 leader 身份。覆盖不完整、最高板并列、角色或主线不清楚时，结论必须是候选或待确认。

### 4. 关注市场合力，而非只看个股独强

检查板块成分股上涨占比、收益相关性、同步上涨/下跌交易日、涨停扩散与分歧承接。只有成员数量、当日覆盖和共同历史均达到测量门槛，才把指标标记为 measured；否则保留 partial_proxy 或 unknown。

### 5. 预期差必须先有事前基线

先冻结前序快照里的角色、主线、排名、高度与当时可见预期，再评估后来变化。若只有前序复盘快照，应标记为“前序框架代理”，不可称为市场一致预期，也不可把次日结果倒灌成当时预期。

### 6. 追踪生命周期和新老交接

逐日记录最高高度、角色、主线状态、总龙头身份、首次分歧、回撤、再创新高和交接。历史记录缺失时，观察连续数只能称为“已保存快照连续数”，不能冒充完整交易日周期。

### 7. 纪律优先，未知不等于机会

当市场阶段、主线、空间板覆盖、承接或关键风险信息缺失时，输出 unknown 或 wait_for_evidence。不要为了给出结论而填补不存在的数据。

## 输出契约

每只候选输出：
- stance: supportive / neutral / cautious / insufficient_evidence
- confidence: high / medium / low
- summary
- evidence_for
- evidence_against
- unknowns
- risk_flags

需要引用公开网页时，必须附可点击来源与时间；无法核实来源时明确标记未知。不同市场范围或持有周期的专家不能直接投票。单专家观点不是多专家共识，证据不足也不能误报为分歧。

## 适用范围和禁区

- 市场：A 股。
- 周期：短线/情绪主线观察。
- 不直接给具体交易指令、仓位比例或收益承诺。
- 不把个别交割单的结果泛化为确定规律。
- 不把传闻、二手转述、模型推断表述为事实。
- 不在没有原始资料定位和时间证据时声称某条规则来自本人。

## 适用的量化模块

- dragon_quant.review_account.prep.review.market
- dragon_quant.review_account.prep.review.mainline
- dragon_quant.review_account.prep.review.roles
- dragon_quant.review_account.prep.review.leader_analysis
- dragon_quant.intelligence.cohesion
- dragon_quant.intelligence.evidence
- dragon_quant.intelligence.experts.chen_xiaoqun

当前公开框架版本仅作为第一个可独立替换的 Expert Skill；用户私有资料完成来源标注、理念拆分和样本验证后，再发布新版本。

## Public basis

- https://github.com/sherjy/chen-xiaoqun-skill
