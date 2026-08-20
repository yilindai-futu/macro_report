<!--
更新时间：2026-08-20 北京时间
状态：待对齐（草稿）
-->

# Phase 1 详细需求文档

> **目的**：与产品/技术负责人对齐 MVP 交付范围、技术方案选型与验收标准。  
> **对应路线图**：business_plan.md § Phase 1（0–3 个月）  
> **预计交付日期**：2026-11-20

---

## 0. 阅前须知：本文档的使用方式

本文档分三个层次：

| 章节 | 受众 | 预期动作 |
|---|---|---|
| §1–§3 交付范围与用户故事 | 产品负责人 | 确认范围边界；标注"超期"或"必须" |
| §4–§7 技术方案与架构 | 技术负责人 | 确认选型；填写"待定"字段 |
| §8–§9 验收标准与里程碑 | 双方 | 确认 DoD（Definition of Done）和节点日期 |

**需要在对齐会议上拍板的决策**已用 🔴 标注；可在会后异步确认的标注 🟡。

---

## 1. Phase 1 交付范围（Scope）

### 1.1 交付物（In Scope）

| # | 交付物 | 说明 |
|---|---|---|
| P1-D1 | **数据采集管道** | FRED、Unusual Whales、SEC EDGAR 三路数据的拉取、清洗、入库 |
| P1-D2 | **每周宏观报告生成脚本** | 多智能体流程，每周五 HKT 18:00 触发，生成结构化报告存入数据库 |
| P1-D3 | **报告展示 Web 页面** | 登录后可查看最新报告（Markdown 渲染），含数据来源侧边栏 |
| P1-D4 | **管理员手动触发入口** | Admin 页面可手动触发一次报告生成（用于测试和内测） |
| P1-D5 | **内测用户管理** | 基于现有 `app_user` / `auth_token`，支持手动添加内测用户（不含付费订阅） |
| P1-D6 | **基础幻觉防控** | 强制数据引用字段、数据时效标注、Critic 校验步骤 |

### 1.2 明确不在 Phase 1 内（Out of Scope）

以下内容明确推迟至 Phase 2 或更晚，**不进入本次迭代**：

- 每日快讯（Daily Brief）
- 可交互 AI 问答
- 付费订阅（Stripe）
- 期权流实时推送告警
- 中文双语版本
- PDF 导出
- API 对外授权
- RAG 向量检索（Phase 1 用结构化数据直接注入 context，无需 pgvector）
- 邮件推送

> **说明**：Phase 1 刻意保持最小范围——先跑通"数据采集 → AI 分析 → 可读报告"的完整闭环，再在 Phase 2 堆叠功能。

---

## 2. 用户故事（User Stories）

### 2.1 核心流程（必须，Phase 1 DoD）

**US-01 管理员触发报告生成**
```
作为管理员（is_admin=true），
我可以在 /admin 页面点击"立即生成本周宏观报告"，
系统在 5 分钟内完成生成并提示"报告已就绪"，
以便我在内测前手动验证报告质量。
```

**US-02 内测用户查看报告**
```
作为已登录的内测用户，
我可以访问首页看到最新一期的宏观报告，
报告包含七个分析维度、每个数据点均标注来源和数据时效，
以便我判断分析质量并提供反馈。
```

**US-03 自动定时生成**
```
作为系统，
每周五 HKT 18:00 自动触发一次报告生成任务，
生成失败时写入错误日志并发送 CloudWatch Alarm，
以便保证报告按时可用、无需人工干预。
```

**US-04 数据时效可见**
```
作为报告读者，
我可以在报告每个数据块旁看到"数据截至 YYYY-MM-DD HH:MM UTC"，
并且看到距上次刷新的时间（如"23 小时前"），
以便判断数据是否足够新鲜。
```

### 2.2 扩展故事（Nice to Have，Phase 1 如有余力）

