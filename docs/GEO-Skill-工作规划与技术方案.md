# GEO Skill 工作规划与技术方案

## 一、项目概述

**目标**：制作一个 Claude Code Skill，让 AI 能够帮助用户系统化地执行 GEO（Generative Engine Optimization）——即 AI 搜索引擎优化，使品牌内容更容易被 ChatGPT、Perplexity、Gemini 等 AI 引擎引用。

**核心价值**：将原本需要 SEO 专家手动操作的 10 步 GEO 框架，转化为 AI 可自动执行的标准化工作流。

---

## 二、Skill 功能模块设计

基于参考资料中的 10 步 GEO 框架，将功能分为 **4 大模块、10 个子功能**：

### 模块 A：结构化数据生成（Step 1/2/4/5/9）

| 子功能 | 输入 | 输出 | 说明 |
|--------|------|------|------|
| A1. 实体标记生成 | 品牌名称、行业、描述 | Organization JSON-LD | 告诉 AI 引擎"你是谁" |
| A2. FAQ Schema 生成 | 业务问答对列表（≥10个） | FAQPage JSON-LD | 43% AI 引用来自 FAQ |
| A3. 文章 Schema 生成 | 文章标题、作者、日期 | TechArticle/Article JSON-LD | 每篇文章必备 |
| A4. E-E-A-T 作者标记 | 作者信息、资质、社交链接 | Person + Article @graph JSON-LD | 建立可信度信号 |
| A5. 引用标记生成 | 引用的权威来源列表 | Article + citation JSON-LD | 提升内容权威性 |

### 模块 B：内容质量检测（Step 3）

| 子功能 | 输入 | 输出 | 说明 |
|--------|------|------|------|
| B1. AI 可读性检测 | 文本内容 | 检测报告（句长/营销词/问句/数据） | Python 脚本执行 |

### 模块 C：内容架构规划（Step 6/7）

| 子功能 | 输入 | 输出 | 说明 |
|--------|------|------|------|
| C1. Pillar Page 规划 | 核心主题、子主题列表 | 集群 HTML + 站点地图 JSON | 生成内容集群结构 |
| C2. 多格式嵌入模板 | 媒体类型 | 结构化 HTML 模板 | 图片/视频/音频嵌入规范 |

### 模块 D：效果监控与报告（Step 8/10）

| 子功能 | 输入 | 输出 | 说明 |
|--------|------|------|------|
| D1. AI 可见度测试 | 品牌名、关键词、API Key | 测试报告（是否被引用+上下文） | 调用 Perplexity API |
| D2. 季度 GEO 报告 | 历史检测数据 JSON | 趋势报告 + 行动建议 | 自动对比分析 |

---

## 三、Skill 目录结构

```
geo-optimizer/
├── SKILL.md                          # 主技能文件（工作流指引）
├── scripts/
│   ├── readability_checker.py        # AI 可读性检测脚本
│   ├── visibility_tester.py          # AI 可见度测试脚本（Perplexity API）
│   ├── geo_report_generator.py       # 季度 GEO 报告生成脚本
│   └── schema_generator.py           # JSON-LD Schema 批量生成脚本
├── references/
│   ├── geo-framework.md              # 10 步 GEO 框架完整参考
│   ├── schema-templates.md           # 各类 JSON-LD 模板汇总
│   └── best-practices.md             # GEO 最佳实践与行业数据
└── assets/
    └── pillar-template.html          # Pillar Page HTML 模板
```

---

## 四、各文件职责与技术细节

### 4.1 SKILL.md（核心工作流）

**职责**：定义 Skill 的触发条件、整体工作流、以及如何调度各脚本和参考文档。

**触发条件设计**：
- 用户提到"GEO"、"AI搜索优化"、"Generative Engine Optimization"
- 用户要求生成 Schema 标记、JSON-LD、FAQ Schema
- 用户要求检测内容对 AI 的友好度/可读性
- 用户要求测试品牌在 AI 引擎中的可见度
- 用户要求规划内容集群/Pillar Page

