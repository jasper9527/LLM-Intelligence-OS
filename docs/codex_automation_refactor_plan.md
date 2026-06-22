# 从脚本主导到 Codex 自动化主导的重构计划书

## 0. 背景与纠偏

当前仓库已经具备一个文件型情报系统雏形：`config/` 定义 sources、routing、taxonomy、automation，`scripts/` 执行采集、分类、发布、报告生成和站点构建，`data/` 保存结构化记录，`site/` 提供静态 HTML 阅读层。

但这套实现和目标之间存在一个关键偏差：当前设计默认由 Python 脚本主导信息获取，Codex/自动化任务更像调度器；而目标应是 Codex 自动化任务主导信息发现、语义筛选、跨源观察、结构化摘要与路由，脚本退到稳定基础设施层。

因此，本计划的核心重构方向是：

```text
旧范式：脚本主导
固定 sources.yaml → Python collectors → JSONL → review → reports/site

新范式：Codex 自动化主导
Codex Discovery Tasks → 结构化 candidate evidence → review gate → modules → reports/site
                  └→ Python scripts 负责落盘、校验、去重、构建和可复现处理
```

这不是取消脚本，而是重新划分职责：Codex 负责非结构化信息发现和智能整理；脚本负责 deterministic pipeline。

## 1. 重构目标

### 1.1 产品目标

将 LLM Intelligence OS 重构为一个云端 Codex 自动化主导的信息系统，使其能够：

1. 主动发现大模型算法领域的岗位、研究、公司、开源、benchmark、社区讨论和破圈信号；
2. 不局限于预设 RSS/API/job board；
3. 对信息进行语义级筛选、摘要、标注、可信度判断和路由建议；
4. 保留证据、来源、搜索线索、跳过原因和不确定性；
5. 通过 review gate 避免自动任务直接污染正式知识库；
6. 继续生成可跨设备阅读的静态 HTML 站点；
7. 不依赖本地机器长期运行。

### 1.2 工程目标

重构后的系统应具备：

1. Codex 自动化任务提示词与输入/输出契约；
2. candidate evidence 的统一数据模型；
3. discovery run 的日志与审计记录；
4. 自动任务写入 draft/review，而不是直接 publish；
5. 脚本化校验、去重、构建和测试；
6. 可逐步替换旧式 scripted collectors 的迁移路径。

### 1.3 非目标

本轮重构不追求：

1. 全网无差别抓取；
2. 社交平台无人值守大规模爬取；
3. 自动职业决策；
4. 自动个人学习规划；
5. 复杂数据库或知识图谱；
6. React/Next.js 前端重写；
7. 取消所有 Python 脚本。

## 2. 新旧职责划分

### 2.1 当前脚本主导职责

当前脚本适合做：

- 固定源抓取；
- JSONL 读写；
- 去重；
- 基础 tag inference；
- routing 执行；
- draft/review/publish 状态维护；
- report/site 生成；
- deployment manifest 更新；
- 单元测试和可复现检查。

这些能力应保留。

### 2.2 Codex 自动化应接管的职责

Codex 自动化任务应接管：

- 非固定源的信息发现；
- 跨源搜索与对比；
- 技术报告、岗位描述、论文页面、社区讨论的语义理解；
- hype / red flag / negative signal / breakout signal 识别；
- 信息是否值得进入系统的初筛；
- candidate evidence 的结构化摘要；
- route suggestion；
- source-quality notes；
- 每日/每周发现盲区；
- 月度认知沉淀候选。

### 2.3 脚本不再承担的职责

脚本不应承担：

- 模拟人类刷信息；
- 主动决定今天该关注什么；
- 对复杂网页进行深层语义判断；
- 判断某趋势是否 hype；
- 从非结构化社区讨论里抽取领域变化；
- 写长篇智能分析。

## 3. 目标架构

