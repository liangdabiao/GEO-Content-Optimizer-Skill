# GEO Optimizer

AI 搜索优化（Generative Engine Optimization）全流程工具，帮助品牌内容被 ChatGPT、Perplexity、Gemini 等 AI 搜索引擎引用。

基于 10 步 GEO 实战框架，覆盖从结构化数据生成到效果监控的完整链路。

## 功能模块

### 模块 A：结构化数据生成
自动生成 7 类 JSON-LD Schema，让 AI 引擎理解你的品牌和内容。

| Schema 类型 | 用途 |
|-------------|------|
| Organization | 品牌实体标记 — 告诉 AI "你是谁" |
| FAQPage | FAQ 问答标记 — 43% AI 引用来源 |
| TechArticle / Article | 文章结构化标记 |
| Person | 作者 E-E-A-T 可信度信号 |
| @graph (Person + Article) | 作者 + 文章联合标记 |
| Citation | 权威来源引用标记 |
| BreadcrumbList | 导航层级结构 |

### 模块 B：内容 AI 可读性检测
分析文本的 AI 友好度，从 4 个维度评分：

- 营销词密度（越少越好）
- 平均句长（理想 15-25 字）
- 是否包含直接问句
- 数据/数字引用量

### 模块 C：Pillar Page 集群规划
1 个核心主题 + 5-10 个子主题的内容架构设计，生成内部链接集群 HTML 和站点地图 JSON。

### 模块 D：可见度测试与报告
- **月度测试**：调用 Perplexity API，检测品牌是否被 AI 引擎引用
- **季度报告**：自动对比引用率趋势，生成行动建议

### 模块 E：内容差距分析
输入 URL，自动对比 Google AI Overview 与有机搜索覆盖，找出内容缺口（依赖 `/geo-content-optimizer` skill）。

## 安装

将 `geo-optimizer.skill` 文件放入 Claude Code 的 skills 目录即可，或直接将 `geo-optimizer/` 文件夹放在 `.claude/skills/` 下。

## 使用

在 Claude Code 中通过自然语言触发：

```
# 结构化数据
"帮我生成 Organization Schema"
"生成 FAQ Schema，我有 10 个问答"
"给这篇文章加 Article Schema"

# 内容检测
"检测这段内容的 AI 友好度"
"这个文章口语化够不够"

# 架构规划
"帮我规划一个 Pillar Page 内容集群"
"设计跨境电商工具的内容架构"

# 效果监控
"测试我的品牌在 AI 搜索中的可见度"
"生成一份季度 GEO 报告"

# 内容优化
"优化这个页面 https://example.com"
"GEO 分析 https://example.com"
```

## 脚本说明

### schema_generator.py

```bash
# 生成 Organization Schema
python scripts/schema_generator.py --type organization \
  --name "品牌名" --description "描述" \
  --knows-about "领域1" "领域2" --offers "产品描述"

# 生成 FAQ Schema（从 JSON 文件读取问答对）
python scripts/schema_generator.py --type faq --input faq_pairs.json

# 生成 Article Schema
python scripts/schema_generator.py --type article \
  --headline "标题" --author "作者" --date-published "2025-01-01"

# 生成 E-E-A-T 联合标记
python scripts/schema_generator.py --type eeat --input author_article.json

# 输出带 <script> 标签包裹的 HTML
python scripts/schema_generator.py --type organization --name "品牌" --description "描述" --wrap
```

FAQ 输入文件格式（`faq_pairs.json`）：
```json
[
  {"question": "新手第一步应该做什么？", "answer": "具体答案..."},
  {"question": "A 和 B 有什么区别？", "answer": "具体答案..."}
]
```

### readability_checker.py

```bash
# 检测文本
python scripts/readability_checker.py --text "要检测的内容"

# 检测文件
python scripts/readability_checker.py --file article.txt

# JSON 格式输出
python scripts/readability_checker.py --text "内容" --json
```

输出示例：
```
=== AI 可读性检查报告 ===
总段落数: 5
平均句长: 22字 [OK]
营销词命中: 无 OK
包含问句: [OK]
数据引用: 3个数字 [OK]
综合评分: 高 (6/7)
```

### visibility_tester.py

```bash
python scripts/visibility_tester.py \
  --brand "品牌名" \
  --keywords "关键词1" "关键词2" \
  --api-key "pplx-xxxxx"
```

需要 [Perplexity API Key](https://docs.perplexity.ai/)。结果自动保存到 `visibility_history.json`。

### geo_report_generator.py

```bash
# 生成 Markdown 报告
python scripts/geo_report_generator.py --history visibility_history.json

# 输出到文件
python scripts/geo_report_generator.py --history visibility_history.json --output report.md

# JSON 格式输出
python scripts/geo_report_generator.py --history visibility_history.json --json
```

## 目录结构

```
geo-optimizer/
├── SKILL.md                           # 主技能文件
├── scripts/
│   ├── schema_generator.py            # JSON-LD Schema 生成
│   ├── readability_checker.py         # AI 可读性检测
│   ├── visibility_tester.py           # AI 可见度测试（Perplexity API）
│   └── geo_report_generator.py        # 季度 GEO 报告
├── references/
│   ├── geo-framework.md               # 10 步 GEO 框架参考
│   ├── schema-templates.md            # 9 类 Schema 完整模板
│   └── best-practices.md              # 最佳实践与部署清单
└── assets/
    └── pillar-template.html           # Pillar Page HTML 模板
```

## 30 分钟快速落地

| 步骤 | 耗时 | 操作 |
|------|------|------|
| 实体标记 | 5 min | 生成 Organization JSON-LD |
| FAQ Schema | 10 min | 写 10 个 FAQ + 生成标记 |
| 口语化检查 | 5 min | 跑可读性检测 |
| 引用标记 | 5 min | 加 citation 标记 |
| Schema 全部署 | 10 min | 文章 + 品牌 + 作者 Schema |
| Pillar 集群 | 30 min | 设计 1+5 内容结构 |

## 依赖

- Python 3.7+
- 可见度测试额外需要 `requests` 库（`pip install requests`）和 Perplexity API Key
- 其他脚本仅使用 Python 标准库，零依赖