**US-05 报告历史存档**
```
作为内测用户，
我可以查看过去 4 期报告的存档列表，
以便对比观点变化。
```

**US-06 管理员查看生成日志**
```
作为管理员，
我可以在 /admin/scripts 看到每次报告生成任务的运行状态和 CloudWatch 日志链接，
以便快速诊断生成失败的原因。
```

---

## 3. 报告内容规格（Product Spec）

### 3.1 报告结构（七个维度，固定顺序）

每期报告必须包含以下七个章节，缺少任一视为生成失败：

```
# 美股宏观周报 YYYY-WW期
> 数据截至：YYYY-MM-DD | 生成于：YYYY-MM-DD HH:MM UTC

## 执行摘要（200 字内）

## 1. 美联储政策
- 利率现状与路径预测
- 通胀趋势（CPI / PCE）
- 资产负债表进展（QT 规模）

## 2. 经济周期定位
- 当前周期阶段判断（早/中/晚/衰退）+ 依据
- GDP 增速、ISM PMI 最新读数
- 就业市场（NFP、JOLTS 离职率）

## 3. 收益率曲线
- 2s10s 利差及趋势
- 10 年期实际收益率
- 曲线形态对金融板块的含义

## 4. 企业盈利周期
- S&P 500 当期盈利季进度（beat/miss 率）
- 下一季 EPS 预测共识
- 利润率压力点

## 5. 板块轮动信号
- 基于当前周期阶段的建议配置（超配/中配/低配各板块）
- 最近 5 日板块 ETF 资金流向异动
- 当前最强/最弱板块（相对 SPX 表现）

## 6. 期权市场情绪
- VIX 水平与趋势
- Put/Call Ratio（20日均值 vs 当前）
- 异常期权流向（如有，附大单明细）

## 7. 主要风险因素
- 当前 Top 3 宏观风险（各 2–3 句）
- 与上期相比的风险变化

---
### 数据来源

| 章节 | 数据来源 | 最新数据时间 | API 序列/端点 |
|---|---|---|---|
| 美联储政策 | FRED | ... | FEDFUNDS, CPIAUCSL, ... |
| ... | ... | ... | ... |
```

### 3.2 质量门禁（Quality Gates）

生成完成后，Critic Agent 对以下条件逐一检查，任一不通过则标记为 `DRAFT`（不对用户展示），并触发告警：

| 检查项 | 规则 |
|---|---|
| **数据完整性** | 七个章节均存在且非空 |
| **数字可溯源** | 报告中所有数值必须在"数据来源"表中有对应记录 |
| **数据时效** | 所有数据源的 `latest_data_time` 均在过去 7 天内 |
| **字数约束** | 执行摘要 ≤ 200 字；各章节 ≥ 150 字 |
| **无占位符** | 不含 `[TODO]`、`[PLACEHOLDER]`、`N/A`（需处理的情况须有文字说明） |

---

## 4. 数据采集规格（Data Spec）

### 4.1 FRED（美联储经济数据）

- **接入方式**：FRED REST API（免费，需申请 API Key）
- **刷新频率**：每天 UTC 14:00（美国东部时间上午，数据发布窗口后）
- **拉取序列清单**（Phase 1 最小集）：

| FRED 序列 ID | 指标名称 | 频率 | 用于报告章节 |
|---|---|---|---|
| `FEDFUNDS` | 联邦基金利率（实际） | 月 | §1 |
| `CPIAUCSL` | CPI 全项（同比）| 月 | §1 |
| `PCEPILFE` | 核心 PCE 物价指数 | 月 | §1 |
| `T10YIE` | 10年 TIPS breakeven 通胀率 | 日 | §1 |
| `GDPC1` | 实际 GDP（季调年化）| 季 | §2 |
| `MANEMP` | 制造业就业人数 | 月 | §2 |
| `JTSJOL` | JOLTS 职位空缺数 | 月 | §2 |
| `UNRATE` | 失业率 | 月 | §2 |
| `PAYEMS` | 非农就业人数（NFP） | 月 | §2 |
| `ISRATIO` | 零售库存销售比 | 月 | §2 |
| `T10Y2Y` | 10年-2年国债利差（2s10s）| 日 | §3 |
| `REALGDP` | 实际 GDP 增长率 | 季 | §2 |
| `T10YFF` | 10年利率 - 联邦基金利率利差 | 日 | §3 |