```text
Cloud Scheduler / Codex Automation
    ├─ Codex Daily Discovery
    ├─ Codex Weekly Deep Discovery
    ├─ Codex Monthly Synthesis Candidate
    └─ Codex Source Scout
              ↓
      candidate evidence files
              ↓
      validation + normalization scripts
              ↓
          Event Stream draft
              ↓
        Review / Publish / Reject
              ↓
    Job Radar / Research Radar / Tech Landscape / Source Map
              ↓
        Weekly Brief / Monthly Review
              ↓
          Static HTML Site
```

关键变化：信息获取入口从 `scripts/collect.py` 单入口扩展为：

```text
1. scripted_collect：稳定结构化源
2. codex_discovery：Codex 主动发现源
3. manual_submission：用户手动输入源
```

三类入口最终都进入统一 draft/review pipeline。

## 4. 新增核心概念

### 4.1 Candidate Evidence

Codex 自动化任务不应直接写正式 event，而应写 candidate evidence。

建议文件：

```text
data/codex_discovery/candidates/YYYY-MM-DD.jsonl
```

每条 candidate evidence 建议字段：

```json
{
  "candidate_id": "",
  "discovery_run_id": "",
  "date_found": "YYYY-MM-DD",
  "evidence_date": "YYYY-MM-DD",
  "title": "",
  "url": "",
  "source_name": "",
  "source_type": "official|paper|company_blog|job_board|open_source|community|social|newsletter|personal|unknown",
  "content_type": "paper|technical_report|job_description|model_release|benchmark|repo|blog|discussion|note",
  "short_summary": "",
  "why_it_matters": "",
  "why_maybe_not": "",
  "evidence_note": "",
  "credibility": "low|medium|high",
  "novelty": "incremental|notable|breakout",
  "relevance": "low|medium|high",
  "uncertainty": "",
  "entities": [],
  "area_tags": [],
  "method_tags": [],
  "task_tags": [],
  "job_tags": [],
  "signal_tags": [],
  "route_suggestion": [],
  "should_enter_review": true,
  "skip_reason": "",
  "created_by": "codex_automation"
}
```

### 4.2 Discovery Run Log

每次 Codex 自动化发现任务都应记录 run log，避免智能任务变成不可审计黑盒。

建议文件：

```text
data/codex_discovery/runs/YYYY-MM-DD_daily.json
```

字段建议：

```json
{
  "run_id": "",
  "run_type": "daily_discovery|weekly_deep_discovery|source_scout|monthly_synthesis_candidate",
  "started_at": "",
  "finished_at": "",
  "queries_or_focus_areas": [],
  "sources_checked": [],
  "candidates_written": 0,
  "items_skipped": [],
  "network_or_access_issues": [],
  "notes": ""
}
```

### 4.3 Codex Discovery Inbox

Codex 输出的 candidates 不直接 publish，而是进入 discovery inbox。

建议页面：

```text
site/discovery.html
```

展示：

- discovery run；
- candidate evidence；
- source；
- credibility/novelty/relevance；
- route suggestion；
- skip reason；
- needs_review；
- promote to event draft / archive / reject。

MVP 可先不做交互按钮，只做静态 review 页面。

## 5. 自动化任务设计

### 5.1 Codex Daily Discovery

频率：每天一次，必要时每日两次。

目标：发现过去 24-48 小时内的高价值外部信号。

覆盖面：

- 研究/论文/技术报告；
- 公司技术发布/模型发布；
- 岗位/JD/团队招聘信号；
- open-source / benchmark；
- negative / red flag / hype risk；
- breakout / 圈外信号。

输出：candidate evidence，不直接 publish。

### 5.2 Codex Weekly Deep Discovery

频率：每周一次，周报前运行。

目标：补足 daily discovery 和 scripted collectors 可能遗漏的重要信息。

重点：

- 本周重要技术报告；
- 社区讨论中反复出现但未进入固定源的问题；
- 岗位描述变化；
- 中外公司动态；
- 降温信号、红旗信号；
- 圈外方向。

输出：weekly candidate evidence 和 weekly brief 输入材料。

### 5.3 Codex Source Scout

频率：每两周或每月一次。

目标：发现值得加入 source map 的新信息源，而不是直接把它们加入自动抓取。

输出：source candidate list，包括：