**工作流设计**（用户进入后按需执行）：

```
用户触发 → 诊断阶段 → 方案阶段 → 执行阶段 → 验证阶段

诊断：用户当前处于 GEO 哪个阶段？已有内容还是从零开始？
方案：根据诊断推荐具体执行步骤
执行：调用对应脚本/模板生成产出物
验证：运行检测脚本确认效果
```

**预估行数**：~300-400 行（控制在 500 行以内）

### 4.2 scripts/schema_generator.py

**功能**：根据用户输入的参数，批量生成各类 JSON-LD Schema。

**核心逻辑**：
```python
# 支持的 Schema 类型
SCHEMA_TYPES = ["Organization", "FAQPage", "TechArticle", "Article",
                "BreadcrumbList", "BlogPosting", "Person"]

# 输入方式：JSON 配置文件 或 命令行参数
# 输出方式：直接打印 JSON-LD，或写入文件

def generate_organization(name, description, knows_about, offers):
    ...

def generate_faq(questions: list[dict]):
    ...  # questions: [{"q": "...", "a": "..."}]

def generate_article(headline, author, date_published, ...):
    ...

def generate_person(name, job_title, knows_about, same_as):
    ...

def generate_eeat_graph(author_info, article_info):
    ...  # @graph 联合 Person + Article

def generate_citation(sources: list[dict]):
    ...
```

**调用方式**：
```bash
python scripts/schema_generator.py --type organization --config brand.json
python scripts/schema_generator.py --type faq --input faq_pairs.json
```

### 4.3 scripts/readability_checker.py

**功能**：检测文本内容的 AI 可读性，输出结构化报告。

**检测维度**：
1. 营销词密度（创新、领先、卓越等）
2. 平均句长（理想 15-25 字）
3. 是否包含直接问句（AI 友好信号）
4. 数据/数字引用量
5. 段落结构合理性
6. 综合评分：高/中/低

**输出格式**：
```
=== AI 可读性检查报告 ===
总段落数: X
平均句长: X字 ✅/⚠️
营销词命中: [...] 或 无 ✅
包含问句: ✅/❌
数据引用: X个数字 ✅/❌
综合评分: 高/中/低
优化建议: [...]
```

### 4.4 scripts/visibility_tester.py

**功能**：调用 Perplexity API 测试品牌在 AI 引擎中的可见度。

**核心逻辑**：
```python
def test_visibility(brand_name, keywords, api_key):
    # 1. 构造查询 prompt
    # 2. 调用 Perplexity API
    # 3. 检测品牌名是否出现在回复中
    # 4. 提取引用上下文
    # 5. 保存结果到 JSON 历史文件
    ...
```

**扩展能力**：
- 支持多关键词批量测试
- 支持自定义查询 prompt
- 结果自动追加到历史记录文件

### 4.5 scripts/geo_report_generator.py

**功能**：基于历史检测数据，生成季度 GEO 效果对比报告。

**核心逻辑**：
```python
def generate_report(history_file):
    # 1. 读取历史 JSON 数据
    # 2. 计算引用率趋势
    # 3. 对比前后半段数据
    # 4. 生成行动建议
    # 5. 输出结构化报告
    ...
```

### 4.6 references/geo-framework.md

**内容**：10 步 GEO 框架的完整说明，包括每一步的原理、数据支撑、操作要点。当用户需要理解某一步的具体原理时，由 Claude 按需读取。

### 4.7 references/schema-templates.md

**内容**：所有 JSON-LD Schema 类型的完整模板，包含注释说明。供 Claude 生成 Schema 时参考。

### 4.8 references/best-practices.md

**内容**：
- BrightEdge、McKinsey 等行业数据
- AI 引擎抓取偏好分析
- 部署清单与优先级排序
- 常见错误与避坑指南

### 4.9 assets/pillar-template.html

**内容**：Pillar Page 的 HTML 模板，包含内部链接集群结构，供 Claude 复制修改。

---

## 五、工作流详细设计

### 5.1 新客户首次使用流程