> 🔴 **需对齐**：是否还需要接入 ISM PMI？ISM 数据不在 FRED 免费 API，需 ISM 官网或第三方（如 Trading Economics 付费）。Phase 1 可暂时引用 PMI 文字描述而非实时数值。

### 4.2 Unusual Whales（期权市场数据）

- **接入方式**：Unusual Whales REST API
- **刷新频率**：每个交易日收盘后（UTC 21:00）
- **拉取端点**（Phase 1）：

| 端点 | 数据内容 | 用于章节 |
|---|---|---|
| `/api/market/vix` | VIX 当日收盘及 20日均值 | §6 |
| `/api/market/options-flow/summary` | 日度 Put/Call Ratio | §6 |
| `/api/market/dark-pool/recent` | 近 5 日大单暗池流向 Top 10 | §6 |
| `/api/etf/sector-flow` | 板块 ETF 近 5 日资金净流入/出 | §5 |
| `/api/market/unusual-options` | 异常期权大单（当日，按 premium 排序 Top 20）| §6 |

> 🔴 **需对齐**：Unusual Whales API 月费约 $79–$199（取决于套餐）。确认预算是否批准，或是否有替代免费数据源（CBOE 官网、Yahoo Finance options）作为 Phase 1 占位。
>
> 🟡 **备选方案**：若 Unusual Whales 无法在 Phase 1 接入，§5 板块 ETF 数据可暂用 Yahoo Finance yfinance 库（免费），§6 期权情绪可暂用 CBOE 官网 VIX 数据 + FRED `VIXCLS` 序列（日度 VIX 收盘价，免费）。

### 4.3 SEC EDGAR（财报数据）

- **接入方式**：SEC EDGAR XBRL API（免费，User-Agent 需注册邮件）
- **刷新频率**：每季度财报季（1月、4月、7月、10月）全量刷新；其他时间每天增量检查
- **拉取内容**（Phase 1 MVP 最小集）：

| 数据内容 | EDGAR 端点 | 用于章节 |
|---|---|---|
| S&P 500 成分股近两季 EPS（实际 vs 预测）| `/submissions/{cik}.json` + XBRL facts | §4 |
| 季度财报 beat/miss 统计（S&P 500 前 50 市值）| 聚合计算 | §4 |
| 最新一季净利润率（按 GICS 板块分组）| XBRL `NetIncomeLoss` | §4 |

> 🟡 **替代方案**：EDGAR 解析工程量较大。Phase 1 可考虑使用 Financial Modeling Prep（FMP）免费层（每日 250 次请求，含 earnings calendar 和 beat/miss 数据），以降低实现复杂度。建议技术负责人评估。

### 4.4 板块 ETF 相对表现（补充数据源）

- **接入方式**：yfinance Python 库（免费，无需 API Key）
- **拉取内容**：SPDR 11 个板块 ETF（XLK, XLF, XLE, XLV, XLI, XLY, XLP, XLB, XLRE, XLC, XLU）近 20 个交易日的日收益率，计算相对 SPY 的超额收益
- **刷新频率**：每个交易日收盘后

---

## 5. 技术架构规格（Tech Spec）

### 5.1 系统上下文

本功能作为 `macro-report` 服务的**定时脚本**实现，完全复用现有基础设施：

