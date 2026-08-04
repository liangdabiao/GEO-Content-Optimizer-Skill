---
name: geo-optimizer
description: >
  GEO (Generative Engine Optimization) 全流程优化工具。帮助品牌内容被 ChatGPT、Perplexity、Gemini 等 AI 搜索引擎引用。
  包含 5 大模块：结构化数据生成 (JSON-LD Schema)、内容 AI 可读性检测、内容集群架构规划、AI 可见度监控与季度报告、内容差距分析。
  当用户提到 "GEO"、"AI搜索优化"、"AI 引用优化"、"Schema 标记"、"JSON-LD"、"FAQ Schema"、"E-E-A-T"、
  "内容被 AI 抓取"、"Pillar Page"、"内容集群"、"AI 可见度"、"Generative Engine Optimization" 时触发。
  也适用于用户要求："帮我生成 Schema"、"检测内容 AI 友好度"、"优化让 AI 引用我的内容"、"测试品牌在 AI 搜索中的曝光"。
---

# GEO Optimizer

AI 搜索优化全流程工具，基于 10 步 GEO 实战框架，帮助品牌内容被 AI 引擎引用。

## 工作流决策树

根据用户需求选择执行路径：

```
用户提供 URL 要求优化？
  → 模块 E：内容差距分析（调用 /geo-content-optimizer）

用户要求生成 Schema/JSON-LD？
  → 模块 A：结构化数据生成

用户提供文本要求检测质量？
  → 模块 B：内容 AI 可读性检测

用户要求规划内容架构？
  → 模块 C：Pillar Page 集群规划

用户要求测试/监控 AI 曝光？
  → 模块 D：可见度测试与报告

用户首次使用 / 不确定从哪开始？
  → 执行"首次完整 GEO 设置"流程（见下方）
```

---

## 首次完整 GEO 设置流程

适用于从未做过 GEO 优化的用户，按顺序执行：

1. 收集品牌信息（名称、行业、核心业务、目标市场）
2. 执行模块 A1：生成 Organization Schema
3. 引导用户创建 ≥10 个 FAQ 问答对
4. 执行模块 A2：生成 FAQ Schema
5. 执行模块 A3：为已有文章生成 Article Schema
6. 执行模块 B：检测关键页面的 AI 可读性
7. 执行模块 C：规划 Pillar Page 内容集群
8. 执行模块 D1：首次 AI 可见度基线测试
9. 汇总输出完整 GEO 部署清单

---

## 模块 A：结构化数据生成

使用 `scripts/schema_generator.py` 或参考 `references/schema-templates.md` 生成 JSON-LD。

### A1. Organization 实体标记

收集以下信息后生成：
- 品牌名称、一句话描述、成立年份
- 目标市场 (areaServed)
- 核心领域 (knowsAbout, 3-5 个)
- 提供的产品/服务描述

```bash
python scripts/schema_generator.py --type organization --name "品牌名" --description "描述" --knows-about "领域1" "领域2" --offers "产品描述"
```

### A2. FAQ Schema

要求用户提供 ≥10 个问答对。每个问答要：
- 问题用自然口语（用户会怎么问 AI）
- 答案含具体数据、案例、可操作建议
- 答案长度 80-200 字

```bash
python scripts/schema_generator.py --type faq --input faq_pairs.json
```

输入文件格式：
```json
[
  {"question": "新手第一步应该做什么？", "answer": "具体答案..."},
  {"question": "A 和 B 有什么区别？", "answer": "具体答案..."}
]
```

### A3. Article Schema

为每篇文章生成 TechArticle 或 Article Schema。

### A4. E-E-A-T 作者标记

生成 Person + Article @graph 联合标记。要求：
- 作者署名 + 简介（不能是"佚名"/"本站编辑"）
- 列出社交账号 (sameAs)
- 列出资质/成果 (hasCredential)

### A5. 引用标记

为引用了权威来源的文章添加 citation Schema。

**Schema 模板详见**：[references/schema-templates.md](references/schema-templates.md)

---

## 模块 B：内容 AI 可读性检测