- source name；
- URL；
- source type；
- coverage；
- expected signal quality；
- expected noise level；
- bias；
- best_for；
- not_good_for；
- 是否建议进入 scripted collector；
- 是否仅建议 Codex discovery 时偶尔访问。

### 5.4 Codex Monthly Synthesis Candidate

频率：每月一次，月报前运行。

目标：从本月 candidate evidence、events、reports、radar records 中提出 durable landscape update candidates。

输出：

- 哪些领域卡片可能需要更新；
- 更新证据；
- 反方证据；
- 不确定性；
- 不建议更新的原因。

## 6. 任务提示词草案

### 6.1 Daily Discovery Prompt

```text
你是 LLM Intelligence OS 的 Codex Daily Discovery 自动化任务。

目标：
主动发现过去 24-48 小时内与大模型算法职业与技术情报相关的高价值外部信号，并写入 candidate evidence。你不是 RSS 聚合器，也不是职业决策 agent。

系统边界：
- 你负责发现、筛选、摘要、证据记录、标签建议和路由建议。
- 你不能替用户决定职业方向、研究方向或学习计划。
- 你不能自动 publish。
- 不确定的信息进入 review，而不是进入正式模块。

必须覆盖的视角：
1. research / paper / technical report；
2. job / company / hiring signal；
3. model release / company technical update；
4. open-source / benchmark；
5. negative / red-flag / hype-risk；
6. breakout / 圈外信号。

信息源策略：
- 优先官方、原始、可引用来源。
- 社区和社交媒体只能作为弱信号，除非有原始来源或多源交叉验证。
- 不要收泛 AI 新闻、营销软文、融资新闻，除非它们明确影响大模型算法岗位、研究或技术路线。
- 不要只围绕已有方向搜索。

执行步骤：
1. 检查当前日期和 git 状态。
2. 确定本次 run_id。
3. 搜索或浏览候选信息。
4. 对每条候选信息判断 credibility、novelty、relevance。
5. 最多写入 5-10 条 candidate evidence。
6. 为每条 evidence 写清 why_it_matters、why_maybe_not、uncertainty、route_suggestion。
7. 写入 data/codex_discovery/candidates/YYYY-MM-DD.jsonl。
8. 写入 data/codex_discovery/runs/YYYY-MM-DD_daily.json。
9. 如已有导入脚本，则运行导入脚本将 candidates 转为 Event Stream draft；否则只保留 candidates，不直接改正式数据。
10. 如页面受影响，重建静态站点。
11. 提交有意义的变更。

输出摘要：
- 本次检查的 source/query/focus areas；
- 写入 candidate 数量；
- 按类型统计；
- 被跳过的信息和原因；
- 网络或访问失败；
- commit hash。
```

### 6.2 Weekly Deep Discovery Prompt

```text
你是 LLM Intelligence OS 的 Codex Weekly Deep Discovery 自动化任务。

目标：
在周报生成前，补足固定源和每日发现可能遗漏的重要信息，尤其是需要跨源对比、语义判断或圈外探索的信息。

重点寻找：
1. 本周重要论文、技术报告、benchmark、repo；
2. 大厂和头部 AI 公司岗位描述或技术布局变化；
3. 社区反复讨论但尚未进入系统的研究问题；
4. 负面证据、红旗岗位、hype risk；
5. 用户可能不会主动关注但外部变重要的方向。

执行要求：
- 最多写入 15 条 candidate evidence。
- 每条必须有 URL 或明确 evidence_note。
- 每条必须说明为什么值得进入系统，以及为什么可能不重要。
- 每条必须给 route_suggestion。
- 不自动 publish。
- 不写个人建议。

输出位置：
- data/codex_discovery/candidates/YYYY-WW_weekly.jsonl
- data/codex_discovery/runs/YYYY-WW_weekly.json

结束时输出：
- 本周补足了哪些盲区；
- 哪些信息不确定；
- 哪些应进入 weekly brief candidate；
- 哪些应只 archive。
```

### 6.3 Source Scout Prompt