```
每周五 HKT 18:00
        │
EventBridge Rule: macro-report-dev-weekly_macro_report
        │
        ▼
Lambda script_dispatcher
        │  (获取 lease，传 run_id)
        ▼
ECS Fargate Task: macro-report-dev-jobs
  python run_script.py weekly_macro_report
        │
        ├── DataIngestionStep
        │   ├── FredDataTool（拉取 FRED 序列）
        │   ├── UnusualWhalesTool（拉取期权数据）
        │   └── EdgarTool / FmpTool（拉取财报数据）
        │
        ├── MacroAnalystAgent（LangGraph node）
        ├── SectorRotationAgent（LangGraph node）
        ├── OptionsFlowAgent（LangGraph node）
        ├── WriterAgent（LangGraph node）
        └── CriticAgent（LangGraph node）
                │
                ▼
        macro_report_weekly 表（PostgreSQL）
                │
                ▼
        FastAPI /api/v1/reports → Web 页面渲染
```

### 5.2 数据库 Schema（新增表）

**`macro_report_weekly`**（周报存储表）

```sql
CREATE TABLE macro_report_weekly (
    id              bigserial PRIMARY KEY,
    report_week     date NOT NULL,           -- 报告对应周（周一日期）
    status          varchar(16) NOT NULL     -- draft / published / failed
                    DEFAULT 'draft',
    title           text NOT NULL,
    content_md      text,                    -- Markdown 全文
    data_sources    jsonb,                   -- 数据来源结构化记录
    quality_checks  jsonb,                   -- Critic Agent 检查结果
    generated_at    timestamptz,
    published_at    timestamptz,
    create_time     timestamptz DEFAULT now(),
    update_time     timestamptz DEFAULT now(),
    CONSTRAINT uq_report_week UNIQUE (report_week)
);
```

**`macro_data_snapshot`**（采集数据快照，供报告生成和溯源）

```sql
CREATE TABLE macro_data_snapshot (
    id              bigserial PRIMARY KEY,
    source          varchar(32) NOT NULL,    -- fred / unusual_whales / edgar / yfinance
    series_id       varchar(128) NOT NULL,   -- FRED 序列 ID 或端点标识
    series_name     text,
    snapshot_date   date NOT NULL,
    data_json       jsonb NOT NULL,          -- 原始数据（最新值 + 近 N 期历史）
    latest_value    numeric,                 -- 快速查询用
    latest_data_time timestamptz,            -- 数据本身的时间戳（非采集时间）
    fetched_at      timestamptz DEFAULT now(),
    CONSTRAINT uq_source_series_date UNIQUE (source, series_id, snapshot_date)
);
```

> 🔴 **需对齐**：`macro_data_snapshot` 的 `data_json` 字段保存多少期历史？建议：FRED 月度序列保存近 24 期，日度序列保存近 60 个交易日。数据量约 5–10 MB/周，PostgreSQL 完全可承载，无需向量数据库。确认是否认可。

### 5.3 智能体框架选型

🔴 **核心决策：LangGraph vs 简化顺序管道**

| 方案 | 优点 | 缺点 | 推荐场景 |
|---|---|---|---|
| **方案 A：LangGraph 有向图** | 支持条件分支（如数据缺失时降级）、节点可独立重试、与 Phase 2 多 Agent 扩展一致 | 引入新依赖（langchain 生态），调试复杂度高 | 长期首选 |
| **方案 B：顺序脚本（简单 for loop）** | 实现最快（1 周可完成），无额外依赖，易于调试 | 无分支/重试，Phase 2 重构成本高 | MVP 快速验证 |

**技术负责人建议填写**：
- [ ] 选择方案 A（LangGraph）
- [ ] 选择方案 B（顺序脚本），Phase 2 重构

> **产品建议**：Phase 1 内测 20 用户，时间压力大，建议优先选方案 B；Phase 2 再迁移至 LangGraph。方案 B 也完全符合 macro-report 现有的 `scripts/` 脚本范式。

### 5.4 LLM 接入方式

