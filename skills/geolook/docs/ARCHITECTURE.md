# GeoLook 系统说明文档

> 适用代码版本：`d:\geolook-main`
> 适用读者：二次开发者 / 集成方 / 接手运维的人
> 文档目的：讲清「这套系统在干什么、为什么这样设计、关键流程怎么走、数据怎么流转」

---

## 目录

1. [项目定位与核心判断](#1-项目定位与核心判断)
2. [核心理念与设计纪律](#2-核心理念与设计纪律)
3. [系统架构总览](#3-系统架构总览)
4. [端到端流水线（9 步）](#4-端到端流水线9-步)
5. [模块职责详解](#5-模块职责详解)
6. [数据流与项目目录结构](#6-数据流与项目目录结构)
7. [评分体系：六维体检](#7-评分体系六维体检)
8. [AI 答案采样：跨市场双轨](#8-ai-答案采样跨市场双轨)
9. [工单系统：执行状态单一真相源](#9-工单系统执行状态单一真相源)
10. [验收闭环：自动判定与回归检测](#10-验收闭环自动判定与回归检测)
11. [资产与内容大纲：结构与人写的分工](#11-资产与内容大纲结构与人写的分工)
12. [大盘对照：CN-GEO 187,818 条引用实算榜](#12-大盘对照cn-geo-187818-条引用实算榜)
13. [报告与三份交付物](#13-报告与三份交付物)
14. [看板：单页前端 + 标库 HTTP 服务](#14-看板单页前端--标库-http-服务)
15. [后台任务系统](#15-后台任务系统)
16. [关键设计取舍](#16-关键设计取舍)
17. [约束、边界与已知限制](#17-约束边界与已知限制)
18. [扩展指南：接一个新平台 / 新检查器](#18-扩展指南接一个新平台--新检查器)

---

## 1. 项目定位与核心判断

GeoLook（GitHub: `bingqiang2021/geolook`）是一个**自托管的全流程 GEO 实施平台**。GEO = Generative Engine Optimization（生成式引擎优化）：让 DeepSeek、豆包、ChatGPT、Perplexity 等 AI 引擎在回答用户问题时**主动提到并引用你的品牌**。

**它不是**：

- 传统 SEO 工具（不查关键词排名、不做外链）
- GEO 监测 SaaS（不是只告诉你提及率然后收订阅费）
- 黑盒 AI 平台（所有指标口径在代码里可查）

**它是**：从「给一个官网」到「客户能签收的交付包」的全流程脚本 + 一个可观测看板。

### 一句话核心判断

> GEO 的终点不是排名，是 **AI 答案里那句话是不是按你的口径说的**。
> 最小单位不是页面，是 **可被抽取的事实块**。

这一判断决定了系统几乎所有设计的走向：把站点拆成可量化的「抽取块」来打，把答案拆成「提及/位次/引用」来测，把交付拆成「能自动验收的工单」来闭环。

---

## 2. 核心理念与设计纪律

代码里反复出现的几条原则，记住它们能少走很多弯路：

| 原则 | 体现位置 | 含义 |
|---|---|---|
| **官网只占 1.37%** | `references/cn-source-ranking.md`、报告里的提醒 | 官网是事实源不是引用源；高 ROI 的动作是外部信源，不是把官网再优化 |
| **不编数** | `report.pct()`、`audit.run()` 里的 `None` 处理 | 算不出的指标显示「未测」，不允许默认 0、不允许凑数 |
| **点名品牌的题不算可见性** | `sample.brand_in_question()`、`aggregate()` | 「X 是家什么公司」答案必然复述品牌名，混进 mention_rate 是假阳性 |
| **API ≠ 网页端** | `sample.MANUAL_ONLY` | 千问 web 与 App 信源只有 24.5% 重合，必须分端记录分端算 |
| **国内 ≠ 海外** | `sample.questions_for()`、`report` 里的市场分组 | 跨市场平均提及率没有解释力，报告里各占一张表 |
| **每条建议都能追到 method.md** | `tasks.from_*()` 里的 why 字段 | 写方案、写工单都带数据出处 |
| **编造防线** | `bootstrap`、`generate.lint_draft()` | 抽不到就标「待确认」、占位名直接挡、初稿必须过风险检查 |
| **不绕过平台限制** | `sample.PROVIDERS` 不含任何需登录 / 破解的端点 | 不批量滥采、不模拟登录 |
| **数据归属你** | `.gitignore` 含 `.env` 与 `work/` | 单机存 JSON/Markdown，`git pull` 不丢数据 |
| **验收即产品** | `verify.check()` | 能自动判定的绝不靠人回填；回归了自动打回 todo |

---

## 3. 系统架构总览

GeoLook 由三层组成：

```
┌─────────────────────────────────────────────────────────────┐
│  表现层：scripts/ui.html（单页 SPA，零外部依赖）            │
│  └── 4 段主线：现状 → 诊断 → 提升 → 成效                   │
├─────────────────────────────────────────────────────────────┤
│  服务层：scripts/dashboard.py（标准库 http.server, 8765）  │
│  ├── REST API（/api/projects、/api/project/<slug>、…）      │
│  ├── 静态文件服务（ui.html、assets）                        │
│  └── 任务代理：把动作交给 jobs.py 起子进程                  │
├─────────────────────────────────────────────────────────────┤
│  业务层：scripts/geo.py + 10 个模块                         │
│  ├── init → crawl → audit → sample → bootstrap              │
│  ├── tasks（工单）→ generate（资产）→ verify（验收）         │
│  ├── blueprint / benchmark（信源规划）                      │
│  ├── report / deliverables / deliver（报告与交付）          │
│  └── geolib.py（共用工具）                                  │
├─────────────────────────────────────────────────────────────┤
│  数据层：work/<slug>/  纯 JSON + Markdown + 原始 HTML       │
│  └── geo.json、audit.json、tasks.json、metrics/、samples/…  │
└─────────────────────────────────────────────────────────────┘
```

技术栈：

- **Python 3.9+**（已修：Windows 兼容，`fcntl` 改为可选 import）
- **3 个第三方依赖**：`requests`、`beautifulsoup4`、`lxml`
- **零前端依赖**：`ui.html` 是单文件原生 HTML + vanilla JS，断网可用
- **零数据库**：`http.server` 起服务，数据在 JSON / Markdown 文件里

---

## 4. 端到端流水线（9 步）

入口是 `scripts/geo.py`，提供两条全自动路径：

- `geo.py new --url <网址>`：建项目 + 9 步全自动
- `geo.py serve --slug <项目>`：对已建项目跑完整一期
- `geo.py cycle --slug <项目>`：轻量循环（抓取→体检→采样→报告，不含工单与交付）

9 步全流程在 [geo.py cmd_new](file:///d:/geolook-main/scripts/geo.py#L106-L161)：

```
1. 建项目（init）
   └─ 写 geo.json，建 work/<slug>/ 子目录
        ↓
2. 抓取官网（crawl）
   └─ evidence/site.json + pages.jsonl + 原始 HTML 快照
        ↓
3. 体检（audit）
   └─ audit.json（六维打分、问题码、缺口统计）
        ↓
4. 自动推导底座（bootstrap）★可跳过
   └─ 从正文 + LLM 推品牌事实 / 竞品 / 问题库
   └─ 写 content/facts.md
        ↓
5. 重跑体检
   └─ 有了问题库才能算对题性维度
        ↓
6. AI 答案采样（sample）
   └─ samples/<日期>.jsonl + metrics/<日期>.json
        ↓
7. 工单与建设蓝图（plan + blueprint）
   └─ tasks.json + blueprint.json
        ↓
8. 资产生成 + 报告（generate + report）
   └─ assets/（llms.txt、JSON-LD、片段、大纲、可选 draft）
   └─ reports/<日期>/report.md + report.html
        ↓
9. 三份交付物 + 验收 + 打包（deliverables + verify + deliver）
   └─ deliverables/1-诊断.html, 2-优化.html, 3-执行.html
   └─ verify/<时间>.json
   └─ delivery/<日期>/（可发客户）
```

每一步都是**幂等**的（重跑不会破坏已有状态，tasks.json 还会保留旧工单的状态与证据）。

---

## 5. 模块职责详解

[scripts/](file:///d:/geolook-main/scripts/) 下每个文件单一职责：

| 模块 | 职责 | 关键产物 |
|---|---|---|
| [geo.py](file:///d:/geolook-main/scripts/geo.py) | CLI 入口，argparse 路由到各 cmd_* | — |
| [geolib.py](file:///d:/geolook-main/scripts/geolib.py) | 共用工具：路径、配置、HTTP、HTML 解析、文本统计 | `load_env`、`project_lock`、`fetch`、`parse_html`、`cjk_ratio`、`page_language`、`word_count` |
| [crawl.py](file:///d:/geolook-main/scripts/crawl.py) | 抓取 + robots/sitemap/llms.txt + AI 抓取器封禁检测 | `evidence/site.json`、`evidence/pages.jsonl` |
| [audit.py](file:///d:/geolook-main/scripts/audit.py) | 六维打分 + 站点级问题 + 语言覆盖 + block_gap | `audit.json` |
| [sample.py](file:///d:/geolook-main/scripts/sample.py) | 13 个 API 平台 + 5 个人工平台 + 答案解析 | `samples/<日期>.jsonl`、`metrics/<日期>.json` |
| [bootstrap.py](file:///d:/geolook-main/scripts/bootstrap.py) | 从正文 + LLM 推底座，**带编造防线** | `geo.json`（补全）、`content/facts.md` |
| [tasks.py](file:///d:/geolook-main/scripts/tasks.py) | 工单生成、状态管理、单条更新 | `tasks.json` |
| [generate.py](file:///d:/geolook-main/scripts/generate.py) | 结构性资产 + 内容大纲 + LLM 初稿 + lint | `assets/llms.txt`、`assets/jsonld/*.json`、`assets/snippets/*.html`、`assets/outlines/*.md`、`assets/drafts/*.md` |
| [verify.py](file:///d:/geolook-main/scripts/verify.py) | 重抓 + 跑 checker + 回写状态 + 回归检测 | `verify/<时间>.json` |
| [report.py](file:///d:/geolook-main/scripts/report.py) | 报告渲染（MD + 自包含 HTML） + delta + 大盘对照 | `reports/<日期>/report.md`、`reports/latest.md` |
| [benchmark.py](file:///d:/geolook-main/scripts/benchmark.py) | 与 CN-GEO 187,818 条引用榜对照 | （被 report / tasks 调用） |
| [blueprint.py](file:///d:/geolook-main/scripts/blueprint.py) | 阵地建设地图：19 个阵地 × 怎么建 | `blueprint.json` |
| [deliverables.py](file:///d:/geolook-main/scripts/deliverables.py) | 三份正式交付物（诊断 / 优化 / 执行） | `deliverables/1-GEO诊断报告.html` 等 |
| [deliver.py](file:///d:/geolook-main/scripts/deliver.py) | 客户交付包打包 | `delivery/<日期>/` |
| [publish.py](file:///d:/geolook-main/scripts/publish.py) | 手动触发，凭证在 `.env` | — |
| [dashboard.py](file:///d:/geolook-main/scripts/dashboard.py) | 看板后端：REST + 任务代理 | http://127.0.0.1:8765 |
| [jobs.py](file:///d:/geolook-main/scripts/jobs.py) | 子进程任务：白名单动作、并发保护、日志、孤儿回收 | `.jobs/<id>.json` + `<id>.log` |
| [analytics.py](file:///d:/geolook-main/scripts/analytics.py) | 看板用：跨期趋势、引擎表现分布等 | （被 dashboard 调用） |
| [ui.html](file:///d:/geolook-main/scripts/ui.html) | 单页前端，4 段主线（现状/诊断/提升/成效） | — |

---

## 6. 数据流与项目目录结构

每个客户/产品一个 `work/<slug>/`，gitignore 但建议本地多机同步。

```
work/<slug>/
├── geo.json                  ★ 品牌底座（brand/competitors/questions/platforms/targets）
├── content/
│   └── facts.md              品牌事实卡（所有资产的输入源）
├── evidence/                 crawl 产物
│   ├── site.json             站点级（robots / sitemap / llms.txt / AI 抓取器封禁）
│   ├── pages.jsonl           每页一条（含正文、JSON-LD、字数、文本统计）
│   └── html/<n>.html         原始 HTML 快照（人工复核用）
├── audit.json                ★ 体检结果（六维分、问题码、block_gap）
├── samples/<日期>.jsonl      每次采样的原始记录
├── metrics/<日期>.json       每期聚合指标（提及率、位次、引用份额）
├── tasks.json                ★ 工单系统（执行状态单一真相源）
├── blueprint.json            建设地图：19 阵地 × 建什么/建多少/节奏
├── assets/                   可部署资产
│   ├── llms.txt / llms.en.txt
│   ├── jsonld/*.json
│   ├── snippets/definition.<lang>.html
│   ├── snippets/faq.<lang>.html
│   ├── outlines/<q_id>.md
│   └── drafts/<q_id>.md     （--draft 才有）
├── reports/<日期>/report.{md,html}    + latest.md
├── verify/<时间>.json        每次验收快照
├── deliverables/             三份正式交付物
│   ├── 1-GEO诊断报告.html
│   ├── 2-GEO优化方案.html
│   └── 3-GEO执行方案.html
├── delivery/<日期>/          客户可签收的完整交付包
├── history/                  历史基线（算 delta）
└── .geo.bak/                 写配置前的自动备份（保留最近 10 份）
```

### 数据流向（一张图）

```
                          ┌──────────────┐
                          │  geo.json    │  ← 人工 + bootstrap
                          └──────┬───────┘
                                 │
       ┌─────────────────┬───────┴───────┬─────────────────┐
       ▼                 ▼               ▼                 ▼
   ┌────────┐       ┌──────────┐    ┌──────────┐     ┌──────────┐
   │ crawl  │──────▶│ evidence │    │ content/ │     │ LLM API  │
   │ 抓取   │       └────┬─────┘    │ facts.md │     │ (可选)   │
   └────────┘            │          └────┬─────┘     └────┬─────┘
                         ▼               │                │
                    ┌─────────┐          │                │
                    │ audit   │          │                │
                    │ 六维打分│          │                │
                    └────┬────┘          │                │
                         │               │                │
                         ▼               ▼                ▼
                    ┌─────────┐    ┌──────────┐     ┌──────────┐
                    │ audit   │    │ generate │     │ sample   │
                    │  .json  │    │ 资产/大纲│     │ 平台采样 │
                    └────┬────┘    └────┬─────┘     └────┬─────┘
                         │              │                │
                         └──────┬───────┘                │
                                ▼                        ▼
                           ┌──────────┐            ┌──────────┐
                           │ tasks    │◀───────────│ metrics  │
                           │ 工单     │            │  指标    │
                           └────┬─────┘            └──────────┘
                                │
                                ▼
                          ┌──────────┐    ┌──────────┐    ┌──────────┐
                          │ verify   │───▶│ report   │───▶│ deliver  │
                          │ 验收闭环 │    │ 报告     │    │ 客户包   │
                          └──────────┘    └──────────┘    └──────────┘
```

**关键不变量**：

1. `geo.json` 和 `tasks.json` 是**唯一会被人工反复修改的文件**，写前自动备份
2. `evidence/`、`audit.json`、`samples/`、`metrics/` 都是**从原始数据可重算**的，可以放心清空重跑
3. `assets/` 内的 `outlines/drafts` 是**给人 / 给 LLM 接着写**的，不被任何代码反向改

---

## 7. 评分体系：六维体检

[audit.py](file:///d:/geolook-main/scripts/audit.py) 是 `references/method.md` 的代码实现。每个数字都有出处，不是拍脑袋。

### 六维与权重

| 维度 | 满分 | 锚定的实证数字 |
|---|---:|---|
| 可抓取性 | 15 | 抓不到 = 不存在；SPA 空壳是 P0 |
| 内容长度 | 15 | Top 1/4 页 1,943 词 vs Bottom 1/4 页 170 词（11.4×） |
| 结构规范 | 20 | Top 页 10.59 标题、47.49 段落、列表密度 0.428 |
| **可抽取块** | **25** | **GEO 核心杠杆**：含数字 +61.6%、定义 +57.3%、对比 +55.3%、how-to +41.2% |
| 权威信号 | 15 | 日期/作者/外链/JSON-LD |
| 对题性 | 10 | **最强预测因子 r=0.432**——标题体系必须含问题原词 |

总分 100。评级：A≥80 / B≥65 / C≥45 / D

### 抽取块识别（核心算法）

`audit.py` 用一组**保守的正则**识别 5 类块（每条都带 P1 缺块提示）：

```python
RE_DEFINITION = r"(是一[款种个家类]|是指|指的是|全称[为是]|is an? \w+|refers to|is defined as)"
RE_NUMBER     = r"\d[\d,\.]*\s*(%|％|万|亿|倍|元|美元|人|家|个|天|小时|...)"
RE_COMPARE    = r"(对比|相比|区别|差异|优于|不如|竞品|替代|vs\.|versus|alternatives?)"
RE_HOWTO      = r"(第[一二...步]|步骤\s*[1-9]|操作流程|step\s*\d|how to)"
RE_HOWTO_SOFT = r"(如何|怎么)"   # 弱信号，必须与列表结构共现才算
RE_FAQ        = r"(常见问题|问答|FAQ|^\s*[问Q][:：]|答[:：])"
```

> **纪律**：正则故意保守——「如何 / 怎么」必须与列表结构共现才算操作步骤块，否则问句标题就送分。
> **防 SPA 误报**：`FUNC_PAGE` 排除登录/注册/购物车等功能页。

### 语言覆盖与海外市场门票

`audit.run()` 在市场为 `global` 或 `both` 时，如果抓到的页面里没有任何英文原生内容页，会直接产出一条**站点级 P0**：

> 海外 AI 引用的可识别语言里英文占 82.90%–95.07%，机翻页进不了候选池

### block_gap

聚合全站「缺哪类块」的页面数，排序后就是内容工程第一优先清单。

---

## 8. AI 答案采样：跨市场双轨

[sample.py](file:///d:/geolook-main/scripts/sample.py) 是系统里**最复杂**的模块，因为要处理 10+ 个平台的不同 API 协议、引用字段、降级策略。

### 平台矩阵

**国内**（market=cn）：
| 平台 code | 协议 | 联网 | 备注 |
|---|---|---|---|
| `glm`（智谱GLM） | OpenAI 兼容 | ✗ | `ZHIPUAI_API_KEY` |
| `doubao`（豆包） | 火山方舟 | ✓ | 优先 Responses+web_search；没开内容插件自动降级为普通对话 |
| `deepseek` | OpenAI 兼容 | ✗ | 测模型参数化知识里的品牌认知 |
| `kimi` | OpenAI 兼容 | ✗ | `MOONSHOT_API_KEY` |
| `minimax`（MiniMax） | OpenAI 兼容 | ✗ | `MINIMAX_API_KEY` |
| `nano_ai` | 人工 | — | `sample-sheet` 导出 |
| `baidu`（百度AI） | 人工 | — | 同上 |

**海外**（market=global）：
| 平台 code | 协议 | 联网 | 备注 |
|---|---|---|---|
| `gemini` | OpenAI 兼容 | ✗ | 不带 grounding |
| `openai` | OpenAI 兼容 | ✗ | Chat Completions 默认不联网 |
| `claude` | Anthropic 原生 | ✗ | 走专用协议；max_tokens=4096；refusal 当错误 |
| `grok` | xAI API | ✗ | `XAI_API_KEY` |
| `perplexity` | Perplexity 原生 | ✓ | **唯一原生联网，海外证据质量最好** |
| `chatgpt` | 人工（网页版） | — | — |
| `claude_web` | 人工（网页版） | — | — |

### 三个关键设计

**1. 协议适配**

不同平台的 API 协议不同，sample.py 用 `protocol` 字段路由：

```python
if p.get("protocol") == "ark":       → ask_ark()      # 火山方舟
if p.get("protocol") == "anthropic": → ask_anthropic()  # 原生 Messages
else:                                → ask()           # OpenAI 兼容
```

引用来源字段也各家不同，合并到统一的 `citations`：

```python
for item in (data.get("search_info") or {}).get("search_results", []): ...
for item in data.get("search_results") or []: ...
for u in data.get("citations") or []: ...
```

**2. 增量落盘 + 平台并发**

```python
fh = path.open("a", encoding="utf-8")  # 中途挂掉不丢已采样本
by_plat = ...  # 按平台分组
ThreadPoolExecutor(max_workers=len(by_plat))  # 平台间并发
# 平台内串行 + time.sleep(0.4) 防止限流
```

**3. 答案解析（核心难点）**

`_entity_hit` / `analyze_answer` 干这件事：

- 实体识别：**跨文种相邻是天然分词边界**，所以拉丁侧加 lookaround 防「AIGC」命中「AIGCLINK」，CJK 侧不查（中文没空格分词）
- 否定语境：「不是 X」里的 X 算否定命中，标 `needs_review` 但**不算提及**
- 疑似负面：品牌命中点前 80 / 后 160 字符窗口内找负面线索词（保守词表，误报会浪费复核时间）
- 引用域名：把 `answer` 里的 URL 与 API 返回的 `citations` 合并，按 `urlparse(...).netloc` 归一

```python
# 关键判定：点名品牌的问题不算可见性
def brand_in_question(question, cfg):
    # 答案必然复述品牌名 → 单独归入"品牌认知"，不混进 mention_rate
```

`aggregate()` 按平台分桶计算指标：

- `mention_rate` / `top1_rate` / `top3_rate` / `avg_rank` / `own_domain_cite_rate` / `competitor_mentions` / `top_cited_domains`
- `probe`（品牌认知）：点名题单独成块

### 增量更新：竞品确认

采样后跑一次 `confirm_competitors()`：被 AI 答案真实提过的竞品 `confirmed` 转正，没被提过的保留 `confirmed: False` 供后续观察。

---

## 9. 工单系统：执行状态单一真相源

[tasks.py](file:///d:/geolook-main/scripts/tasks.py) 把诊断结果变成**可分派、可验收、可追踪**的执行任务。

### 工单结构

每条工单有 8 个必备字段：

```json
{
  "id": "T-001",
  "priority": "P0",
  "package": "页面技术",
  "market": "both",
  "title": "解除 robots.txt 对 AI 抓取器的封禁",
  "why": "robots 封禁了 GPTBot、ClaudeBot…（method.md 可抓取性）",
  "action": "移除对应 Disallow，或改为仅屏蔽后台路径",
  "owner": "开发",
  "effort": "S",
  "window": "30天",
  "affected": ["https://..."],
  "acceptance": {
    "type": "auto",
    "check": "site.no_ai_bot_block",
    "desc": "重抓后 robots 不再整站封禁任何 AI 抓取器"
  },
  "status": "todo",
  "assets": [],
  "evidence": [],
  "closed_at": null
}
```

**纪律**：没有验收标准的不叫工单，叫愿望。

### 七个包与优先级

- 实体消歧 / 页面技术 / 内容矩阵 / 标题体系 / 知识库 / 外部证据 / 监测闭环
- 优先级：**P0 → 30天，P1 → 60天，P2 → 90天**
- 优先级顺序（method.md 第 6 节）：门票问题 → 事实错误 → 抽取块缺口 → 高价值问题无承接 → **外部信源（P1，不是 P2）** → 长尾扩量
- 外部信源是 P1 不是 P2，因为**官网只占全库引用 1.37%**

### 工单生成：四个来源

`build()` 把四类工单拼起来：

1. `entity_tasks(cfg)`：实体消歧 + 品牌事实卡 + 百科词条（永远存在）
2. `from_audit(audit, cfg)`：站点级 + 页面级（按缺口类型聚合，不是按页聚合）
3. `from_metrics(metrics, cfg)`：按市场分（cn / global）的可见性指标工单
4. `from_benchmark(bench, cfg)`：CN-GEO 大盘对照出的高杠杆信源

### 状态机

`todo → doing → done / blocked / wontfix`

- 写状态走 `set_status()`，自动加 `evidence` 时间戳
- `done` 时自动写 `closed_at`
- 回归（`verify` 重新检查不达标）时**自动回退到 `todo`**

### 进度持久化

重跑 `plan` 不会清空已有工单状态：

```python
old = {t["id"]: t for t in (G.read_json(pdir / "tasks.json", {}) or {}).get("tasks", [])}
# 按 id + title 双键匹配，保留 status / evidence / assets / closed_at
```

---

## 10. 验收闭环：自动判定与回归检测

[verify.py](file:///d:/geolook-main/scripts/verify.py) 是「服务」与「建议」的分界线。

### checker DSL

写在工单 `acceptance.check` 里的微型 DSL，13 种检查器：

| 表达式 | 含义 |
|---|---|
| `site.no_ai_bot_block` | robots 不再整站封 AI 抓取器 |
| `site.has_sitemap` / `has_llms_txt` | 站点级资产已上线 |
| `site.avg_score_gte:70` | 重跑 audit 均分达标 |
| `site.en_pages_gte:8` | 英文有效内容页数达标 |
| `site.lang_balance:0.7` | 中英页面数差距在阈值内 |
| `pages.static_text` | 受影响页面正文词数 ≥120（SPA 修复） |
| `pages.has_jsonld` | 受影响页面已挂 JSON-LD |
| `pages.block:定义` | 缺该抽取块的页面数下降 ≥50% |
| `pages.wordcount_gte:1000` | 正文不足 1000 词的页面数下降 ≥40% |
| `metrics.mention_rate_gte:cn:0.3` | 指定市场平均无提示提及率达标 |
| `metrics.own_cite_gte:cn:0.1` | 指定市场引用官网率达标 |
| `external.any:a.com,b.com` | 采样里出现任一目标域名的引用 |

`check()` 返回 `(通过?, 说明, 进度快照)`，进度快照是 before/after 数据源。

### 回归检测

```python
if ok is True and status != "done":   # 之前没完成 → 现在通过
    status = "done"
elif ok is False and status == "done":  # 之前通过 → 现在不达标（回归！）
    status = "todo"
```

### 关键纪律

- **None = 未测**：所有指标字段都用 `is None` 判断，不允许用「0 = 未测」这种约定
- **基线用生成工单时的真实缺口数**：`baseline_count` 字段存的是 `from_audit()` 当时的实际缺口，不受 `affected` 截断影响
- **写 tasks.json 走 project_lock**：Unix 上 fcntl，Windows 上 no-op（见 [geolib.py L91-L106](file:///d:/geolook-main/scripts/geolib.py#L91-L106)）

---

## 11. 资产与内容大纲：结构与人写的分工

[generate.py](file:///d:/geolook-main/scripts/generate.py) 的设计原则：

> **结构性资产由代码确定性生成**（不会漏 schema 字段）；**文章正文由 Claude / LLM 按 outline 写**（代码写不出好文案）。

### 4 类资产

| 资产 | 确定性 | 来源 | 部署位置 |
|---|---|---|---|
| `llms.txt` / `llms.en.txt` | ✓ | facts.md 解析 + 审计页 Top 12 | 网站根目录 |
| `jsonld/*.json` | ✓ | geo.json + facts.md | `<head>` |
| `snippets/definition.<lang>.html` | ✓ | facts.md | 首屏口号下方 |
| `snippets/faq.<lang>.html` | ✓ | questions | FAQ 区块 |
| `outlines/<q_id>.md` | ✓ | questions + facts | — |
| `drafts/<q_id>.md`（`--draft`） | ✗ | LLM API | 人工核实后才能用 |

### 事实卡解析

`parse_facts()` 从 `content/facts.md` 抽出结构化事实：

- 一句话定义（合并多行引用块，去 markdown 标记，去 CJK 间空格）
- 关键数字表（Markdown 表格）
- 适合 / 不适合（项目列表）

### JSON-LD 5 个

`Organization` / `SoftwareApplication` / `FAQPage` / `Article` / `BreadcrumbList`，每个都有占位提示（`<填：…>`），结构不会缺，但具体内容需要人补。

### 内容大纲 4 类模板

按 `questions[].group` 路由到模板：

- `推荐` → 榜单型
- `比较 / 替代` → 对比型
- `价格 / 风险 / 品牌验证` → 定义型
- `场景` → 教程型

每份大纲含：标题候选（**对题性 r=0.432，标题必须含问题原词**）、章节骨架、硬性要求（词数、H2、列表密度、必备抽取块）、可用的已核实事实。

### LLM 初稿 + lint

`draft()` 按大纲调用 LLM 出初稿，写入 `assets/drafts/<q_id>.md`。随后 `lint_draft()` 做三类风险检查：

| 风险等级 | 类型 | 检测 |
|---|---|---|
| 高 | 疑似编造 | 「工具A/某某/XX公司/acme」等占位名 |
| 中 | 未核实数字 | 文中数字不在事实卡且未标「待确认」 |
| 低 | 年份存疑 | 出现非当前年份的「2024 年」之类 |

**关键纪律**：lint 只是辅助，**初稿必须人工核实事实后才能发布**。

---

## 12. 大盘对照：CN-GEO 187,818 条引用实算榜

[benchmark.py](file:///d:/geolook-main/scripts/benchmark.py) 内嵌的 15 个「跨平台通吃」信源 + 5 个「平台生态门槛」信源，数据来自 `references/cn-source-ranking.md` 末尾的复算脚本。

### 用途

报告里回答两个问题：

1. AI 在你这个行业引用的信源，和全国大盘重合吗？
2. 大盘里的高杠杆信源（榜单站、内容平台），你一个都没占的有哪些？

### 三类结论

- `cross_platform_covered` / `cross_platform_missing`：15 个高杠杆信源本期是否占到
- `ecosystem_gaps`：5 个平台生态门槛（baidu / iesdouyin / qq / sm.cn / toutiao）没过
- `high_position_hits`：已占到的且引用位置靠前的（值得加码）

### 类目占比

```python
CATEGORY_SHARE = [
    ("内容平台（qq/toutiao/baidu/iesdouyin）", 0.164, 4),
    ("综合新闻媒体",                          0.136, 68),
    ("商业推荐与榜单站",                      0.091, 28),
    ("品牌官网 / 企业站",                     0.0137, 52),  # ← 1.37%
    ...
]
```

> **官网是事实源不是引用源**——把力气从「官网再优化」转到「外部信源」通常回报更高。

---

## 13. 报告与三份交付物

### 13.1 report.py

生成本期 GEO 报告：MD + 自包含 HTML，与上一期对比出 delta。

- 输入：`audit.json` + `metrics/<最新>.json` + `history/audit-<日期>.json`
- 关键函数：`collect_todos()`（按优先级排好的 P0/P1/P2 待办）、`delta()`（箭头 + 百分点）
- 产物：`reports/<日期>/report.md`、`report.html`、`reports/latest.md`（软链接式副本）

### 13.2 deliverables.py — 三份正式交付物

| 文档 | 回答什么 | 输入 |
|---|---|---|
| **1-GEO 诊断报告** | 现在什么样 | audit + metrics + 大盘对照 |
| **2-GEO 优化方案** | 应该改成什么样，为什么 | audit + 建设蓝图 + 工单摘要 |
| **3-GEO 执行方案** | 谁在什么时候做什么，做到什么算完成 | tasks.json + 工单表 |

### 13.3 deliver.py — 客户可签收的交付包

打包到 `work/<slug>/delivery/<日期>/`：

```
delivery/<日期>/
├── index.html              总览入口
├── 1-诊断报告.html
├── 2-优化方案.html
├── 3-执行方案.html
├── 工单表.html + .csv      可导入项目管理工具
├── 验收表.html
├── assets/                 llms.txt / JSON-LD / 片段
├── 交付说明.md
└── ...（其他派生文件）
```

---

## 14. 看板：单页前端 + 标库 HTTP 服务

[dashboard.py](file:///d:/geolook-main/scripts/dashboard.py) + [ui.html](file:///d:/geolook-main/scripts/ui.html)。

### 服务特点

- **只绑 127.0.0.1**（刻意的安全边界，无认证体系）
- **零外部依赖**：标准库 `http.server` + `ThreadingHTTPServer`
- **REST 路由**（`do_GET` / `do_POST` 内分发）：
  - `GET /api/projects`：所有项目列表
  - `GET /api/project/<slug>`：单项目全量聚合
  - `POST /api/task`：触发任务（白名单动作）
  - `POST /api/tasks/<id>/status`：更新工单状态
  - `GET /api/jobs/<id>/tail?offset=N`：增量日志
- **后端聚合**：把 audit + tasks + verify_history + analytics + facts_struct 一次性打包好，前端只负责展示

### 4 段主线

| 段 | 页面 | 看什么 |
|---|---|---|
| **现状** | 总览 / 引擎表现 / 竞品对比 / 问题库 | 提及率、位次、引用份额、AI 实际在引用谁、样本回放 |
| **诊断** | 差距诊断 / 阵地地图 / 品牌事实库 | 缺口按「先修哪个」排序、19 阵地 × 怎么建、口径核对 |
| **提升** | 行动计划 / 内容工作台 | 工单领单、选题池、右侧可被引用度预检、AI 初稿 lint |
| **成效** | 效果验收 / 报告与交付 | 逐题前后期对比、任务级 before/after、月报、交付包 |

### 总览标题自动生成

`auto_headline()`：由数据自动生成一句结论（如「国内 5 平台平均无提示提及率 24%，目标 30%」），不算就显示「未测」。

---

## 15. 后台任务系统

[jobs.py](file:///d:/geolook-main/scripts/jobs.py) 让看板能触发管线命令并看到实时日志。

### 三个关键设计

**1. 用子进程而不是线程**

子进程隔离最干净——管线里有 requests、文件写入和模块级状态，一个任务崩掉不会拖死整个服务。

```python
proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT,
                        cwd=str(G.ROOT), env=env, start_new_session=True)
```

`start_new_session=True` 让任务脱离主进程组，方便 `killpg(SIGTERM)` 整组杀。

**2. 同一项目同时只允许一个任务**

```python
_running: dict[str, str] = {}  # slug -> job_id
if running_for(slug):
    raise RuntimeError("该项目已有任务在运行…")
```

避免 crawl 和 verify 抢同一份 `audit.json`。

**3. 启动时回收孤儿 job**

```python
def reap_orphans():
    # 上次服务崩溃留下的 status=running 记录，进程已死就回写 interrupted
    # 不回收的话并发保护会永远挡住新项目
```

注意 60ms 内的「刚启动还没落 pid」窗口——`start()` 先落 `running` 再补 `pid`，所以加了 `time.time() - mtime < 60` 的豁免。

### 任务元数据

`/jobs/<id>.json`：

```json
{
  "id": "abc123def456",
  "slug": "example",
  "action": "crawl",
  "label": "抓取站点",
  "status": "running|done|failed|stopped|interrupted",
  "started_at": "...",
  "finished_at": "...",
  "pid": 12345,
  "exit_code": 0,
  "cmd": "geo.py crawl --slug example"
}
```

`/jobs/<id>.log`：实时日志，界面按 `offset` 增量拉取。

---

## 16. 关键设计取舍

把「为什么」写在前面，下次改代码时少踩坑：

| 取舍 | 选了 | 理由 |
|---|---|---|
| 数据库 vs 文件 | **文件** | 单机自托管目标；git 一下就是备份；调试方便；扩到多用户时再换 |
| 框架 vs 标库 | **标库 http.server** | 3 个第三方依赖是设计上限；前端零依赖；断网可用 |
| 子进程 vs 线程 | **子进程** | 隔离干净；状态不互相污染；容易整组杀 |
| Lock 库 | **fcntl（Unix）/ no-op（Windows）** | 单机单人场景够用；多进程并发时再补 msvcrt |
| JSON-LD 库 vs 手写 | **手写** | 5 个固定 schema，手写更可控；占位 `<填>` 强迫人补 |
| 评分算法 | **保守正则** | 误报比漏报代价高（多写一条 P1 不致命；漏报 P0 致命） |
| 「未测」字段 | **None 不默认 0** | 「0% 提及率」和「没采样」是两件事，混在一起会下错结论 |
| 品牌名 | **`name` + `aliases` + `disambiguation` 三层** | AI 容易把同名不同行业的品牌混淆，消歧是地基 |
| 引用源 | **官网 vs 外部** | 1.37% vs 98.63%；外部信源 P1 不是 P2 |
| AI 初稿 | **必须过 lint + 人工核实** | 编造比没内容更糟；不替人做事实判断 |
| .env 权限 | **600** | 含 API Key，谨慎 |
| 工单改状态 | **走 project_lock** | tasks.json 是执行状态单一真相源 |
| 数据备份 | **写 .env / geo.json / tasks.json 前自动备份** | 最近 10 份；恢复比抢救便宜 |
| 平台 API | **只用官方公开端点** | 不绕过平台限制，不批量滥采 |
| 模型选择 | **轻量档**（glm-4-flash、gpt-4o-mini、claude-sonnet） | 测的是「模型认不认识这个品牌」，不是推理质量 |
| 采样并发 | **平台间并发，平台内串行 + 0.4s 延迟** | 推理型 90s/次，串行几十题要 1 小时+；0.4s 防止限流 |
| 增量落盘 | **采样 jsonl 边采边写** | 中途挂掉不丢已采样本 |
| 工单生成 | **聚合到类型级，不一页一条** | 100 个低分页 = 100 条工单？人会被淹死 |
| 验收 | **自动 + 人工二选一** | 能判定的绝不靠人回填；定性的（百科过审）标 manual |
| 回归检测 | **verify 主动回退 done→todo** | 服务不靠人记得「上次好的怎么又坏了」 |
| UI 主题色 | **暗色 4 段主线** | 看板承载信息量大，暗色不刺眼 |

---

## 17. 约束、边界与已知限制

### 不做

- 传统 SEO 关键词排名、外链买卖、竞价投放
- 建站/改站的实际代码实施（给方案、给可直接用的片段，落地由客户开发做）
- 绕过平台限制的批量采集、模拟登录、刷量
- 编造品牌事实、客户案例、价格或资质——**查不到就标「待确认」，问用户**

### 不承诺

任何平台一定会引用某个页面。GEO 提高的是概率，不是保证。给客户写方案时这句话必须原样写进去。

### 已知限制

| 限制 | 影响 | 缓解 |
|---|---|---|
| **Windows 无 fcntl** | project_lock no-op | 单机单人够用；多进程并发需补 msvcrt 实现 |
| **3 个第三方依赖** | 不能加 ORM、模板引擎 | 故意保持轻量；要加就明确收益 |
| **只绑 127.0.0.1** | 远程访问需 SSH 隧道 | 刻意的安全边界 |
| **无账号体系** | 多人协作需自加反向代理 + 认证 | 文档里给了 nginx basic auth 建议 |
| **采样频率与样本量由 API 预算决定** | 频次有限 | 文档建议页面体检每周、采样每两周或每月 |
| **疑似负面是线索不是定性** | 需人工复核 | 故意保守词表，宁可漏报不误报 |
| **品牌名称歧义** | 同名不同行业会被错引 | 强制要求 `disambiguation` 字段 |
| **AI 引擎结果波动** | 同问题不同时间结果可能不同 | `repeat` 参数支持多轮采样取分布 |
| **CJK 语言识别** | 短文本（<80 字符）会 fallback 到 html lang 属性 | 文档化行为 |

### 性能与规模

- 单项目建议 **25–50 页**（默认 25，CLI `--max-pages` 可调）
- 问题库建议 **20–40 题**（按市场分）
- 采样量：13 个平台 × 20 题 × 1 轮 ≈ 260 次 API 调用，按并发约 **15–40 分钟**
- 报告渲染：单页 < 200KB HTML 自包含（含 CSS inline）

---

## 18. 扩展指南：接一个新平台 / 新检查器

### 18.1 接一个新 AI 平台

1. 在 [sample.py](file:///d:/geolook-main/scripts/sample.py) `PROVIDERS` 里加：
   ```python
   "new_platform": {
       "name": "新平台", "market": "cn",  # 或 "global"
       "base": "https://api.example.com/v1",
       "model": os.environ.get("NEW_PLATFORM_MODEL", "model-v1"),
       "model_env": "NEW_PLATFORM_MODEL",
       "key_env": "NEW_PLATFORM_API_KEY",
       "search": False,
       "note": "OpenAI 兼容端点不联网",
   },
   ```
2. 如果协议不是 OpenAI 兼容也不是 anthropic / ark，新增 `ask_xxx()` 函数并修改 `ask()` 路由
3. 引用源字段在 `ask()` 末尾的 `refs = []` 那块加入
4. `available()` / `market_of()` / `label_of()` / `aggregate()` 都会自动适配
5. 在 [jobs.py](file:///d:/geolook-main/scripts/jobs.py) `ACTIONS` 里的 `sample` 已经支持 `--platforms` 透传

### 18.2 接一个新检查器（验收 DSL）

1. 在 [verify.py](file:///d:/geolook-main/scripts/verify.py) `check()` 函数里加一个 `if expr.startswith("your.check:")` 分支
2. 返回 `(bool | None, str, dict | None)` 三元组：
   - `bool`：通过 / 未达标
   - `None`：无法自动判定（走 manual）
   - 第三项是「进度快照」，用于 before/after 进度条
3. 在 [tasks.py](file:///d:/geolook-main/scripts/tasks.py) `from_audit()` 等生成函数里用 `_t(..., {"type": "auto", "check": "your.check:..."})` 生成工单

### 18.3 加一个新评分维度

1. 在 [audit.py](file:///d:/geolook-main/scripts/audit.py) `score_page()` 里加 `d["新维度"] = ...`
2. 加 issue 报告（用 `issue()` 函数收集问题码）
3. 总分 100 需要重平衡，把新维度从其他维度挪权重过来
4. 前端总览的健康分要适配新维度

### 18.4 加一个新交付物

1. 在 [deliverables.py](file:///d:/geolook-main/scripts/deliverables.py) 加新函数，参考 `optimization_plan()` 的结构
2. 在 [deliver.py](file:///d:/geolook-main/scripts/deliver.py) 打包时把新文件复制到 `delivery/<日期>/`
3. 在 [geo.py](file:///d:/geolook-main/scripts/geo.py) `cmd_deliverables()` 里调用新函数

### 18.5 加一个新信源（CN-GEO 榜外）

[benchmark.py](file:///d:/geolook-main/scripts/benchmark.py) 是直接内嵌的，加新信源：

1. 在 `CROSS_PLATFORM` 字典里加（仅当覆盖 11+ 平台端）
2. 在 `ECOSYSTEM` 字典里加（仅当是某平台生态必经之路）
3. 在 `TOP_POSITION` 里加（仅当引用位置进 Top 10）
4. 在 `CATEGORY_SHARE` 里加（仅当类目占比有变化）

加之前先看 `references/cn-source-ranking.md` 末尾的复算脚本，**不要凭印象加**——这是整套方法论的数据底盘。

---

## 附录 A：完整命令速查

| 命令 | 作用 | 何时用 |
|---|---|---|
| `new` | ★ 只给一个网址全自动出三份交付物 | 首次接客户 |
| `serve` | 对已建项目跑完整周期 | 每期复跑 |
| `cycle` | 轻量循环（抓取→体检→采样→报告） | 不想跑工单与交付时 |
| `init` | 只建项目骨架 | 手工配置时 |
| `autopilot` | 对已建项目跑完整引导 | 已有项目要补完整底座 |
| `bootstrap` | 从官网推导品牌事实/竞品/问题库 | LLM 可用时加速首期 |
| `crawl` | 抓站 | 单独刷新数据 |
| `audit` | 六维体检 | 单独打体检分 |
| `sample` | API 平台采样 | 加新 Key 后单独采 |
| `sample-sheet` | 导出人工采样表 | 无 API 平台用 |
| `sample-import` | 导入人工采样表 | 人工采完回灌 |
| `plan` | 诊断 → 带验收标准的工单 | 体检/采样之后 |
| `blueprint` | 建设蓝图：阵地 × 怎么建 | 资源取舍时 |
| `generate` | 产出可部署资产 | 改完页面后刷资产 |
| `lint` | 检查 AI 初稿的编造风险 | 交付前 |
| `verify` | 重抓并自动验收工单 | 下期开始时 |
| `report` | 报告（MD + HTML） | 每期必出 |
| `deliverables` | 三份正式交付物 | 给客户前 |
| `deliver` | 客户交付包 | 上面三份出完 |
| `publish` | 把成稿/资产发布到已配置渠道 | 永远手动触发 |
| `task` | 查看/更新单条工单状态 | UI 外快捷改 |
| `status` | 项目进度看板 | UI 外看总览 |
| `ui` | **全流程界面** | 默认入口 |
| `list` | 所有项目 | 多项目时 |

## 附录 B：关键引用源

- `references/method.md` — 评分口径与所有判据出处
- `references/cn-source-ranking.md` — 国内信源实测榜（CN-GEO 187,818 条去重引用）
- `references/cn-platforms.md` — 国内平台适配
- `references/global-platforms.md` — 海外平台适配
- `references/content-patterns.md` — 可抽取内容模板
- `references/sources.md` — 资料索引（含 GEORank / GEOFlow 选型）

> 每条建议都能追到 `method.md` 的某条实测数字。**说不出依据的别写进方案。**

## 附录 C：与 Claude Code 集成

`SKILL.md` 在仓库根目录——把它放进 Claude Code 技能目录，对 Claude 说「给 example.com 做 GEO」即可驱动全流程。**不用 Claude 也完全可用**，所有脚本都是普通 CLI。

---

*文档维护：随着 `scripts/` 下各模块的演进同步更新。约定：新加的检查器 / 平台 / 评分维度，在本文件「18. 扩展指南」一节补一行示例。*