```text
你是 LLM Intelligence OS 的 Codex Source Scout 自动化任务。

目标：
发现和评估可能适合进入系统的信息源。你不能直接把大量新源加入自动抓取配置，除非有明确理由和低风险。

任务：
1. 检查现有 config/sources.yaml 和 data/sources.jsonl。
2. 识别当前 source coverage 缺口。
3. 提出最多 10 个候选 source。
4. 对每个 source 写明 coverage、signal_quality、noise_level、bias、best_for、not_good_for。
5. 建议该 source 适合 scripted collector、Codex discovery occasional browsing，还是 manual-only。
6. 不直接加入 sources.yaml，除非用户明确要求。

输出位置：
- data/codex_discovery/source_candidates/YYYY-MM-DD.json

输出摘要：
- coverage gaps；
- recommended sources；
- sources not recommended；
- rationale and risks。
```

### 6.4 Monthly Synthesis Candidate Prompt

```text
你是 LLM Intelligence OS 的 Codex Monthly Synthesis Candidate 自动化任务。

目标：
从本月 collected events、candidate evidence、weekly briefs、job/research/source/landscape records 中提炼可能需要长期沉淀的 Tech Landscape 更新候选。

要求：
- 不做职业方向决策。
- 不用评分替代证据。
- 必须保留争议、反方证据和不确定性。
- 不直接覆盖 landscape card，先写 update candidate。

输出：
- 哪些 landscape card 可能需要更新；
- 新增 evidence；
- negative evidence；
- controversies；
- open questions；
- 是否建议进入 monthly review。

输出位置：
- data/codex_discovery/landscape_update_candidates/YYYY-MM.json
```

## 7. 数据流改造计划

### Phase 1：只加 Codex Discovery Inbox，不改旧 pipeline

目标：最小风险验证 Codex 自动化获取是否可用。

变更：

1. 新增 `data/codex_discovery/` 目录结构；
2. 新增 candidate evidence schema 文档；
3. 新增 discovery run log schema 文档；
4. Codex 自动化任务先只写 candidates，不改 `data/events.jsonl`；
5. 新增或扩展 HTML 页面展示 discovery candidates。

验收：

- Codex 任务能稳定写入 candidates；
- 每条 candidate 有 evidence；
- 能看到 skip reason 和 uncertainty；
- 不影响现有站点和测试。

### Phase 2：Candidates 转 Event Draft

目标：把 Codex candidates 纳入统一 review pipeline。

变更：

1. 新增 `scripts/import_codex_candidates.py`；
2. 将 approved/eligible candidates 转为 Event Stream draft；
3. 增加去重逻辑：candidate URL/title/source/date 与 existing events 比对；
4. 在 review 页面标记来源为 `codex_discovery`；
5. 保留 candidate_id 与 event_id 映射。

验收：

- Codex candidates 能进入 draft；
- 不自动 publish；
- 重复 candidate 不重复创建 event；
- review 页面能区分 scripted/manual/codex 来源。

### Phase 3：Codex Discovery 成为主入口

目标：信息发现由 Codex 自动化主导，脚本采集成为稳定补充。

变更：

1. Daily task 默认先运行 Codex Discovery；
2. scripted collectors 只负责高稳定源；
3. Weekly brief 优先读取 reviewed Codex candidates 和 events；
4. Source Map 记录 Codex discovery 访问过的 source；
5. Report 中展示 `source_path`: scripted / codex / manual。

验收：

- 周报中大部分高价值信号来自 Codex discovery 或 Codex+scripted 组合；
- scripted collectors 不再定义系统信息边界；
- 用户可以看到 Codex 发现了什么、跳过了什么、为什么。

### Phase 4：Source Scout 与 Landscape Synthesis

目标：让 Codex 不只是发现信息，还帮助维护信息源地图和长期领域状态。

变更：

1. Source Scout 定期生成 source candidates；
2. Monthly Synthesis Candidate 生成 landscape update candidates；
3. Source Map 增加 discovered_by、last_seen_by_codex、recommended_collection_mode；
4. Tech Landscape 更新进入人工 review。

验收：