遵循 `docs/llm-call-convention.md`，所有 LLM 调用通过 `llm_configs` + `prompt_bundle` 统一管理。

Phase 1 需新建以下 `prompt_bundle`（在数据库中配置）：

| Bundle Code | 用途 | 输入 | 输出格式 |
|---|---|---|---|
| `macro_fed_analysis` | 美联储政策章节分析 | FRED 数据 JSON + 经济日历 | Markdown 段落 + 数据引用列表 |
| `macro_cycle_analysis` | 经济周期定位 | FRED 宏观指标 JSON | Markdown 段落 + 周期阶段标签 |
| `macro_yield_curve` | 收益率曲线章节 | FRED 利差数据 | Markdown 段落 |
| `macro_earnings_cycle` | 企业盈利周期 | EDGAR/FMP 财报数据 | Markdown 段落 |
| `macro_sector_rotation` | 板块轮动信号 | ETF 流向 + 周期阶段 | Markdown 段落 + 板块评级表 |
| `macro_options_sentiment` | 期权市场情绪 | Unusual Whales 数据 | Markdown 段落 |
| `macro_risk_factors` | 风险因素章节 | 综合输入（上述所有） | Markdown 段落（Top 3 风险） |
| `macro_executive_summary` | 执行摘要 | 七章节草稿 | 200 字以内 Markdown |
| `macro_critic_check` | Critic 质量校验 | 完整报告草稿 + 数据来源 | JSON（质量检查结果） |

> 🔴 **需对齐**：`llm_configs` 中使用哪个模型？推荐 Claude Sonnet 4.6（本项目已在用）。是否需要为宏观分析配置独立的 `llm_configs` 记录（不同 temperature、context window）？

### 5.5 新增脚本

**`app/scripts/weekly_macro_report.py`**

```
功能：驱动整个报告生成流程
调用链：数据采集 → 各章节 LLM 分析 → Writer 整合 → Critic 校验 → 写库
预计运行时间：10–20 分钟
ECS 配置：同 macro-report-dev-jobs，256 CPU / 512 MiB（可能需升至 512/1024）
```

**`app/scripts/refresh_macro_data.py`**

```
功能：独立的数据采集脚本（每日 UTC 14:00 刷新 macro_data_snapshot 表）
与报告生成解耦：报告生成时直接读库，不临时拉 API
预计运行时间：2–5 分钟
```

> **设计原则**：数据采集与报告生成分离——`refresh_macro_data` 每天跑，保证数据库始终有最新快照；`weekly_macro_report` 每周跑，直接读快照生成报告，不依赖实时 API。这样报告生成即使失败重跑也不重复消耗 API 配额。

### 5.6 新增 API 端点

遵循 `AGENTS.md` 约定，以下端点变更需同步更新 `docs/api.md`（CI 强制）：

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `GET` | `/api/v1/reports` | Bearer | 报告列表（分页，默认返回最新 10 期） |
| `GET` | `/api/v1/reports/latest` | Bearer | 最新一期已发布报告 |
| `GET` | `/api/v1/reports/{id}` | Bearer | 指定报告详情（含 Markdown 全文） |
| `GET` | `/api/v1/reports/{id}/sources` | Bearer | 指定报告的数据来源明细 |
| `POST` | `/api/v1/reports/generate` | Admin | 立即触发一次报告生成（管理员） |

### 5.7 新增 Web 页面路由

| 路径 | 页面 | 说明 |
|---|---|---|
| `/reports` | 报告列表页 | 显示最近 10 期，状态徽标（published/draft/failed） |
| `/reports/latest` | 最新报告页 | 渲染 Markdown，侧边栏显示数据来源 |
| `/reports/{id}` | 指定报告页 | 同上 |

---

## 6. 非功能性需求

### 6.1 性能