```
Step 1 → 收集品牌信息（名称/行业/描述/核心业务）
Step 2 → 生成 Organization Schema（A1）
Step 3 → 引导创建 ≥10 个 FAQ（A2）
Step 4 → 生成 FAQ Schema
Step 5 → 内容可读性检测（B1）
Step 6 → 规划 Pillar Page 集群（C1）
Step 7 → 部署全部 Schema（A3/A4/A5）
Step 8 → 首次可见度测试（D1）
```

### 5.2 已有内容优化流程

```
Step 1 → 读取用户现有内容/网站
Step 2 → 运行可读性检测（B1）→ 给出优化建议
Step 3 → 检查现有 Schema 缺失项 → 补充生成
Step 4 → 优化 E-E-A-T 信号（A4）
Step 5 → 运行可见度测试建立基线（D1）
```

### 5.3 定期监控流程

```
Step 1 → 运行月度可见度测试（D1）
Step 2 → 季度生成对比报告（D2）
Step 3 → 根据报告调整策略
Step 4 → 更新 FAQ / 扩展集群
```

---

## 六、关键技术决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 脚本语言 | Python 3 | 参考资料全部使用 Python，生态成熟 |
| API 集成 | Perplexity API（sonar-pro 模型） | 专为 AI 搜索设计，返回带引用的结果 |
| Schema 格式 | JSON-LD（非 Microdata/RDFa） | Google 推荐，AI 引擎解析效率最高 |
| 输出格式 | JSON + HTML + Markdown 混合 | 适配不同部署场景 |
| 数据存储 | 本地 JSON 文件 | 轻量，无需数据库依赖 |

---

## 七、执行计划

### Phase 1：基础框架（预计 2-3 小时）

| 任务 | 产出 | 预计时间 |
|------|------|----------|
| 初始化 Skill 目录结构 | 完整目录 + SKILL.md 模板 | 15 min |
| 编写 SKILL.md 主文件 | 触发条件 + 工作流 + 模块导航 | 60 min |
| 编写 schema_generator.py | 5 种 Schema 生成功能 | 45 min |
| 编写 schema-templates.md | 所有 Schema 模板 | 30 min |

### Phase 2：检测与监控（预计 2 小时）

| 任务 | 产出 | 预计时间 |
|------|------|----------|
| 编写 readability_checker.py | 可读性检测脚本 | 30 min |
| 编写 visibility_tester.py | Perplexity API 测试 | 45 min |
| 编写 geo_report_generator.py | 季度报告生成 | 30 min |
| 测试所有脚本 | 确保运行无报错 | 15 min |

### Phase 3：参考文档与资产（预计 1 小时）

| 任务 | 产出 | 预计时间 |
|------|------|----------|
| 编写 geo-framework.md | 10 步框架完整文档 | 30 min |
| 编写 best-practices.md | 最佳实践参考 | 15 min |
| 编写 pillar-template.html | Pillar Page 模板 | 15 min |

### Phase 4：集成测试与打包（预计 30 min）

| 任务 | 产出 | 预计时间 |
|------|------|----------|
| 端到端测试 | 确认全流程可用 | 15 min |
| 运行 package_skill.py | 分发包 .skill 文件 | 5 min |
| 文档检查 | 确认无遗漏 | 10 min |

**总计预估：5.5 - 6.5 小时**

---

## 八、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| Perplexity API 不可用或需付费 | 可见度测试无法执行 | 提供手动测试指引作为降级方案 |
| Schema 验证不通过 | 生成的标记无效 | 脚本内集成基础验证逻辑 |
| SKILL.md 过长 | 占用过多 context | 严格控制在 500 行内，详细内容下沉到 references |
| Python 环境差异 | 脚本运行失败 | 仅使用标准库，无第三方依赖（除 requests 外） |

---

## 九、交付物清单

1. **geo-optimizer.skill** — 可分发安装的 Skill 包
2. 包含完整可运行的 Python 脚本 × 4
3. 包含参考文档 × 3
4. 包含 HTML 模板 × 1
5. SKILL.md 完整工作流指引
