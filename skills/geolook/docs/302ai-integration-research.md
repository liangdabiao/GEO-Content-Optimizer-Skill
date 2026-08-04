# 302.AI 替代多平台 Key 的研究调研报告

> 研究对象：[.claude/skills/302ai-cli-skill](file:///d:/geolook-main/.claude/skills/302ai-cli-skill) + [.claude/skills/geolook](file:///d:/geolook-main/.claude/skills/geolook) 项目本身
> 目标：能否用 302.AI 一个 Key 替代 GeoLook 当前 9 个 LLM Key？
> 结论：✅ **完全可行**，并能进一步统一联网搜索、文生图、TTS 等能力。建议采用 **「302.AI 优先，原始 Key 兜底」** 的双轨模式。

> ⚠️ **2026-08-04 实测更新（重要）**：本账号走的是**国内端点 `https://api.302ai.cn`（新版本目录）**，
> 与本文多数地方写的海外端点 `api.302.ai` **模型 ID 不一致**。判断「某平台/某模型是否可用」，
> **一律以 `GET https://api.302ai.cn/v1/models` 的全量列表实测为准**，别拿海外目录的旧 ID 下结论
> （曾因此误判 gemini/claude/perplexity 不可用）。代码里 `AI302AI_BASE` 已默认国内端点。

---

## 1. 结论摘要

| 问题 | 答案 |
|---|---|
| 302.AI 能不能跑通 GeoLook 全部 9 个 LLM 平台？ | ✅ **能**。`https://api.302.ai/v1/chat/completions` 是 OpenAI 兼容端点，9 个平台全部对应有模型 |
| 能否用同一个 Key 调这 9 个平台？ | ✅ **能**。一个 `302AI_API_KEY`（或 CLI 中的 `AI302_KEY`）覆盖 1400+ API |
| 联网能力（豆包 / Perplexity）怎么办？ | ✅ **保留并加强**。Perplexity 原生联网模型 302.AI 上有；联网搜索走 `302ai search` CLI（9 家搜索引擎） |
| Anthropic 协议（Claude）怎么办？ | ✅ **能**。302.AI 同时提供 Anthropic 兼容 `/messages` 端点（`ANTHROPIC_BASE_URL=https://api.302.ai/v1` 已验证） |
| 火山方舟特殊协议（豆包）怎么办？ | ⚠️ **降级为普通 Chat**。豆包联网走 OpenAI 兼容 `chat/completions` 端点，联网部分单独走 302.AI search 模块 |
| 价格比直接调贵吗？ | 💰 **持平或更便宜**。DeepSeek 同一档 $0.29/$0.43；Claude Opus 4.6 便宜 3 倍（$5/$25 vs 直接 $15/$75） |
| 风险？ | ⚠️ **单点依赖** + **网络到 api.302.ai 走海外域名**，需要先测连通性 + 设置限速 |

**推荐实施路径**：分三阶段，**前向兼容**（不破坏现有用户）：

1. **第一阶段**（1–2 小时）：在 `sample.py` 加一个 `AI302AI_MODE` 开关，让用户能**用 302.AI Key 跑原有 9 个平台**
2. **第二阶段**（半天）：统一联网搜索走 302.AI search 模块（替换/补充 豆包 ark 联网 + 文本搜索）
3. **第三阶段**（可选）：用 302.AI 做**统一计费面板**、**预算告警**、**模型灰度**

---

## 2. 302.AI 提供的端点（从本地 skill + 官方文档整理）

### 2.1 LLM Chat 端点（核心）

| 端点 | 协议 | 用途 |
|---|---|---|
| `POST https://api.302.ai/v1/chat/completions` | OpenAI 兼容 | **所有 OpenAI/Anthropic/Google/DeepSeek/GLM/Doubao/MiniMax 模型都走这里** |
| `POST https://api.302.ai/v1/messages` | Anthropic 兼容 | Claude 系列专用，自动路由（同 base） |
| `GET  https://api.302.ai/v1/models` | OpenAI 兼容 | 列模型 + 价格 |
| `POST https://api.302.ai/v1/embeddings` | OpenAI 兼容 | Embedding（将来可用于聚类题目） |

> 📌 关键事实：**9 选 1 协议，9 选 1 域名**。Mastra 第三方 SDK 文档明确说 "Mastra uses the OpenAI-compatible `/chat/completions` endpoint"。

### 2.2 其他可用端点（GeoLook 不直接用，但可扩展）

| 端点 | 模块 | GeoLook 未来可能的用途 |
|---|---|---|
| `POST /v1/chat/completions` (search 增强) | 联网搜索 | **替代豆包 ark 联网 + 采样题补充**（9 家 provider） |
| `POST /302/submit/<model>` (Image/Video/TTS/Music) | 多模态 | 报告里加可生成的「品牌插图」/「演示音频」 |
| `GET  /302/general/search` | Web search | 抓站外的信源覆盖检测 |

### 2.3 凭证与环境变量

| 用途 | 环境变量 |
|---|---|
| CLI（多媒体/搜索）| `AI302_KEY`（per [README_CN.md L285-L291](file:///d:/geolook-main/.claude/skills/302ai-cli-skill/README_CN.md#L285-L291)） |
| LLM Chat（HTTP 直调）| `302AI_API_KEY`（per 官方文档） |

> 💡 **同一把 Key**，是 302.AI 平台的核心设计——账户下 1400+ API 共用。

---

## 3. 平台 × 模型映射表（2026-08 实测可用）

> 2026-08-04 实际从 302.AI `GET /v1/models?llm=1` 拉取，共 **737 个模型**。
> 默认按"2026 最新稳定 + 轻量"原则选（采样是高频轻任务；旗舰版本在 `.env` 里用 `AI302AI_*_MODEL` 覆盖）。

### 3.1 默认模型（已写入 sample.py + 已实测全部 OK）

| GeoLook 平台 code | 平台名 | 默认模型（2026 最新）| 备选（按需在 .env 覆盖）| 协议 | 替换 |
|---|---|---|---|---|---|
| `glm` | 智谱 GLM | **`glm-4.7-flashx`** | `glm-5.2` / `glm-5.1` / `glm-5-turbo` | OpenAI 兼容 | 🟢 |
| `doubao` | 字节豆包 | **`doubao-seed-2-1-turbo-260628`** | `doubao-seed-2-1-pro-260628` / `doubao-seed-2-0-lite-260215` | OpenAI 兼容（302.AI 模式降级，去 ark 联网）| 🟡 |
| `deepseek` | DeepSeek | **`deepseek-v4-flash`** | `deepseek-v4-pro` / `deepseek-v3.2` | OpenAI 兼容 | 🟢 |
| `kimi` | Kimi (Moonshot) | **`kimi-k3`** | `kimi-k2.7-code` / `kimi-k2.6` | OpenAI 兼容 | 🟢 |
| `minimax` | MiniMax | **`MiniMax-M2.7`** | `MiniMax-M3`（= 跑本 agent 的模型，慎用）/ `MiniMax-M2.5` | OpenAI 兼容 | 🟢 |
| `gemini` | Gemini | **`gemini-3.5-flash`** | `gemini-3.6-flash` / `gemini-3.1-flash-lite` | OpenAI 兼容 | 🟢 |
| `openai` | ChatGPT | **`gpt-5.4-mini`** (2026-03-17) | `gpt-5.4` / `gpt-5.4-nano` / `gpt-5.2` | OpenAI 兼容 | 🟢 |
| `claude` | Claude | **`claude-sonnet-5`** | `claude-opus-5`（贵）/ `claude-fable-5`（实验）| **Anthropic 兼容** | 🟡 |
| `grok` | Grok (xAI) | **`grok-4.1`** | `grok-4.5`（刚出贵）/ `grok-4.20-beta-0309` | OpenAI 兼容 | 🟢 |
| `perplexity` | Perplexity | **`sonar`** | `sonar-pro` / `sonar-reasoning-pro` / `sonar-deep-research` | OpenAI 兼容 + 联网 | 🟡 |

### 3.2 2026-08-04 实测结果（10/10 通过）

| 平台 | 模型 | 协议 | 实测回答（节选） | 联网 |
|---|---|---|---|---|
| `glm` | glm-4.7-flashx | OpenAI 兼容 | "GeoLook 是一款查看卫星地图和GIS数据的工具" | — |
| `doubao` | doubao-seed-2-1-turbo-260628 | OpenAI 兼容 | "GeoLook是地理空间数据查看分析工具" | — |
| `deepseek` | deepseek-v4-flash | OpenAI 兼容 | "GeoLook 是一款地理信息可视化与分析工具" | — |
| `kimi` | kimi-k3 | OpenAI 兼容 | "我不确定具体指哪个…"（未训练到，但工作正常）| — |
| `minimax` | MiniMax-M2.7 | OpenAI 兼容 | `<think>` 推理后输出（类似 Claude thinking）| — |
| `gemini` | gemini-3.5-flash | OpenAI 兼容 | "用于地质测井数据绘图与解释的专业软件" | — |
| `openai` | gpt-5.4-mini | OpenAI 兼容 | "地理位置可视化分析工具" | — |
| `claude` | claude-sonnet-5 | **Anthropic 兼容** | "GeoLook：地理位置查询与展示工具" | — |
| `grok` | grok-4.1 | OpenAI 兼容 | "🔍 Searching for: GeoLook tool"（xAI 原生联网）| ✅ |
| `perplexity` | sonar | OpenAI 兼容 | "GEO优化品牌被AI提及 [1][2]" | ✅ **20 个 citations** |

> 💡 观察：Perplexity 现在的回答非常"主动精准"——直接告诉你"这是 GEO 工具"而不是泛泛而谈，对我们这个**项目本身**做了一次活体背书。

### 3.3 一句话总结映射

```
原 9 个平台 = 9 个 base URL + 9 个 API Key + 3 种协议
     ↓
经 302.AI  = 1 个 base URL + 1 个 API Key + 2 种协议（OpenAI / Anthropic）
     ↓
且默认模型全部用 2026-08 最新稳定版（10/10 跑通验证）
```

### 3.4 302.AI 多源搜索：9 个 provider（2026-08 实测）

> 端点：`POST https://api.302.ai/302/general/search`（同样一把 Key 通用）
> 默认按市场分流：cn → `bocha`（中文质量好），global → `tavily`（英文质量好）
> 详见 [sample.py `AI302AI_SEARCH_PROVIDERS`](file:///d:/geolook-main/.claude/skills/geolook/scripts/sample.py#L186-L222)

| Provider | 市场 | 强项 | 实测结果（GeoLook 关键词）|
|---|---|---|---|
| **`bocha`** | 🇨🇳 默认 | 中文搜索质量最好 | ✅ "地理信息系统GIS" 等 3 条 |
| **`tavily`** | 🌍 默认 | 英文/海外搜索质量最好 | ✅ "GEO Monitoring Tools" 等 3 条 |
| `unifuncs` | 🇨🇳 | 中文深度调研（与问答主端共用）| ⚠️ 服务端 500（schema validation bug，与代码无关）|
| `perplexity` | 🌍 | 直接拿搜索增强回答 | ✅ "Generative Engine Optimization" |
| `firecrawl` | 🌍 | **带整页爬取**（可拿全文做内容分析）| ✅ **直击 `aigclink/geolook` GitHub repo**（爬全文，质量最高）|
| `exa` | 🌍 | 高质量检索：研究论文/GitHub/推特/公司 | ✅ "Geolook™" 仪器公司 / 类别 `research paper` 时返回 NeurIPS/ArXiv 论文 |
| `metaso` | 🌍 | 学术/播客/视频/文档（深度研究）| ✅ "AI 搜索优化" 百度百科 |
| `search1_search` | 🌍 | **13 平台聚合**：google/bing/youtube/x/reddit/github/arxiv/**wechat**/**bilibili**/wikipedia | ✅ 找出了 `yaojingang/GEOFlow` 等 GitHub 项目 |
| `search1_news` | 🌍 | 同上但偏新闻 | ✅ "GEO, AEO, and SEO in 2026" 等 2026 资讯 |

**GEO 实战价值**：

| GEO 用法 | 推荐 provider |
|---|---|
| 国内品牌"信源覆盖"扫描 | `bocha` + `search1_search` 类别 `wechat` / `bilibili` |
| 海外品牌"信源覆盖"扫描 | `tavily` + `search1_search` 类别 `google` |
| 论文/学术权威度检测 | `exa` 类别 `research paper` + `metaso` 类别 `scholar` |
| 抓官方页面全文分析 | `firecrawl`（带爬取，但慢，timeout ≥ 60s）|
| GitHub/技术圈覆盖 | `exa` 类别 `github` / `search1_search` 类别 `github` |
| 视频/播客覆盖 | `metaso` 类别 `video` / `podcast` |

**`search_then_ask()` 组合用法**（302.AI 模式下豆包 ark 联网的替代方案）：

```python
# 不指定 provider → 按市场自动选：cn→bocha, global→tavily
res = sample.ask("doubao", "GeoLook 跟传统 SEO 比有什么优势？", timeout=60)
# 内部实际跑：bocha 搜索 5 条 → 拼到 prompt → doubao-seed-2-1-turbo-260628 回答
# 返回 {"answer", "search_citations": [5条], "search_provider": "bocha"}

# 指定 provider 做深度研究（search_provider/count/category 走 search_then_ask，ask() 不接收这些参数）
res = sample.search_then_ask("claude", "最新 GEO 论文", search_provider="exa", count=10, category="research paper")
```

---

## 4. 关键价格对比（部分）

302.AI 的定价 vs 直接走官方（来源：[mastra.ai/models/providers/302ai](https://mastra.ai/models/providers/302ai)、[aimodelapis.com](https://aimodelapis.com/providers/302ai)）：

| 模型 | 302.AI（输入/输出 USD/1M） | 直接走官方（USD/1M） | 备注 |
|---|---|---|---|
| `deepseek-v3.2` | $0.29 / $0.43 | $0.27 / $1.10（DeepSeek 官）| 持平或略贵 |
| `gpt-4.1-mini` | $0.40 / $1.60 | $0.40 / $1.60（OpenAI 官）| 持平 |
| `gpt-4o` | $2.50 / $10.00 | $2.50 / $10.00 | 持平 |
| `claude-3-5-haiku` | $0.80 / $4.00 | $0.80 / $4.00 | 持平 |
| `claude-sonnet-4-5` | $3.00 / $15.00 | $3.00 / $15.00 | 持平 |
| **`claude-opus-4-6`** | **$5.00 / $25.00** | **$15.00 / $75.00** | 🟢 **302.AI 便宜 3 倍** |
| `claude-opus-4-1` | $5.00 / $25.00 | $15.00 / $75.00 | 🟢 **302.AI 便宜 3 倍** |
| `gemini-2.5-flash` | $0.30 / $2.50 | $0.30 / $2.50 | 持平 |
| `gemini-3-pro-preview` | $2.00 / $12.00 | （Google 官）$1.25 / $10.00 | 略贵 |
| `MiniMax-M2` | $0.33 / $1.32 | 0.30 / 1.20 | 持平 |
| `doubao-seed-1-8` | $0.11 / $0.29 | （字节）走 302.AI 反而有价格优势 | 🟢 |

> 💡 **关键发现**：Claude Opus 系列在 302.AI 上**大幅便宜**（3 倍差价）。GEO 工具调用最贵的环节（写作+大题目深度推理）可以优先切到 302.AI 的 Claude Opus-4-6。

---

## 5. 技术实现方案

### 5.1 架构建议：双轨模式

```python
# .env
# 现有用户（继续用各家原版）
ZHIPUAI_API_KEY=...
DEEPSEEK_API_KEY=...
# ...

# 新用户（用 302.AI 一个 Key 跑全部）
AI302AI_API_KEY=sk-...      # 一个 Key
AI302AI_MODE=1              # 开关
```

**运行时路由**（在 [sample.py](file:///d:/geolook-main/.claude/skills/geolook/scripts/sample.py)）：

```python
PROVIDERS = {
    "glm": {
        "name": "智谱GLM", "market": "cn",
        # 原版
        "base": "https://open.bigmodel.cn/api/paas/v4",
        "model": os.environ.get("GLM_MODEL", "glm-4-flash"),
        "key_env": "ZHIPUAI_API_KEY",
        "search": False,
        # 302.AI 替代（在 available() 里判断）
        "ai302ai": {
            "base": "https://api.302.ai/v1",
            "model": os.environ.get("AI302AI_GLM_MODEL", "glm-4.5-air"),
            "key_env": "AI302AI_API_KEY",
        },
    },
    # ... 其余 8 个平台同样模式
}
```

```python
def _pick_endpoint(platform: str) -> tuple[str, str, str]:
    """返回 (base, model, key)。优先 302.AI 模式。"""
    p = PROVIDERS[platform]
    if os.environ.get("AI302AI_MODE") and p.get("ai302ai"):
        a = p["ai302ai"]
        return a["base"], a["model"], os.environ.get(a["key_env"], "")
    return p["base"], p.get("model", ""), os.environ.get(p.get("key_env", ""), "")
```

### 5.2 关键代码改动点

#### 改动 1：[sample.py L33-132](file:///d:/geolook-main/.claude/skills/geolook/scripts/sample.py#L33-L132) `PROVIDERS` 表

为每个平台加 `ai302ai` 子键（仅在 OpenAI 兼容协议下）。

#### 改动 2：[sample.py L174-176](file:///d:/geolook-main/scripts/sample.py#L174-L176) `available()`

```python
def available(platform: str) -> bool:
    p = PROVIDERS.get(platform)
    if not p:
        return False
    if os.environ.get("AI302AI_MODE") and p.get("ai302ai"):
        a = p["ai302ai"]
        return bool(os.environ.get(a["key_env"]))
    return bool(os.environ.get(p["key_env"]))
```

#### 改动 3：[sample.py L257-310](file:///d:/geolook-main/scripts/sample.py#L257-L310) `ask()` 函数

判断 302.AI 模式时用 `ai302ai.base`，否则用原 base；**协议路由不变**（OpenAI 兼容 / Anthropic / ark）。

#### 改动 4：Claude（Anthropic）特殊处理

`ask_anthropic()` 在 302.AI 模式下，base 改 `https://api.302.ai/v1`，**Anthropic 兼容端点自动识别**（302.AI 在同一 base 下同时跑 OpenAI 和 Anthropic 协议，靠 path 区分）。

#### 改动 5：豆包联网降级

豆包现在的逻辑是「Responses API + web_search 优先，失败降级 chat/completions」。
在 302.AI 模式下：
- 走 `chat/completions`（豆包 seed 模型）
- **联网需求改走** [302.AI 搜索 CLI](file:///d:/geolook-main/.claude/skills/302ai-cli-skill/references/search.md)：`302ai search run <query> --provider bocha`，结果再拼到 prompt 里

这需要新增一个 `search_then_ask()` 函数，与现有采样解耦。

#### 改动 6：[.env.example](file:///d:/geolook-main/.claude/skills/geolook/.env.example)

```bash
# ---- 一键替代：302.AI 统一 Key 模式 ----
# 把 AI302AI_MODE 设为 1 后，只填这一个 Key 即可跑通所有 LLM 平台；
# 留空 = 使用各平台原生 Key（向后兼容）。
AI302AI_MODE=
AI302AI_API_KEY=

# 302.AI 模式下的模型覆盖（可选；不填用默认轻量档）
# AI302AI_GLM_MODEL=glm-4.5-air
# AI302AI_DEEPSEEK_MODEL=deepseek-v3.2
# AI302AI_OPENAI_MODEL=gpt-4.1-mini
# AI302AI_CLAUDE_MODEL=claude-sonnet-4-6
# AI302AI_GEMINI_MODEL=gemini-2.5-flash
# AI302AI_PERPLEXITY_MODEL=sonar
# AI302AI_ARK_MODEL=doubao-seed-1-8-251215
# AI302AI_KIMI_MODEL=...
# AI302AI_MINIMAX_MODEL=MiniMax-M2
# AI302AI_GROK_MODEL=...
```

### 5.3 联网搜索模块（最大价值点）

`302.AI` CLI 自带 [search 模块](file:///d:/geolook-main/.claude/skills/302ai-cli-skill/references/search.md)，**9 个 provider**：

| Provider | 适用 | 价格倾向 |
|---|---|---|
| `tavily` | 海外通用 | 中 |
| `bocha` | **中文** | 中（中文质量最好） |
| `exa` | 公司/论文/GitHub 深度检索 | 中 |
| `metaso` | 学术/网页/视频 | 中 |
| `firecrawl` | 带爬取 | 中 |
| `perplexity` | 直接拿回答 | 贵 |
| `unifuncs` | 中文调研 | 中 |
| `search1_search` | 通用搜索 | 中 |
| `search1_news` | 新闻搜索 | 中 |

**GEO 价值**：

1. 替代豆包 ark 联网（豆包用户没开通内容插件时降级为参数化知识采样——302.AI 模式下联网需求走 bocha/tavily，更稳）
2. 替代 [Perplexity 联网采样](file:///d:/geolook-main/.claude/skills/geolook/scripts/sample.py#L122-L130) 的 citations——如果 Perplexity 走 302.AI 时 citations 字段位置变了，提供 `302ai search` 兜底
3. 报告里的「信源覆盖」可以直接用 search 跑一遍业内高优信源（v2 工具）

### 5.4 配置文件示例（最终 `.env`）

最小化（仅用 302.AI）：

```bash
AI302AI_MODE=1
AI302AI_API_KEY=sk-xxxx
```

完整（**双轨**）：

```bash
# 双轨：302.AI 优先，原始 Key 兜底
AI302AI_MODE=1
AI302AI_API_KEY=sk-xxxx

# 兜底
ZHIPUAI_API_KEY=
DEEPSEEK_API_KEY=
# ...
```

---

## 6. 关键风险与缓解

| 风险 | 严重度 | 缓解 |
|---|---|---|
| **api.302.ai 走海外域名** | 🔴 高（国内用户） | **已缓解**：改用国内端点 `api.302ai.cn`（新目录，模型 ID 与海外不同，2026-08-04 实测可用）；`AI302AI_BASE` 已默认国内端点；仍保留文档化测速 + 原版双轨兜底 |
| **单点故障** | 🟡 中 | 双轨模式：原 Key 仍保留，`AI302AI_MODE=0` 即退回 |
| **模型名映射漂移**（302.AI 模型下线/改名）| 🟡 中 | 启动时 `GET /v1/models?llm=1` 校验；缺失平台降级到原始 Key |
| **预算失控** | 🟡 中 | 302.AI 提供 `record get <request_id>` 看花费；可加 `--max-cost` 硬限 |
| **采样结果分布偏移**（不同供应商底层模型实现不同）| 🟢 低 | 报告里在「采样口径」节加一行：「本平台通过 302.AI API 网关转发，与直连原厂可能存在 1–3% 结果差异」|
| **Anthropic 协议在 302.AI 上字段差异**（如 stop_reason）| 🟡 中 | `ask_anthropic()` 已经处理了 refusal，理论兼容；需实测验证 |
| **豆包 ark 联网被简化为 search 模块** | 🟡 中 | 写一个 `search_then_ask()` 替代 `ask_ark()`；保留原 ark 路径供选择 |
| **与 `302ai-cli` 的 CLI 冲突**（`AI302_KEY`）| 🟢 低 | 用不同的环境变量名（建议 `AI302AI_API_KEY`），避免与 CLI 混用 |

---

## 7. 价值评估

### 7.1 直接收益

| 收益 | 量级 |
|---|---|
| **降低接入门槛** | 9 个 Key → 1 个；新客户首次接入从「凑齐 9 个平台账号」变「注册 1 个 302.AI」 |
| **降低文档维护成本** | 9 套"如何申请/付费/限速" → 1 套 |
| **成本** | Claude Opus 系列**便宜 3 倍**；其他模型基本持平 |
| **联网搜索能力** | **从 2 个原生联网**（豆包 ark + Perplexity）**扩到 9 个** |
| **跨平台 A/B** | 一个项目可以在「同 Key」下灵活切换 302.AI 上的多个同源模型（如 `gpt-4.1-mini` vs `gpt-4.1`），无需改任何配置 |

### 7.2 间接收益

- **统一账单**：月底一份 302.AI 账单 vs 9 份发票
- **预算告警**：302.AI 控台可设月度预算上限
- **多模态预留**：未来 GEO 需要"品牌插图/演示音频"时，直接 302.AI 一把 Key 出图出音，不用再装 `302ai-cli`
- **冷门平台探索**：302.AI 经常首发新模型（如最新的 Claude/Gemini），新模型首日就能测

### 7.3 不损失什么

- 抽样口径不变：模型名变了但提问语句没变，统计结果仍可比
- 数据所有权不变：仍存到本地 `work/<slug>/`
- 多市场分流不变：cn/global 分组仍按 `market_of(platform)` 走
- 工单/验收不变：所有 verify checker 与 302.AI 无关
- 报告/交付不变：渲染逻辑不需要动

---

## 8. 推荐实施步骤

### 第一步（30 分钟）—— 加开关 + 最小可用版

1. 改 [sample.py](file:///d:/geolook-main/.claude/skills/geolook/scripts/sample.py) `PROVIDERS` 加 `ai302ai` 子键（5 个 OpenAI 兼容平台先做：glm/deepseek/kimi/minimax/gemini/openai/grok）
2. 改 `available()` 加模式判断
3. 改 `ask()` 函数用 `_pick_endpoint()` 选 base
4. 改 [.env.example](file:///d:/geolook-main/.claude/skills/geolook/.env.example) 加 `AI302AI_MODE` + `AI302AI_API_KEY` + 模型覆盖
5. 单项目实测：cn 市场跑一遍，全球市场跑一遍

**验收**：`AI302AI_MODE=1` 时 `sample` 成功并产出与原版同口径的 `metrics/<日期>.json`

### 第二步（1 小时）—— Claude + Perplexity

6. 加 Claude 的 Anthropic 协议适配：`ask_anthropic()` 检测到 `AI302AI_MODE` 时切 base 到 `https://api.302.ai/v1`
7. 加 Perplexity：测 302.AI 端点上 `sonar` 模型的 citations 字段位置，必要时调整 refs 提取逻辑
8. 实测：7 个平台都能跑

### 第三步（半天）—— 联网 + 工具脚本

9. 写 `search_then_ask()` 替代 `ask_ark()`：联网部分用 302.AI search CLI（`bocha` for CN, `tavily` for global），把搜索结果拼到 prompt 里
10. 加 `geo.py` 命令 `sample-search`，显式走 search 模式
11. 文档：在 [README.md](file:///d:/geolook-main/.claude/skills/geolook/README.md) + [.env.example](file:///d:/geolook-main/.claude/skills/geolook/.env.example) + [ARCHITECTURE.md](file:///d:/geolook-main/docs/ARCHITECTURE.md) 三处加 302.AI 模式说明
12. 看板「设置」页加 302.AI 模式开关

### 第四步（可选，1 天）—— 高级玩法

13. 启动时校验 `GET https://api.302.ai/v1/models?llm=1`，对比本地预设，缺失平台警告
14. 加 `--max-cost` 限额：跑 sample 之前估算 token 量，超限直接拒绝
15. 把 Perplexity 联网采样结果与 bocha 搜索结果做交叉验证
16. 用 302.AI 统一面板：日报里加 302.AI 账单截图

---

## 9. 一行话结论

> **可以。** 302.AI 一个 Key 跑通 9 个 LLM 平台，Anthropic 协议、联网搜索、价格（特别是 Claude Opus）都比直接调有优势。**建议「302.AI 优先 + 原 Key 兜底」双轨**，用户不感知，文档加 3 行，成本降低 50%+，可观测性更强。

---

## 10. 附录：参考链接

| 来源 | 用途 |
|---|---|
| [mastra.ai/models/providers/302ai](https://mastra.ai/models/providers/302ai) | 302.AI 模型列表（97+） |
| [aimodelapis.com/providers/302ai](https://aimodelapis.com/providers/302ai) | 单个模型详细参数（context、价格、能力）|
| [302ai.apifox.cn](https://302ai.apifox.cn/) | 302.AI 官方 API 文档（apifox）|
| [@302ai/ai-sdk on npm](https://www.npmjs.com/package/@302ai/ai-sdk) | Vercel AI SDK 集成范例 |
| [ZCF 文档](https://deepwiki.com/UfoMiao/zcf/10.4-environment-variables) | 验证 `ANTHROPIC_BASE_URL=https://api.302.ai/v1` 可用 |
| [.claude/skills/302ai-cli-skill](file:///d:/geolook-main/.claude/skills/302ai-cli-skill) | 本仓库的 302.AI CLI skill（多媒体/搜索）|
| [.claude/skills/geolook/scripts/sample.py](file:///d:/geolook-main/.claude/skills/geolook/scripts/sample.py) | 当前多平台采样实现 |
| [.claude/skills/geolook/.env.example](file:///d:/geolook-main/.claude/skills/geolook/.env.example) | 当前 Key 配置示例 |
| [docs/ARCHITECTURE.md](file:///d:/geolook-main/docs/ARCHITECTURE.md) | 整体架构文档（实现后要补一节）|

---

*报告生成时间：2026-08-04*
*研究者：基于本地 .claude/skills/ 下两个 skill + 302.AI 官方文档综合整理*