| 指标 | 要求 | 备注 |
|---|---|---|
| 报告生成端到端时间 | ≤ 20 分钟 | 含数据读取 + 9 次 LLM 调用 + Critic |
| 报告页加载时间 | ≤ 2 秒 | 静态 Markdown 渲染，无向量检索 |
| 数据刷新延迟 | FRED 数据：发布后 24 小时内入库 | FRED 发布时间不固定，每日 UTC 14:00 拉取即可 |

### 6.2 可靠性

| 场景 | 处理方式 |
|---|---|
| FRED API 超时/限速 | 指数退避重试 3 次；失败则跳过该序列并在报告中注明"数据暂不可用" |
| Unusual Whales API 不可用 | 降级：§6 期权章节使用 FRED `VIXCLS` 占位，注明"完整期权数据暂不可用" |
| LLM 调用失败 | 某章节失败则整份报告标记为 `failed`；保存已完成章节供调试 |
| 脚本超时（ECS 2h 限制） | 将 9 个 LLM 调用拆分为可断点续跑的步骤，中间结果写临时表 |
| DynamoDB lease 机制 | 复用现有 `script_lease`，防止并发重复生成 |

### 6.3 可观测性

- CloudWatch Logs：所有 LLM 调用记录 `bundle_code`、`llm_config_id`、`model`、`duration_ms`、`input_tokens`、`output_tokens`（不记录完整 prompt/response）
- CloudWatch Alarm：报告生成失败（`status=failed`）时触发 SNS 通知
- 管理员页面（`/admin/scripts`）：显示最近 10 次 `weekly_macro_report` 任务状态和日志链接

### 6.4 合规与免责

- 每份报告底部必须包含固定免责声明：
  > "本报告由 AI 自动生成，仅供参考，不构成任何投资建议或要约。数据来源均已注明，读者应自行核实。MacroReport 不承担因使用本报告信息所产生的任何损失。"
- 报告中**禁止**出现具体的"买入/卖出/持有"建议措辞
- 报告中所有数值必须可追溯至 `macro_data_snapshot` 表中的原始 API 响应

---

## 7. 数据库迁移

Phase 1 需新增两张表，对应迁移文件：

| 编号 | 文件名 | 内容 |
|---|---|---|
| `000002` | `000002_create_macro_report_weekly.sql` | `macro_report_weekly` 表 |
| `000003` | `000003_create_macro_data_snapshot.sql` | `macro_data_snapshot` 表 + 索引 |

> 迁移编号从 `000002` 开始（`000001_init_macro_report_schema.sql` 已建 `app_user` / `auth_token`）

---

## 8. 验收标准（Definition of Done）

Phase 1 整体 DoD：以下所有条目必须全部通过，才视为 Phase 1 完成。

### 8.1 功能验收

- [ ] `refresh_macro_data` 脚本可在 dev 环境成功拉取所有 FRED 序列并写入 `macro_data_snapshot`
- [ ] `weekly_macro_report` 脚本可端到端生成包含七个章节的报告，状态为 `published`
- [ ] 报告中每个数值均可在 `macro_data_snapshot` 中找到对应原始数据
- [ ] Critic Agent 检查结果存入 `quality_checks` 字段，且所有质量门禁通过
- [ ] Web 页面 `/reports/latest` 可正常渲染报告 Markdown（含数据来源侧边栏）
- [ ] 管理员可通过 `POST /api/v1/reports/generate` 手动触发并在 `/admin/scripts` 查看状态
- [ ] EventBridge 规则已在 dev 配置，每周五 HKT 18:00 触发（`schedules.yaml` 中添加 `weekly_macro_report`）
- [ ] 所有新增端点已更新至 `docs/api.md`（CI 检查通过）

### 8.2 质量验收（内测前必须通过）

- [ ] 对最近 4 期报告进行人工抽查，幻觉率（数值错误/虚构数据）< 5%
- [ ] 每份报告中的 FRED 数据点与 FRED 官网数值比对，误差 = 0
- [ ] 报告生成 P95 时间 ≤ 20 分钟（5 次测试）
- [ ] 免责声明完整出现在每份报告底部