使用 `scripts/readability_checker.py` 分析文本。

```bash
python scripts/readability_checker.py --text "要检测的文本内容"
python scripts/readability_checker.py --file article.txt
```

检测维度：
1. **营销词密度** — "创新/领先/卓越/全方位/一站式/极致/颠覆/最佳" 等，越少越好
2. **平均句长** — 理想 15-25 字，>35 字 AI 难以理解
3. **直接问句** — 包含 "？/?" 的句子，AI 偏好有问句的内容
4. **数据引用** — 具体数字/百分比/金额，AI 更信任含数据的内容
5. **综合评分** — 高/中/低

优化建议规则：
- 营销词 > 3 个 → 建议替换为具体事实描述
- 句长 > 25 字 → 建议拆分长句
- 无问句 → 建议加入 1-2 个直接问句
- 无数据 → 建议加入行业数据或自有统计

---

## 模块 C：Pillar Page 集群规划

### 设计内容集群结构

1 个核心主题页 + 5-10 个子主题，内部链接串联。

收集用户输入：
- 核心主题（Pillar Page 标题）
- 子主题列表（5-10 个相关主题）
- 每个子主题与核心主题的关系

生成内容：
- 集群 HTML 代码块（放到每篇子文章末尾）
- 站点地图 JSON 结构
- 内部链接策略建议

**模板详见**：[assets/pillar-template.html](assets/pillar-template.html)

---

## 模块 D：可见度测试与报告

### D1. AI 可见度测试（月度）

使用 `scripts/visibility_tester.py` 调用 Perplexity API。

```bash
python scripts/visibility_tester.py --brand "品牌名" --keywords "关键词1" "关键词2" --api-key "pplx-xxx"
```

要求用户提供 Perplexity API Key（获取：https://docs.perplexity.ai/）。

脚本会：
1. 用多个关键词构造查询
2. 检测品牌名是否出现在 AI 回复中
3. 提取引用上下文
4. 结果自动追加到历史 JSON 文件

**无 API Key 时**：提供手动测试指引（在 ChatGPT/Perplexity/Gemini 中搜索目标关键词，观察是否提及品牌）。

### D2. 季度 GEO 报告

使用 `scripts/geo_report_generator.py`。

```bash
python scripts/geo_report_generator.py --history visibility_history.json
```

报告包含：
- 引用率趋势（前半期 vs 后半期）
- 趋势方向（上升/下降/持平）
- 行动建议（根据趋势自动生成）

---

## 模块 E：内容差距分析

当用户提供 URL 要求优化时，调用已有的 `/geo-content-optimizer` skill。

触发词："优化这个页面"、"分析这个网址"、"GEO 分析"、用户提供 URL 要求改进。

执行方式：`/geo-content-optimizer <url>`

该 skill 会自动完成：抓取标题 → Google 查询扩展 → AI Overview 获取 → 对比分析 → 优化建议报告。

---

## 30 分钟快速落地清单

| 步骤 | 时间 | 操作 |
|------|------|------|
| 实体标记 | 5 min | 模块 A1：生成 Organization JSON-LD |
| FAQ Schema | 10 min | 模块 A2：写 10 个 FAQ + 生成标记 |
| 口语化检查 | 5 min | 模块 B：跑可读性检测 |
| 引用标记 | 5 min | 模块 A5：加 citation 标记 |
| Schema 全部署 | 10 min | 模块 A3/A4：文章 + 品牌 + 作者 |
| Pillar 集群 | 30 min | 模块 C：设计 1+5 内容结构 |
| 可见度测试 | 5 min/月 | 模块 D1：跑 API 脚本 |
| 季度报告 | 10 min/季 | 模块 D2：跑对比分析 |

---

## 参考资料

- **GEO 10 步框架**：[references/geo-framework.md](references/geo-framework.md) — 每步原理、数据支撑、操作要点
- **Schema 模板汇总**：[references/schema-templates.md](references/schema-templates.md) — 所有 JSON-LD 类型完整模板
- **最佳实践**：[references/best-practices.md](references/best-practices.md) — 行业数据、部署清单、常见错误