- 新 source 不再随意加入，而是有 source-quality 评估；
- landscape updates 有证据链和反方观点；
- 月报能沉淀长期变化，而不只是新闻摘要。

## 8. 文件结构调整建议

建议新增：

```text
data/codex_discovery/
  candidates/
  runs/
  source_candidates/
  landscape_update_candidates/
  mappings/

docs/
  codex_automation_refactor_plan.md
  codex_candidate_schema.md

templates/
  discovery.html

site/
  discovery.html

scripts/
  validate_codex_candidates.py
  import_codex_candidates.py
```

其中脚本只负责校验和导入，不负责替 Codex 发现信息。

## 9. 风险与应对

### 9.1 风险：Codex 输出不稳定

应对：

- 固定 candidate schema；
- 增加 validation script；
- 不直接 publish；
- invalid candidate 留在 discovery inbox。

### 9.2 风险：Codex 搜索结果漂移

应对：

- 记录 run log；
- 记录 queries/focus areas/sources checked；
- 记录 skipped items；
- 每周 deep discovery 补漏。

### 9.3 风险：信息质量下降

应对：

- credibility/novelty/relevance 三维判断；
- source-quality note；
- 社交媒体只作为弱信号；
- review gate。

### 9.4 风险：系统越界成职业规划 agent

应对：

- 所有 prompt 明确禁止 personal recommendation；
- report 保持导航和分析，不输出决策；
- action item 不作为核心输出。

### 9.5 风险：成本和运行时间过高

应对：

- daily discovery 限制 5-10 条 candidate；
- weekly deep discovery 限制 15 条 candidate；
- source scout 低频运行；
- scripted collectors 保留用于稳定源。

## 10. 实施顺序

建议实施顺序：

1. 新增 candidate evidence schema；
2. 新增 discovery run log schema；
3. 新增 `data/codex_discovery/` 目录和 `.gitkeep`；
4. 新增 validate script；
5. 新增 discovery inbox 静态页面；
6. 将 Codex Daily Discovery 配置为只写 candidates；
7. 运行 3-5 天试验；
8. 新增 import script，将 candidates 转 draft events；
9. 将 Weekly Brief 纳入 Codex candidates；
10. 再讨论是否收缩或弱化旧 scripted collectors。

## 11. 第一轮试运行标准

第一轮试运行不应追求覆盖广，而应验证：

1. Codex 是否能发现固定源之外的信息；
2. candidate evidence 是否结构化、可审计；
3. 是否能保留 negative/red-flag/breakout signals；
4. 是否能避免个人决策输出；
5. 是否能顺利进入 review；
6. 是否比单纯 scripted collectors 更有“情报感”；
7. 是否没有污染正式数据。

## 12. 与当前文档的关系

当前 `docs/architecture_v1.md` 仍可作为产品边界和模块目标参考，但其中关于 collection 的表述需要在后续修订为 Codex automation first。

当前 `docs/cloud_automation_prompts.md` 可保留部分通用任务规则，但需要新增 Codex Discovery、Weekly Deep Discovery、Source Scout、Monthly Synthesis Candidate，并降低 `python scripts/collect.py` 在信息获取中的主导地位。

## 13. 下一步动手前的确认点

在开始改运行代码前，需要确认：

1. Codex candidates 是先写 `data/codex_discovery/candidates/`，还是直接写 `data/raw/manual_submissions.jsonl`？
2. 是否需要新增 `site/discovery.html` 作为独立 review 页面？
3. candidate → event draft 是否需要人工 gate，还是满足 schema 后自动进入 draft？
4. Codex Daily Discovery 的信息范围是否限制在过去 24-48 小时？
5. 社交/社区源是否只作为 weak signal？
6. discovery run log 是否必须记录搜索 query？
7. 第一周是否保留现有 Python scripted collectors 作为稳定源补充？

默认建议：

- 先写 `data/codex_discovery/candidates/`；
- 新增 `site/discovery.html`；
- candidate 到 event draft 通过 import script 自动进入 draft，但不 publish；
- 社交/社区源只作为 weak signal；
- 第一周保留现有 scripted collectors。