### 8.3 运维验收

- [ ] 生成失败时 CloudWatch Alarm 触发 SNS 通知（测试验证）
- [ ] `macro_data_snapshot` 表在 dev 至少有 5 天的数据积累
- [ ] 脚本已通过 `app/schedules.yaml` 注册，`tofu validate -backend=false` 通过

---

## 9. 里程碑与时间节点

| 里程碑 | 目标日期 | 交付物 | 负责人 |
|---|---|---|---|
| **M1：数据管道就绪** | 2026-09-10 | FRED + yfinance 数据采集脚本，`macro_data_snapshot` 表稳定运行 | TBD |
| **M2：报告框架可用** | 2026-09-30 | `weekly_macro_report` 脚本可生成完整七章节报告（允许 AI 质量不完美） | TBD |
| **M3：幻觉率达标** | 2026-10-20 | Critic Agent 质量门禁通过，人工抽查幻觉率 < 5% | TBD |
| **M4：Web 页面上线** | 2026-11-05 | 报告列表页 + 报告详情页在 dev 可访问 | TBD |
| **M5：内测发布** | 2026-11-20 | 20 名内测用户可正常使用，问题修复周期 ≤ 3 天 | TBD |

> 🔴 **需对齐**：各里程碑负责人待确认；如有资源冲突需在对齐会议上调整节点。

---

## 10. 待确认事项汇总

以下问题需在对齐会议中确认（🔴）或会后 3 个工作日内异步确认（🟡）：

| # | 问题 | 类型 | 当前默认假设 |
|---|---|---|---|
| Q1 | Unusual Whales API 订阅是否批准？（约 $79–$199/月）| 🔴 产品/财务 | 若不批准，Phase 1 用 FRED VIXCLS + yfinance 期权数据替代 |
| Q2 | ISM PMI 数据：是否接受用文字描述替代实时数值？ | 🔴 产品 | 是：Phase 1 用"最近公布值为 XX（日期）"文字引用 |
| Q3 | EDGAR vs FMP：财报数据用哪个源？ | 🔴 技术 | 推荐 FMP 免费层（更低实现复杂度） |
| Q4 | 智能体框架：LangGraph vs 顺序脚本？ | 🔴 技术 | 推荐顺序脚本（Phase 1 快速交付） |
| Q5 | LLM 模型：宏观分析用 Claude Sonnet 还是 Opus？ | 🔴 技术/财务 | Sonnet（成本低 5–10 倍，质量足够） |
| Q6 | `macro_data_snapshot` 历史保留多少期？ | 🟡 技术 | FRED 月度 24 期，日度 60 交易日 |
| Q7 | 报告生成 ECS 规格：256/512 是否足够？ | 🟡 技术 | 如 LLM 调用并行则需升至 512/1024 |
| Q8 | 内测用户 20 名：如何招募、如何收集反馈？ | 🟡 产品 | 目前无规划，需产品侧主导 |
| Q9 | 报告对外可见性：内测期间是否仅 `is_admin=true` 用户可见？ | 🟡 产品 | 是：内测阶段所有注册用户均可查看，admin 才能手动触发 |

---

## 附录 A：FRED API 快速参考

```bash
# 申请免费 API Key：https://fred.stlouisfed.org/docs/api/api_key.html
# 获取序列最新值示例：
curl "https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key=YOUR_KEY&limit=1&sort_order=desc&file_type=json"
```

## 附录 B：相关文档索引

| 文档 | 路径 |
|---|---|
| 商业计划书 | `docs/business_plan.md` |
| 服务总览 | `AGENTS.md` |
| LLM 调用规范 | `docs/llm-call-convention.md` |
| 管理员角色 | `docs/admin_roles.md` |
| API 文档（待更新）| `docs/api.md` |
| 调度权威源 | `app/schedules.yaml` |
