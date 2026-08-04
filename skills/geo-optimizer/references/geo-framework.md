# GEO 10 步实战框架

## 目录
1. [关键词 → 实体转型](#step-1)
2. [FAQ 生态系统](#step-2)
3. [口语化写作](#step-3)
4. [引用权威来源](#step-4)
5. [Schema 全面部署](#step-5)
6. [Pillar Page + 内容集群](#step-6)
7. [多格式内容嵌入](#step-7)
8. [系统测试 AI 可见度](#step-8)
9. [E-E-A-T 信号建设](#step-9)
10. [季度迭代报告](#step-10)

---

## Step 1: 关键词 → 实体转型 {#step-1}

AI 引擎通过实体关系理解内容，不靠关键词密度。用自然句子 + 结构化数据告诉 AI "你是谁、做什么、解决什么"。

**核心操作**: 生成 Organization JSON-LD，注入网站 `<head>` 或通过 Google Tag Manager 注入。

**验证工具**: [Schema.org Validator](https://validator.schema.org/)

---

## Step 2: FAQ 生态系统 {#step-2}

43% 的 AI 引用来自 FAQ Schema 内容，是投入产出比最高的单步操作。

**关键数据**: BrightEdge 分析 100 万条 AI 回答，68% 引用来源为高权威站点，43% 来自带正确 Schema 标记的 FAQ。

**操作要点**:
- 最少写 10 个 FAQ
- 问题用自然口语（用户会怎么问 AI）
- 答案含具体数据、案例、可操作建议
- 答案长度 80-200 字

---

## Step 3: 口语化写作，去营销腔 {#step-3}

AI 偏好自然语言。写完后读出来——像正常说话吗？

**规则**:
- 禁用: "创新/领先/卓越/全方位/一站式/极致/颠覆/最佳"
- 平均句长 15-25 字
- 加入直接问句
- 加入具体数据

**检测工具**: `scripts/readability_checker.py`

---

## Step 4: 引用权威来源 + 创造独特数据 {#step-4}

AI 引擎对"引用了权威数据的内容"给更高权重。

**操作要点**:
- 引用 BrightEdge、McKinsey、Forrester 等权威报告
- 使用 citation Schema 标记引用来源
- 创造自有数据: "实测数据: 已服务 X+客户，使用后指标从 A 提升至 B"
- 真实案例数据比任何营销辞藻都有用

---

## Step 5: Schema 标记全面部署 {#step-5}

多个 Schema 类型共同作用提升 AI 抓取概率。

**部署清单**:
- Article/TechArticle Schema — 每篇文章
- FAQ Schema — 含问答内容
- Organization Schema — 品牌信息
- BreadcrumbList Schema — 导航结构
- BlogPosting Schema — 博客文章
- Person Schema — 作者信息

---

## Step 6: Pillar Page + 内容集群 {#step-6}

1 个核心主题页 + 5-10 个子主题 → 上下文链接串联。

**结构**: AI 抓取时把 Pillar Page 当主入口。

**模板**: `assets/pillar-template.html`

---

## Step 7: 多格式内容嵌入 {#step-7}

GPT-4V 分析图片，Gemini 处理音频，多模态内容更容易被引用。

**关键**:
- 图片 alt 属性写完整描述句，不要只写关键词
- 视频必须配字幕（VTT 文件），AI 才能理解视频内容
- 使用 schema.org/ImageObject 结构化标记

---

## Step 8: 系统测试 AI 可见度 {#step-8}

**工具**: `scripts/visibility_tester.py`（Perplexity API）

每月跑一次，记录结果变化，纳入季度报告。

**无 API Key 时**: 在 ChatGPT/Perplexity/Gemini 中手动搜索目标关键词，观察是否提及品牌。

---

## Step 9: E-E-A-T 信号建设 {#step-9}

AI 引擎评估内容的四大维度: Experience（经验）、Expertise（专业）、Authoritativeness（权威）、Trustworthiness（可信）。

**文章底线**: 每篇文章必须有作者署名 + 作者简介，不能是"佚名"或"本站编辑"。AI 对无主内容降权。

---

## Step 10: 季度迭代报告 {#step-10}

**工具**: `scripts/geo_report_generator.py`

每个季度跑一次，输出品牌在 AI 引擎里的可见度变化报告。这是决策下一步 GEO 策略的依据。
