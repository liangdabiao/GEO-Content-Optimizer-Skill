# GEO Content Optimizer

AI 驱动的网页内容优化分析工具，基于 Claude Code Skill 实现。

## 功能

输入一个 URL，自动完成以下分析流程：

1. **抓取页面标题** — 提取网页 H1 或标题
2. **查询扩展研究** — 基于标题在 Google 上进行多角度搜索
3. **主查询提取** — 从搜索结果中提炼核心 Google 搜索词
4. **AI Overview 获取** — 从 Google 搜索结果中获取 AI Overview 内容
5. **搜索摘要生成** — 将查询扩展结果整理为结构化摘要
6. **对比分析报告** — 对比摘要与 AI Overview，生成优化建议

## 使用方法

在 Claude Code 中调用：

```
/geo-content-optimizer https://example.com
```

## 输出文件

每次分析按 URL 域名生成独立文件夹，互不覆盖：

```
output/
  apimart-ai/              ← https://apimart.ai/
    report.md
    ai_overview.md
    query_fanout.md
    query_fanout_summary.md
  openai-com/              ← https://openai.com/
    report.md
    ...
```

| 文件 | 说明 |
|------|------|
| `report.md` | 最终优化报告（对比表格 + 行动建议） |
| `query_fanout.md` | 原始搜索结果 |
| `ai_overview.md` | Google AI Overview 内容 |
| `query_fanout_summary.md` | 搜索结果摘要 |

## 零依赖

无需 Python 环境、无需 API Key。直接使用 Claude Code 内置工具（WebSearch、Web Reader、Playwright）完成所有操作。
 